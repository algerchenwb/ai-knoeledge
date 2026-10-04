"""Actual sklearn t-SNE and neighborhood checks; optional reproducible SVG export."""
import argparse
import json
from pathlib import Path
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.manifold import TSNE, trustworthiness


def run(plot=False):
    x, reference = make_blobs(n_samples=150, n_features=8, centers=3,
                              cluster_std=1.5, random_state=21)
    embeddings, results = [], []
    for perplexity in [10, 30]:
        model = TSNE(n_components=2, perplexity=perplexity, init="pca",
                     learning_rate="auto", max_iter=500, random_state=0)
        embedding = model.fit_transform(x)
        assert embedding.shape == (150, 2) and np.all(np.isfinite(embedding))
        assert np.isfinite(model.kl_divergence_)
        assert not hasattr(model, "transform")
        score = trustworthiness(x, embedding.astype(float), n_neighbors=5)
        assert 0 <= score <= 1
        shifted = 3.0 * embedding.astype(float) + [100., -80.]
        np.testing.assert_allclose(score, trustworthiness(x, shifted, n_neighbors=5))
        results.append({"perplexity": perplexity, "trustworthiness_k5": float(score),
                        "kl_divergence": float(model.kl_divergence_),
                        "learning_rate": float(model.learning_rate_)})
        embeddings.append(embedding)
    try:
        TSNE(perplexity=len(x)).fit_transform(x)
    except ValueError as error:
        assert "perplexity" in str(error)
    else:
        raise AssertionError("perplexity >= sample count accepted")
    print("PASS finite embeddings, perplexity bound, no transform, neighborhood invariance")
    print(json.dumps(results))
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["svg.hashsalt"] = "tsne-fixed-example"
        figure, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
        for axis, embedding, result in zip(axes, embeddings, results):
            axis.scatter(embedding[:, 0], embedding[:, 1], c=reference,
                         cmap="viridis", s=20, alpha=0.8)
            axis.set_title(f"perplexity={result['perplexity']}; T@5={result['trustworthiness_k5']:.3f}")
            axis.set_xlabel("t-SNE coordinate 1")
            axis.set_ylabel("t-SNE coordinate 2")
        figure.suptitle("Synthetic reference colors; gaps and areas are not calibrated")
        path = Path(__file__).resolve().parent.parent / "assets" / "tsne-perplexity.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(path, metadata={"Date": None})
        figure.savefig(path.with_suffix(".png"), dpi=100)
        plt.close(figure)
        print(f"PLOT {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", action="store_true", help="Also export SVG/PNG (requires matplotlib)")
    run(plot=parser.parse_args().plot)
