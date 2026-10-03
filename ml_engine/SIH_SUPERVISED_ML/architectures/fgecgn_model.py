import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class TopKNodePooling(nn.Module):
    def __init__(self, in_channels: int, k: int = 50):
        super().__init__()
        self.in_channels = in_channels
        self.k = k
        self.p = nn.Parameter(torch.Tensor(in_channels, 1))
        nn.init.kaiming_uniform_(self.p, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        num_nodes = x.size(0)
        actual_k = min(self.k, num_nodes)
        scores = torch.matmul(x, self.p) / (torch.norm(self.p) + 1e-8)
        scores = torch.sigmoid(scores.view(-1))
        topk_scores, topk_indices = torch.topk(scores, actual_k)
        selected_nodes = x[topk_indices] * topk_scores.unsqueeze(-1)
        if actual_k < self.k:
            padding = torch.zeros(self.k - actual_k, self.in_channels, device=x.device, dtype=x.dtype)
            selected_nodes = torch.cat([selected_nodes, padding], dim=0)
        return selected_nodes

class MatGRUCell(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, k: int = 50):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.k = k
        self.u_proj = nn.Linear(k, out_channels)
        self.gru = nn.GRUCell(input_size=in_channels, hidden_size=in_channels)

    def forward(self, u_t: torch.Tensor, w_prev: torch.Tensor) -> torch.Tensor:
        u_projected = self.u_proj(u_t.transpose(0, 1)).transpose(0, 1)
        w_curr = self.gru(u_projected, w_prev)
        return w_curr

class EvolveGCNHConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, k: int = 50):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.k = k
        self.pooling = TopKNodePooling(in_channels, k=k)
        self.mat_gru = MatGRUCell(in_channels, out_channels, k=k)
        self.register_buffer("w_init", torch.empty(out_channels, in_channels))
        self.register_buffer("w_state", torch.empty(out_channels, in_channels))
        nn.init.kaiming_uniform_(self.w_init, a=math.sqrt(5))
        self.w_state.copy_(self.w_init)

    def reset_temporal_state(self):
        self.w_state = self.w_init.clone()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        u_t = self.pooling(x)
        w_t = self.mat_gru(u_t, self.w_state)
        self.w_state = w_t

        num_nodes = x.size(0)
        if edge_index.shape[1] > 0:
            row, col = edge_index
            deg = torch.bincount(row, minlength=num_nodes).float()
            deg_inv_sqrt = torch.pow(deg, -0.5)
            deg_inv_sqrt[deg_inv_sqrt == float('inf')] = 0.0
            edge_weight = deg_inv_sqrt[row] * deg_inv_sqrt[col]

            out = torch.zeros_like(x)
            out.index_add_(0, row, x[col] * edge_weight.unsqueeze(-1))
        else:
            out = x

        out = torch.matmul(out, w_t.transpose(0, 1))
        return out

class AdaptiveReliabilityGate(nn.Module):
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.gate_net = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    def forward(self, z_t: torch.Tensor, s_t: torch.Tensor) -> torch.Tensor:
        combined = torch.cat([z_t, s_t], dim=-1)
        return self.gate_net(combined)

class FGEGCNModel(nn.Module):
    """Feature-Gated EvolveGCN (FG-EGCN) with Adaptive Reliability Gate."""
    def __init__(self, in_channels: int, hidden_dim: int = 64, out_channels: int = 2, top_k: int = 50, dropout: float = 0.3):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.dropout = dropout

        # Branch 1: Temporal Graph Encoder (EvolveGCN-H)
        self.gnn1 = EvolveGCNHConv(in_channels, hidden_dim, k=top_k)
        self.bn_gnn1 = nn.BatchNorm1d(hidden_dim)
        self.gnn2 = EvolveGCNHConv(hidden_dim, hidden_dim, k=top_k)
        self.bn_gnn2 = nn.BatchNorm1d(hidden_dim)

        # Branch 2: Residual Feature Projector (Direct transaction attributes)
        self.feat_proj = nn.Sequential(
            nn.Linear(in_channels, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim)
        )

        # Branch 3: Node-wise Adaptive Reliability Gate
        self.gate = AdaptiveReliabilityGate(hidden_dim)
        self.classifier = nn.Linear(hidden_dim, out_channels)

    def reset_temporal_state(self):
        self.gnn1.reset_temporal_state()
        self.gnn2.reset_temporal_state()

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor):
        # 1. Temporal Graph Encoder
        z = self.gnn1(x, edge_index)
        z = self.bn_gnn1(z)
        z = F.relu(z)
        z = F.dropout(z, p=self.dropout, training=self.training)

        z = self.gnn2(z, edge_index)
        z = self.bn_gnn2(z)
        z_t = F.relu(z)

        # 2. Residual Feature Projector
        s_t = F.relu(self.feat_proj(x))

        # 3. Adaptive Gate
        gamma_t = self.gate(z_t, s_t)

        # 4. Convex Fusion
        h_t = gamma_t * z_t + (1.0 - gamma_t) * s_t
        logits = self.classifier(h_t)
        return logits, gamma_t
