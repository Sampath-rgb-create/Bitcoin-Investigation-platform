import torch
import torch.nn as nn
import torch.nn.functional as F

class SparseGraphSAGE(nn.Module):
    """Spatial inductive GraphSAGE with separate self and neighbor mean projections via sparse adjacency."""
    def __init__(self, in_features: int = None, hidden_dim: int = 64, num_classes: int = 2, dropout: float = 0.3, in_channels: int = None):
        super().__init__()
        in_dim = in_features if in_features is not None else in_channels
        self.w_neigh1 = nn.Linear(in_dim, hidden_dim, bias=False)
        self.w_self1 = nn.Linear(in_dim, hidden_dim, bias=True)
        self.w_neigh2 = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.w_self2 = nn.Linear(hidden_dim, hidden_dim, bias=True)
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )
        self.dropout = dropout

    def forward(self, x: torch.Tensor, adj_sage: torch.Tensor) -> torch.Tensor:
        # Layer 1: Concat(Self, Neighbor_Mean)
        h_neigh = torch.sparse.mm(adj_sage, x)
        h = F.relu(self.w_self1(x) + self.w_neigh1(h_neigh))
        h = F.dropout(h, p=self.dropout, training=self.training)
        # Layer 2
        h_neigh2 = torch.sparse.mm(adj_sage, h)
        h2 = F.relu(self.w_self2(h) + self.w_neigh2(h_neigh2))
        return self.classifier(h2)
