import numpy as np
import pytest
from sklearn.metrics import roc_auc_score
from connectome_pilot.evaluation import aggregate_images, transform_training, weighted_auc, validate_records
from connectome_pilot.nulls import rewire


def test_weighted_auc_handles_ties_and_cluster_multiplicity():
    y = np.array([0, 1, 0, 1, 0, 1])
    p = np.array([.1, .1, .4, .6, .6, .6])
    w = np.array([[1., 2, 3, 0, 2, 1], [2., 1, 0, 3, 1, 2]])
    for got, weights in zip(weighted_auc(y, p, w), w):
        assert got == pytest.approx(roc_auc_score(y, p, sample_weight=weights))


def test_log_transform_precedes_visit_aggregation():
    X = np.array([[0., 8.], [8., 0.], [2., 2.], [4., 4.]])
    y = np.array([0, 0, 1, 1])
    p = np.array(["a", "a", "b", "b"])
    v = np.array(["same", "same", "same", "other"])
    f = np.array([0, 0, 1, 1])
    got, labels, patients, _ = aggregate_images(X, y, p, v, f, spike_counts=True)
    np.testing.assert_allclose(got[0], np.log1p(X[:2]).mean(0))
    assert not np.allclose(got[0], np.log1p(X[:2].mean(0)))
    assert len(got) == 3 and patients.tolist() == ["a", "b", "b"]
    assert labels.tolist() == [0, 1, 1]


def test_preprocessing_uses_only_training_data():
    train = np.array([[0., 2., 4.], [1., 2., 5.], [2., 2., 6.]])
    other = np.array([[10000., 99999., 20000.]])
    a, b = transform_training(train, other, 0)
    np.testing.assert_allclose(a.mean(0), 0, atol=1e-12)
    assert a.shape[1] == 2  # A test-only change cannot revive a training-constant column.
    assert b.min() > 1000


def test_rejects_patient_split_across_outer_folds():
    with pytest.raises(ValueError, match="more than one outer fold"):
        validate_records(np.ones((4, 2)), np.array([0, 0, 1, 1]),
                         np.array(["a", "a", "b", "b"]), np.arange(4), np.array([0, 1, 0, 0]))


def test_rewiring_preserves_signed_degrees_strength_and_has_no_duplicates():
    n = 14
    pre = np.repeat(np.arange(n), 3)
    post = np.concatenate([[(i + 1) % n, (i + 3) % n, (i + 5) % n] for i in range(n)]).astype(np.int32)
    ptr = np.arange(0, len(post) + 1, 3).astype(np.int64)
    weight = np.repeat(np.where(np.arange(n) % 2, -.55, .275), 3).astype(np.float32)
    out, report = rewire(ptr, post, weight, sweeps=10)
    assert report["accepted_swaps"] > 0
    for w in np.unique(weight):
        mask = weight == w
        np.testing.assert_array_equal(np.bincount(post[mask], minlength=n), np.bincount(out[mask], minlength=n))
    assert len(np.unique(pre * n + out)) == len(out)
    assert not np.any(pre == out)
