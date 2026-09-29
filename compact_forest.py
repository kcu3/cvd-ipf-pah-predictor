"""Memory-mapped inference for exported binary sklearn random forests."""
import json
from pathlib import Path
import numpy as np

class CompactForest:
    def __init__(self, directory, spec):
        self.nodes = np.load(Path(directory) / spec['file'], mmap_mode='r', allow_pickle=False)
        self.roots = np.asarray(spec['offsets'], dtype=np.int64)
        self.n_features_in_ = spec['n_features']
        self.classes_ = np.array([0, 1])
        if spec.get('feature_names') is not None:
            self.feature_names_in_ = np.asarray(spec['feature_names'])
        self.n_jobs = 1

    def predict_proba(self, X):
        X = np.asarray(X, dtype=np.float32)
        if X.ndim != 2 or X.shape[1] != self.n_features_in_ or not np.isfinite(X).all():
            raise ValueError('Invalid forest input.')
        n, trees = len(X), len(self.roots)
        positions = np.tile(self.roots, n)
        rows = np.repeat(np.arange(n), trees)
        active = np.flatnonzero(self.nodes['feature'][positions] >= 0)
        while len(active):
            node = self.nodes[positions[active]]
            goes_left = X[rows[active], node['feature']] <= node['threshold']
            positions[active] = np.where(goes_left, node['left'], node['right'])
            active = active[self.nodes['feature'][positions[active]] >= 0]
        votes = self.nodes['positive'][positions].reshape(n, trees)
        # sklearn accumulates trees in estimator order, then divides by tree count.
        positive = np.cumsum(votes, axis=1)[:, -1] / trees
        return np.column_stack((1-positive, positive))

def load_compact(directory):
    directory = Path(directory)
    return [CompactForest(directory, spec) for spec in json.loads((directory/'manifest.json').read_text())]
