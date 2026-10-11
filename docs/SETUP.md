# Running the public circuit code

## Environment

Use a local working directory outside synchronized document storage. Install Python 3.11/3.12 and uv, then run:

```sh
uv sync --frozen --extra simulation --group dev
uv run --frozen pytest -q
```

Fly OCR is pinned to commit `48cf341e99c17dc911fb09fdc8419d98b4d0ea86`. Linux/macOS use its compiler path. Windows uses this package's MSVC adapter to compile the same `kernel.cpp` with `/O2 /std:c++17 /EHsc /LD`. The Python adapter modifies build behavior in memory; it does not edit the installed kernel or require a fixed Visual Studio installation path.

## Obtain and prepare public source data

The upstream CLI needs the source configuration in its Git checkout. Obtain a separate clone and check out the pinned commit:

```sh
git clone https://github.com/jerryjliu/fly_ocr.git upstream-fly-ocr
git -C upstream-fly-ocr checkout 48cf341e99c17dc911fb09fdc8419d98b4d0ea86
uv run --frozen flyocr download --config upstream-fly-ocr/configs/malecns-v1.json --source data/source
uv run --frozen flyocr prepare --config upstream-fly-ocr/configs/malecns-v1.json --source data/source --graph data/upstream-graph
uv run --frozen connectome-pilot prepare-graph --source-graph data/upstream-graph --annotations data/source/annotations.feather --output data/visual-graph
uv run --frozen connectome-pilot simulate-synthetic --graph data/visual-graph --output private/synthetic-responses.json
```

Downloading and preparing the full public dataset requires substantial storage and memory. Data are CC BY 4.0; preserve attribution if redistributing modified graphs. This repository distributes code and aggregate/synthetic figures, not graph arrays.

## A rewired control

```sh
uv run --frozen connectome-pilot rewire --graph data/visual-graph --seed 20260916 --output private/null-00.npy
uv run --frozen connectome-pilot simulate-synthetic --graph data/visual-graph --post-override private/null-00.npy --output private/null-00-activity.json
```

Repeat seeds 20260916-20260925. Check gray and checker responses against the real graph using the activity guard in METHODS.md. Degree and strength preservation alone do not prove adequate null mixing or physiological matching.

## Bring your own private images

Keep your own manifest and images outside the publishable repository. A local JSON manifest is a list of objects with `image_path`, `patient_id`, `visit_id`, `label`, and `outer_fold`. Paths may be absolute or relative to that manifest. IDs are opaque local study keys. Label 0 is bacterial and label 1 fungal. A patient's images and visits must all have one label and one outer fold.

```json
[
  {"image_path": "images/example.png", "patient_id": "example-a", "visit_id": "example-visit", "label": 0, "outer_fold": 0}
]
```

This is an illustrative schema, not an evaluable dataset. Create enough patients of both labels per inner/outer fold for the locked analysis.

```sh
uv run --frozen connectome-pilot encode --graph data/visual-graph --manifest private/manifest.json --output private/real-features.npz
uv run --frozen connectome-pilot evaluate --features private/real-features.npz --unit visit --output private/real-visit-metrics.json
```

The NPZ stores per-image raw counts and private metadata. The evaluation command applies per-image log1p before aggregating visits. It exports aggregate AUROC, a conditional bootstrap interval, and fold summaries; it does not export individual patient predictions. Python callers can obtain predictions locally from `evaluate` for paired analysis.

For baseline representations, supply an NPZ with `X`, `y`, `patient_id`, `visit_id`, `outer_fold`, and scalar `feature_kind="features"`. Use `--dimensions 28` for visual PCA/input/HOG arms and `--dimensions 0` for text-28 or nuisance statistics. These commands accept precomputed baselines; this public core does not redistribute clinical MedSigLIP embeddings or the private cohort importer.

## Scope

The original clinical numbers remain in results/. The public tabular demo, numerical checks, and synthetic-circuit smoke check establish implementation behavior; they do not independently reproduce the private clinical study. The original unattended queues are not included, so a long batch run needs its own checkpointing, logging, and recovery plan before launch.
