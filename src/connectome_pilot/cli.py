"""Explicit local commands; graph downloads and clinical data are never implicit."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import numpy as np


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("demo", help="Synthetic tabular evaluation only; no connectome or patient data")
    p.add_argument("--output", type=Path, default=Path("private/toy-evaluation.json"))
    p = sub.add_parser("prepare-graph")
    p.add_argument("--source-graph", type=Path, required=True)
    p.add_argument("--annotations", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("simulate-synthetic")
    p.add_argument("--graph", type=Path, required=True)
    p.add_argument("--post-override", type=Path)
    p.add_argument("--output", type=Path, default=Path("private/synthetic-responses.json"))
    p = sub.add_parser("rewire")
    p.add_argument("--graph", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20260916)
    p.add_argument("--sweeps", type=int, default=5)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("encode", help="Read a PRIVATE local image manifest")
    p.add_argument("--graph", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--post-override", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("evaluate", help="Evaluate PRIVATE per-image arrays with fixed patient folds")
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--unit", choices=("visit", "image"), default="visit")
    p.add_argument("--dimensions", type=int, default=28, help="0 disables PCA (text-28/nuisance arms)")
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "encode" and args.output.suffix.lower() != ".npz":
        parser.error("encode output must end in .npz")
    if args.command == "rewire" and args.output.suffix.lower() != ".npy":
        parser.error("rewire output must end in .npy")
    if args.command == "prepare-graph":
        from .graph import prepare_visual_graph
        result = prepare_visual_graph(args.source_graph, args.annotations, args.output)
        print(json.dumps({k: result[k] for k in ("nodes", "edges", "readout_nodes")}))
    elif args.command in ("simulate-synthetic", "encode"):
        from .encoding import load_graph, brain_for, synthetic_stimuli, spike_features, image_gray
        arrays = load_graph(args.graph, args.post_override)
        brain = brain_for(arrays)
        if args.command == "simulate-synthetic":
            result = {}
            for name, gray in synthetic_stimuli().items():
                feature = spike_features(brain, gray)
                result[name] = {"readout_spikes": int(feature.sum()),
                                "active_readout": int(((feature[:len(feature)//2] +
                                                       feature[len(feature)//2:]) > 0).sum())}
            write_json(args.output, result)
            print(json.dumps(result, indent=2))
        else:
            records = json.loads(args.manifest.read_text(encoding="utf-8"))
            if not records:
                raise ValueError("Image manifest is empty")
            vectors = []
            for row in records:
                path = Path(row["image_path"])
                if not path.is_absolute():
                    path = args.manifest.parent / path
                vectors.append(spike_features(brain, image_gray(path)))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(args.output, X=np.stack(vectors),
                                y=np.asarray([r["label"] for r in records], np.int8),
                                patient_id=np.asarray([str(r["patient_id"]) for r in records]),
                                visit_id=np.asarray([str(r["visit_id"]) for r in records]),
                                outer_fold=np.asarray([r["outer_fold"] for r in records]),
                                feature_kind=np.array("spike_counts"))
            print(f"Encoded {len(records)} local images; features and metadata remain private")
    elif args.command == "rewire":
        from .encoding import load_graph
        from .nulls import rewire
        arrays = load_graph(args.graph)
        target, report = rewire(arrays["ptr"], arrays["post"], arrays["weight"], args.seed, args.sweeps)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        np.save(args.output, target, allow_pickle=False)
        write_json(args.output.with_suffix(".json"), report)
        print(json.dumps(report))
    elif args.command == "demo":
        from .evaluation import evaluate, EvaluationConfig
        rng = np.random.default_rng(20260916)
        patients = np.repeat([f"toy-{i:03d}" for i in range(60)], 2)
        y = np.repeat(np.arange(60) % 2, 2)
        folds = np.repeat((np.arange(60) // 2) % 5, 2)
        visits = np.tile(["visit-a", "visit-b"], 60)
        X = rng.normal(size=(120, 12)).astype(np.float32)
        X[:, 0] += y * .6
        result, _ = evaluate(X, y, patients, visits, folds,
                             config=EvaluationConfig(dimensions=4, bootstrap_replicates=500))
        result["data_kind"] = "Synthetic tabular smoke test; not connectome or keratitis performance"
        write_json(args.output, result)
        print(json.dumps(result, indent=2))
    else:
        from .evaluation import evaluate, EvaluationConfig
        with np.load(args.features, allow_pickle=False) as data:
            kind = str(data["feature_kind"])
            if kind not in ("spike_counts", "features"):
                raise ValueError("feature_kind must be spike_counts or features")
            result, _ = evaluate(data["X"], data["y"], data["patient_id"], data["visit_id"],
                                 data["outer_fold"], unit=args.unit,
                                 spike_counts=kind == "spike_counts",
                                 config=replace(EvaluationConfig(), dimensions=args.dimensions))
        write_json(args.output, result)
        print(f"{result['unit']} AUROC: {result['auroc']:.3f}")


if __name__ == "__main__":
    main()
