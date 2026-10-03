import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv

class GATv2Model(nn.Module):
    """Multi-Head GATv2 model for transaction graph node classification."""
    def __init__(self, in_d: int, hidden_d: int = 32, heads: int = 4, dropout: float = 0.3, num_classes: int = 2):
        super().__init__()
        self.conv1 = GATv2Conv(in_d, hidden_d, heads=heads, concat=True)
        self.conv2 = GATv2Conv(hidden_d * heads, hidden_d, heads=1, concat=False)
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_d, num_classes)
        )
        self.dropout = dropout

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.conv1(x, edge_index))
        h = F.dropout(h, p=self.dropout, training=self.training)
        h = F.relu(self.conv2(h, edge_index))
        return self.classifier(h)
