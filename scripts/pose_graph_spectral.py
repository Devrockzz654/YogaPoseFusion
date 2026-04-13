# pose_graph_spectral.py

import numpy as np
import networkx as nx
from scipy.sparse.linalg import eigsh

# Define anatomical MediaPipe connections (subset of 33 keypoints)
POSE_EDGES = [
    (11, 13), (13, 15), (12, 14), (14, 16),  # arms
    (11, 12), (12, 24), (11, 23),            # shoulders to hips
    (23, 25), (25, 27), (27, 31),            # left leg
    (24, 26), (26, 28), (28, 32),            # right leg
    (23, 24), (27, 29), (28, 30),            # hip bridge and lower
    (15, 21), (16, 22),                      # hands
]

def build_pose_graph(landmarks):
    """
    landmarks: np.array of shape (33, 3) for (x, y, z)
    returns: 5D spectral feature vector (top-5 nonzero Laplacian eigenvalues)
    """
    G = nx.Graph()
    for i in range(33):
        G.add_node(i)
    for i, j in POSE_EDGES:
        dist = np.linalg.norm(landmarks[i] - landmarks[j])
        if dist == 0:
            dist = 1e-6  # avoid div-by-zero
        G.add_edge(i, j, weight=1.0 / dist)

    L = nx.laplacian_matrix(G, weight='weight').astype(float)
    vals, _ = eigsh(L, k=6, which='SM')  # smallest magnitude eigenvalues
    return np.sort(vals)[1:6]  # drop the zero eigenvalue

def extract_features_batch(landmark_list):
    """
    Accepts list of np.array (landmarks per sample), returns spectral feature matrix.
    """
    return np.array([build_pose_graph(lmk) for lmk in landmark_list])

if __name__ == '__main__':
    # Example test
    dummy_pose = np.random.rand(33, 3)
    features = build_pose_graph(dummy_pose)
    print("Spectral Features:", features)
