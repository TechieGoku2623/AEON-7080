"""Logistic regression trained on synthetic morphology features.

The label is a synthetic T-wave class. Accuracy is reported only on the
held-out synthetic split created in the same call.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.labels import MODEL_PREDICTION, SYNTHETIC_DATA


def _sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -30, 30)
    return 1.0 / (1.0 + np.exp(-z))


def train_logistic(x: np.ndarray, y: np.ndarray, seed: int = 42, epochs: int = 200, lr: float = 0.2) -> dict:
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(y)
    order = rng.permutation(n)
    cut = max(1, int(n * 0.7))
    train_idx, test_idx = order[:cut], order[cut:]
    if len(test_idx) == 0:
        test_idx = train_idx
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0)
    std = np.where(std < 1e-8, 1.0, std)
    xt = (x_train - mean) / std
    xv = (x_test - mean) / std
    w = np.zeros(xt.shape[1])
    b = 0.0
    loss_curve = []
    for _ in range(epochs):
        p = _sigmoid(xt @ w + b)
        eps = 1e-9
        loss = -np.mean(y_train * np.log(p + eps) + (1 - y_train) * np.log(1 - p + eps))
        loss_curve.append(float(loss))
        grad_w = xt.T @ (p - y_train) / len(y_train)
        grad_b = float(np.mean(p - y_train))
        w -= lr * grad_w
        b -= lr * grad_b
    test_p = _sigmoid(xv @ w + b)
    pred = (test_p >= 0.5).astype(int)
    truth = y_test.astype(int)
    tp = int(np.sum((pred == 1) & (truth == 1)))
    tn = int(np.sum((pred == 0) & (truth == 0)))
    fp = int(np.sum((pred == 1) & (truth == 0)))
    fn = int(np.sum((pred == 0) & (truth == 1)))
    accuracy = float(np.mean(pred == truth))
    return {
        "weights": w,
        "bias": float(b),
        "mean": mean,
        "std": std,
        "loss_curve": loss_curve[:: max(1, len(loss_curve) // 40)],
        "metrics": {
            "accuracy": accuracy,
            "n_train": int(len(y_train)),
            "n_test": int(len(y_test)),
            "confusion_matrix": [[tn, fp], [fn, tp]],
            "label": MODEL_PREDICTION,
        },
    }


def train_morphology_classifier(seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    n = 400
    # Class 0: positive T-wave mean. Class 1: negative T-wave mean. Plus noise.
    labels = rng.integers(0, 2, size=n)
    t_wave = np.where(labels == 0, rng.normal(0.25, 0.04, size=n), rng.normal(-0.2, 0.04, size=n))
    x = t_wave.reshape(-1, 1)
    trained = train_logistic(x, labels.astype(float), seed=seed)

    def predict(t_wave_mean: float) -> dict:
        z = ((np.array([t_wave_mean]) - trained["mean"]) / trained["std"]) @ trained["weights"] + trained["bias"]
        probability = float(_sigmoid(np.array([z]))[0]) if np.ndim(z) else float(_sigmoid(np.array([float(z)]))[0])
        # z may be shape (1,)
        score = float(np.asarray(z, dtype=float).reshape(-1)[0])
        probability = float(_sigmoid(np.array([score]))[0])
        klass = "synthetic_morphology_b" if probability >= 0.5 else "synthetic_morphology_a"
        return {
            "label": MODEL_PREDICTION,
            "class": klass,
            "probability_class_b": probability,
            "feature_t_wave_mean": float(t_wave_mean),
            "note": "Class labels refer only to the synthetic training distribution.",
        }

    torch_status = _optional_torch(x, labels.astype(float), seed)
    return {
        "predict": predict,
        "metrics": trained["metrics"],
        "loss_curve": trained["loss_curve"],
        "architecture": {
            "type": "logistic regression",
            "inputs": ["t_wave_mean"],
            "output": "probability of synthetic_morphology_b",
            "epochs": 200,
            "implementation": "numpy",
        },
        "frameworks": {
            "numpy": {"available": True, "used": True},
            "pytorch": torch_status,
            "tensorflow": _tensorflow_status(),
        },
        "training_data": SYNTHETIC_DATA,
    }


def _optional_torch(x: np.ndarray, y: np.ndarray, seed: int) -> dict:
    try:
        import torch
    except ImportError:
        return {"available": False, "used": False, "note": "PyTorch is not installed. No PyTorch metric is reported."}
    generator = torch.Generator().manual_seed(seed)
    xt = torch.tensor(x, dtype=torch.float32)
    yt = torch.tensor(y, dtype=torch.float32).reshape(-1, 1)
    weight = torch.zeros((1, 1), requires_grad=True)
    bias = torch.zeros(1, requires_grad=True)
    for _ in range(80):
        score = xt @ weight + bias
        loss = torch.mean(torch.nn.functional.binary_cross_entropy_with_logits(score, yt))
        loss.backward()
        with torch.no_grad():
            weight -= 0.2 * weight.grad
            bias -= 0.2 * bias.grad
            weight.grad.zero_()
            bias.grad.zero_()
    with torch.no_grad():
        pred = (torch.sigmoid(xt @ weight + bias) >= 0.5).to(torch.float32)
        accuracy = float(torch.mean((pred == yt).to(torch.float32)))
    return {
        "available": True,
        "used": True,
        "version": torch.__version__,
        "held_in_sample_accuracy": accuracy,
        "note": "In-sample accuracy on the same synthetic draw. Not an external validation.",
        "generator_seed": int(seed),
        "unused": int(generator.initial_seed()),
    }


def _tensorflow_status() -> dict:
    try:
        import tensorflow as tf
    except ImportError:
        return {
            "available": False,
            "used": False,
            "note": "TensorFlow is not installed. No TensorFlow metric is reported.",
        }
    return {"available": True, "used": False, "version": tf.__version__, "note": "Detected but not used for this classifier."}
