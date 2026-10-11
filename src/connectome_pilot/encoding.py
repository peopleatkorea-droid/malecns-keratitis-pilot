"""Fixed image preprocessing and a thin adapter to the upstream LIF engine."""
from pathlib import Path
import numpy as np
from PIL import Image


def image_gray(path):
    """128-square letterbox and gamma-encoded sRGB luma, as in the pilot."""
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        scale = 128 / max(width, height)
        rgb = rgb.resize((max(1, round(width * scale)), max(1, round(height * scale))),
                         Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (128, 128), (128, 128, 128))
        canvas.paste(rgb, ((128 - rgb.width) // 2, (128 - rgb.height) // 2))
        pixels = np.asarray(canvas, dtype=np.float32)
    return pixels @ np.array([.2126, .7152, .0722], np.float32)


def synthetic_stimuli():
    y, x = np.mgrid[:128, :128]
    return {
        "gray": np.full((128, 128), 127.5, np.float32),
        "dark": np.full((128, 128), 51, np.float32),
        "bright": np.full((128, 128), 204, np.float32),
        "vertical": np.where(x < 64, 51, 204).astype(np.float32),
        "horizontal": np.where(y < 64, 51, 204).astype(np.float32),
        "checker": np.where((x // 16 + y // 16) % 2, 51, 204).astype(np.float32),
    }


def load_graph(folder, post_override=None):
    folder = Path(folder)
    required = ("ptr", "post", "weight", "retina", "lamina", "candidates", "uv")
    arrays = {key: np.load(folder / f"{key}.npy", mmap_mode="r", allow_pickle=False)
              for key in required}
    if post_override is not None:
        post = np.load(post_override, mmap_mode="r", allow_pickle=False)
        if post.shape != arrays["post"].shape or post.dtype != np.int32:
            raise ValueError("Rewired targets must match the original graph shape and dtype")
        arrays["post"] = post
    return arrays


def brain_for(arrays):
    # Compile the unchanged upstream kernel on Windows with a discovered MSVC.
    from .native_windows import enable_windows_build
    enable_windows_build()
    from flyocr.brain.model import Brain, StimulusConfig
    config = StimulusConfig(sensory_gain=20, lamina_drive=12, warmup_ms=0,
                            duration_ms=100, bins=20, half_saturation=.2, invert=False)
    brain = Brain(arrays, config)
    for _ in range(20):
        brain.present_samples(np.full(len(arrays["retina"]), .5, np.float32), 5)
    brain.canonical = brain.snapshot()
    return brain


def spike_features(brain, gray):
    """Return raw 0-50 and 50-100 ms counts; log1p is applied before aggregation."""
    counts, _, _ = brain.encode(gray, reset=True)
    if counts.shape[0] != 20:
        raise ValueError("Expected twenty 5 ms bins")
    return np.concatenate((counts[:10].sum(0), counts[10:].sum(0))).astype(np.int32)
