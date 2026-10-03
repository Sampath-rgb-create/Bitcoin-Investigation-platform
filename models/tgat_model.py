import torch
import torch.nn as nn
import torch.nn.functional as F

class SparseNetworkTGAT(nn.Module):
    """Temporal Graph Attention network with continuous sinusoidal time encodings on bipartite network."""
    def __init__(self, in_features: int, time_dim: int = 16, hidden_dim: int = 64, num_classes: int = 2, dropout: float = 0.3):
        super().__init__()
        self.time_dim = time_dim
        inv_freq = 1.0 / (10000 ** (torch.arange(0, time_dim, 2).float() / time_dim))
        self.register_buffer('inv_freq', inv_freq)

        total_in = in_features + time_dim
        self.w_neigh1 = nn.Linear(total_in, hidden_dim, bias=False)
        self.w_self1 = nn.Linear(total_in, hidden_dim, bias=True)
        self.w_neigh2 = nn.Linear(hidden_dim, hidden_dim, bias=False)
        self.w_self2 = nn.Linear(hidden_dim, hidden_dim, bias=True)
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )
        self.dropout = dropout

    def forward(self, x: torch.Tensor, adj: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        if t.dim() == 1:
            t = t.unsqueeze(-1)
        sin_inp = t.float() * self.inv_freq
        t_emb = torch.cat([torch.sin(sin_inp), torch.cos(sin_inp)], dim=-1)
        x_timed = torch.cat([x, t_emb], dim=-1)

        h_neigh = torch.sparse.mm(adj, x_timed)
        h = F.relu(self.w_self1(x_timed) + self.w_neigh1(h_neigh))
        h = F.dropout(h, p=self.dropout, training=self.training)

        h_neigh2 = torch.sparse.mm(adj, h)
        h2 = F.relu(self.w_self2(h) + self.w_neigh2(h_neigh2))
        return self.classifier(h2)
