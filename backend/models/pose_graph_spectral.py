import numpy as np
import networkx as nx
from scipy.sparse.linalg import eigsh

POSE_EDGES = [
    (11,13),(13,15),(12,14),(14,16),
    (11,12),(12,24),(11,23),
    (23,25),(25,27),(27,31),
    (24,26),(26,28),(28,32),
    (23,24),(27,29),(28,30),
    (15,21),(16,22)
]

def build_pose_graph(landmarks):
    G = nx.Graph()
    for i in range(33): G.add_node(i)
    for i,j in POSE_EDGES:
        d = np.linalg.norm(landmarks[i] - landmarks[j]) + 1e-6
        G.add_edge(i, j, weight=1.0/d)
    L = nx.laplacian_matrix(G, weight='weight').astype(float)
    vals,_ = eigsh(L, k=6, which='SM')
    return np.sort(vals)[1:6]
