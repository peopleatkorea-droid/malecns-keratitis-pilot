"""Directed rewiring within exact signed weight groups, adapted from the pilot."""
import numpy as np
from numba import njit


@njit(cache=True)
def switch_edges(ptr, pre, post, order, bounds, seed, sweeps):
    np.random.seed(seed)
    out = post.copy()
    accepted = 0
    attempted = 0
    for _ in range(sweeps):
        for k in range(len(bounds) - 1):
            lo, hi = bounds[k], bounds[k + 1]
            if hi - lo < 2:
                continue
            for _ in range(hi - lo):
                i = order[np.random.randint(lo, hi)]
                j = order[np.random.randint(lo, hi)]
                attempted += 1
                a, b = pre[i], pre[j]
                c, d = out[i], out[j]
                if a == b or c == d or a == c or b == d or a == d or b == c:
                    continue
                duplicate = False
                for e in range(ptr[a], ptr[a + 1]):
                    if out[e] == d:
                        duplicate = True
                        break
                if duplicate:
                    continue
                for e in range(ptr[b], ptr[b + 1]):
                    if out[e] == c:
                        duplicate = True
                        break
                if duplicate:
                    continue
                out[i], out[j] = d, c
                accepted += 1
    return out, accepted, attempted


def rewire(ptr, post, weight, seed=20260916, sweeps=5):
    n = len(ptr) - 1
    if sweeps < 1 or n < 1 or ptr[0] != 0 or ptr[-1] != len(post):
        raise ValueError("Invalid graph or sweep count")
    if len(weight) != len(post) or np.any(np.diff(ptr) < 0):
        raise ValueError("Invalid CSR graph")
    if np.any(post < 0) or np.any(post >= n) or not np.isfinite(weight).all():
        raise ValueError("Invalid targets or weights")
    pre = np.repeat(np.arange(n, dtype=np.int32), np.diff(ptr))
    if len(np.unique(pre.astype(np.int64) * n + post)) != len(post):
        raise ValueError("Input graph contains duplicate directed edges")
    order = np.argsort(weight, kind="stable")
    bounds = np.r_[0, np.flatnonzero(np.diff(weight[order]) != 0) + 1,
                   len(weight)].astype(np.int64)
    target, accepted, attempted = switch_edges(ptr, pre, post, order, bounds, seed, sweeps)
    if not np.array_equal(np.bincount(target, minlength=n), np.bincount(post, minlength=n)):
        raise RuntimeError("Incoming degrees changed")
    if not np.array_equal(pre == target, pre == post):
        raise RuntimeError("Self-edges changed")
    if len(np.unique(pre.astype(np.int64) * n + target)) != len(target):
        raise RuntimeError("Duplicate edges were introduced")
    # Validate positive and negative weighted inputs separately.
    for mask in (weight > 0, weight < 0):
        before = np.bincount(post[mask], weights=weight[mask], minlength=n)
        after = np.bincount(target[mask], weights=weight[mask], minlength=n)
        if not np.allclose(before, after, rtol=1e-7, atol=1e-7):
            raise RuntimeError("Signed incoming strength changed")
    return target, {"seed": int(seed), "sweeps": int(sweeps),
                    "accepted_swaps": int(accepted), "attempted_swaps": int(attempted),
                    "changed_target_fraction": float(np.mean(target != post)) if len(post) else 0.,
                    "spatial_geometry_preserved": False}
