"""Select the pilot's visual induced subgraph from an upstream prepared graph."""
import hashlib
import json
from pathlib import Path
import numpy as np


def prepare_visual_graph(source, annotations, output):
    import pyarrow.feather as feather
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve():
        raise ValueError("Use a separate output directory")
    keys = ("ids", "ptr", "post", "weight", "retina", "lamina", "candidates", "uv",
            "retina_confidence", "signs", "cell_type", "superclass")
    graph = {k: np.load(source / f"{k}.npy", mmap_mode="r", allow_pickle=False) for k in keys}
    keep = np.unique(np.r_[graph["retina"], graph["lamina"], graph["candidates"]])
    n = len(keep)
    remap = np.full(len(graph["ids"]), -1, np.int32)
    remap[keep] = np.arange(n, dtype=np.int32)
    pre = np.repeat(np.arange(len(graph["ids"]), dtype=np.int32), np.diff(graph["ptr"]))
    mask = (remap[pre] >= 0) & (remap[graph["post"]] >= 0)
    p, q = remap[pre[mask]], remap[graph["post"][mask]]
    arrays = {"ptr": np.r_[0, np.cumsum(np.bincount(p, minlength=n))].astype(np.int64),
              "post": q.astype(np.int32), "weight": np.asarray(graph["weight"][mask], np.float32)}
    for key in ("ids", "signs", "cell_type", "superclass"):
        arrays[key] = graph[key][keep]
    for key in ("retina", "lamina", "candidates"):
        arrays[key] = remap[graph[key]]
    table = feather.read_table(annotations).to_pandas().set_index("bodyId")
    sides = table.loc[graph["ids"][graph["retina"]], "rootSide"].to_numpy()
    if not np.isin(sides, ["L", "R"]).all():
        raise ValueError("Every retinal input needs a left/right eye annotation")
    uv = np.array(graph["uv"], copy=True)
    for side in ("L", "R"):
        mask = sides == side
        if not mask.any():
            raise ValueError("Both eyes are required")
        for axis in (0, 1):
            span = np.ptp(uv[mask, axis])
            if span <= 0:
                raise ValueError("Eye map has zero coordinate span")
            uv[mask, axis] = (uv[mask, axis] - uv[mask, axis].min()) / span
    arrays["uv"] = uv
    arrays["retina_confidence"] = graph["retina_confidence"]
    xyz = table.loc[arrays["ids"], "somaLocation"]
    arrays["xyz"] = np.asarray([v if isinstance(v, (list, np.ndarray)) and len(v) == 3
                                else [np.nan] * 3 for v in xyz], np.float32)
    arrays["old_index"] = keep
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for key, value in arrays.items():
        dest = output / f"{key}.npy"
        np.save(dest, value, allow_pickle=False)
        hashes[key] = hashlib.sha256(dest.read_bytes()).hexdigest()
    manifest = {"dataset": "MaleCNS v1.0 visual induced subgraph", "nodes": n,
                "edges": len(q), "retinal_inputs": len(arrays["retina"]),
                "tonic_inputs": len(arrays["lamina"]), "readout_nodes": len(arrays["candidates"]),
                "source": "https://male-cns.janelia.org/download/", "license": "CC BY 4.0",
                "upstream_commit": "48cf341e99c17dc911fb09fdc8419d98b4d0ea86",
                "input_map": "Connectivity-inferred map; rescaled separately within each eye",
                "array_hashes": hashes}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
