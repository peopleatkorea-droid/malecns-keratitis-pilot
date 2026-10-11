"""Patient-grouped nested CV and bootstrap of fixed out-of-fold predictions."""
from dataclasses import dataclass
import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits


@dataclass(frozen=True)
class EvaluationConfig:
    dimensions: int = 28
    inner_folds: int = 4
    inner_seeds: tuple = (20260916, 20260917, 20260918)
    strengths: tuple = (.001, .01, .1, 1., 10.)
    bootstrap_replicates: int = 5000


def validate_records(X, y, patients, visits, folds):
    X, y = np.asarray(X), np.asarray(y)
    if X.ndim != 2 or len(X) == 0 or not np.isfinite(X).all():
        raise ValueError("Features must be a nonempty finite matrix")
    columns = (y, patients, visits, folds)
    if any(np.asarray(c).ndim != 1 or len(c) != len(X) for c in columns):
        raise ValueError("Metadata must have one value per image")
    if set(np.unique(y)) != {0, 1}:
        raise ValueError("Both binary labels are required; fungal is 1")
    patients, visits = np.asarray(patients).astype(str), np.asarray(visits).astype(str)
    if np.any(patients == "") or np.any(visits == ""):
        raise ValueError("Patient and visit keys must be nonempty")
    for patient in np.unique(patients):
        mask = patients == patient
        if len(np.unique(np.asarray(folds)[mask])) != 1:
            raise ValueError("A patient appears in more than one outer fold")
        if len(np.unique(y[mask])) != 1:
            raise ValueError("This pilot expects one culture label per patient")


def aggregate_images(X, y, patients, visits, folds, unit="visit", spike_counts=False):
    validate_records(X, y, patients, visits, folds)
    X = np.asarray(X, np.float32)
    y, patients, visits, folds = map(np.asarray, (y, patients, visits, folds))
    if spike_counts:
        if np.any(X < 0):
            raise ValueError("Spike counts cannot be negative")
        X = np.log1p(X)  # Per-image transform BEFORE visit averaging.
    if unit == "image":
        return X, y, patients.astype(str), folds
    if unit != "visit":
        raise ValueError("unit must be image or visit")
    groups = {}
    for i, key in enumerate(zip(patients.astype(str), visits.astype(str))):
        groups.setdefault(key, []).append(i)
    first = np.array([indices[0] for indices in groups.values()])
    features = np.stack([X[indices].mean(0) for indices in groups.values()])
    return features, y[first], patients[first].astype(str), folds[first]


def transform_training(train, other, dimensions):
    varying = np.ptp(train, axis=0) > 1e-10
    if not varying.any():
        raise ValueError("No features vary in this training fold")
    scaler = StandardScaler()
    a = scaler.fit_transform(train[:, varying])
    b = scaler.transform(other[:, varying])
    if dimensions:
        if min(a.shape[0] - 1, a.shape[1]) < dimensions:
            raise ValueError("Insufficient training rank bound for requested PCA dimensions")
        pca = PCA(n_components=dimensions, svd_solver="full")
        a, b = pca.fit_transform(a), pca.transform(b)
    return a, b


def _fit(a, y, strength):
    return LogisticRegression(C=strength, class_weight="balanced", max_iter=3000,
                              random_state=20260916).fit(a, y)


def patient_bootstrap_auc(y, predictions, patients, replicates=5000, seed=20260916):
    _, inverse = np.unique(patients, return_inverse=True)
    count = inverse.max() + 1
    weights = np.random.default_rng(seed).multinomial(count, np.full(count, 1 / count),
                                                     size=replicates)[:, inverse].astype(float)
    return weighted_auc(y, predictions, weights)


def weighted_auc(y, predictions, weights):
    """Vectorized AUROC with tied-score half-credit and patient resample weights."""
    order = np.argsort(predictions, kind="stable")
    y, scores, weights = np.asarray(y)[order], np.asarray(predictions)[order], weights[:, order]
    starts = np.r_[0, np.flatnonzero(np.diff(scores) != 0) + 1]
    positive = np.add.reduceat(weights * y, starts, axis=1)
    negative = np.add.reduceat(weights * (1 - y), starts, axis=1)
    numerator = (positive * (np.cumsum(negative, axis=1) - negative * .5)).sum(1)
    denominator = positive.sum(1) * negative.sum(1)
    return np.divide(numerator, denominator, out=np.full_like(numerator, np.nan),
                     where=denominator > 0)


def evaluate(X, y, patients, visits, folds, unit="visit", spike_counts=False,
             config=None):
    config = config or EvaluationConfig()
    if config.dimensions < 0 or config.inner_folds < 2 or not config.inner_seeds:
        raise ValueError("Invalid evaluation configuration")
    if config.bootstrap_replicates < 1 or not config.strengths or any(c <= 0 for c in config.strengths):
        raise ValueError("Invalid bootstrap or regularization grid")
    X, y, patients, folds = aggregate_images(X, y, patients, visits, folds, unit, spike_counts)
    if len(np.unique(folds)) < 2:
        raise ValueError("At least two outer folds are required")
    predictions = np.full(len(y), np.nan)
    audit = []
    strengths = sorted(config.strengths)  # First maximum gives the smaller-C tie break.
    with threadpool_limits(limits=2):
        for fold in np.unique(folds):
            dev, test = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
            if set(patients[dev]) & set(patients[test]):
                raise ValueError("Patient leakage in outer split")
            if len(np.unique(y[test])) < 2:
                raise ValueError("Every outer test fold must contain both labels")
            for label in (0, 1):
                if len(np.unique(patients[dev][y[dev] == label])) < config.inner_folds:
                    raise ValueError("Too few development patients for inner stratified groups")
            scores = []
            for seed in config.inner_seeds:
                splitter = StratifiedGroupKFold(config.inner_folds, shuffle=True, random_state=seed)
                for it, iv in splitter.split(X[dev], y[dev], patients[dev]):
                    if set(patients[dev[it]]) & set(patients[dev[iv]]):
                        raise ValueError("Patient leakage in inner split")
                    if len(np.unique(y[dev[iv]])) < 2:
                        raise ValueError("An inner validation fold has only one label")
                    a, b = transform_training(X[dev[it]], X[dev[iv]], config.dimensions)
                    scores.append([roc_auc_score(y[dev[iv]], _fit(a, y[dev[it]], c).predict_proba(b)[:, 1])
                                   for c in strengths])
            means = np.asarray(scores).mean(0)
            best = strengths[int(np.argmax(means))]
            a, b = transform_training(X[dev], X[test], config.dimensions)
            predictions[test] = _fit(a, y[dev], best).predict_proba(b)[:, 1]
            audit.append({"fold": str(fold), "C": float(best),
                          "inner_mean_auroc": means.tolist(),
                          "test_patients": len(np.unique(patients[test])),
                          "test_units": len(test)})
    if not np.isfinite(predictions).all():
        raise RuntimeError("Out-of-fold predictions are incomplete")
    boot = patient_bootstrap_auc(y, predictions, patients, config.bootstrap_replicates)
    result = {"unit": unit, "patients": len(np.unique(patients)), "units": len(y),
              "auroc": float(roc_auc_score(y, predictions)),
              "ci95": np.nanquantile(boot, [.025, .975]).tolist(), "folds": audit,
              "bootstrap_valid_replicates": int(np.isfinite(boot).sum()),
              "interval_scope": "Conditional on fixed OOF predictions; not external validation"}
    return result, predictions
