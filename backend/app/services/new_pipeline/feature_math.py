"""
Forensic Feature Computation Engine for Elliptic++ Case Generation.

Generates the exact mathematical features matching the frozen 9-brain model contracts:
1. Transaction Domain (182 features):
   - 17 graph/flow quantities: in/out degree, total BTC, fees, size, address counts, in/out BTC stats
   - 93 local features (LF_1 - LF_93): fee-per-byte, input/output variances, Shannon entropy, script types
   - 72 aggregate features (AF_1 - AF_72): 1-hop forward & backward neighbor statistics (min, max, mean, std, median)
2. Wallet Domain (55 features):
   - 6 interaction/degree: txs as sender, receiver, total txs, multi-tx addresses
   - 6 block appearance/lifetime: first/last blocks, block lifetime, interval blocks
   - 15 BTC flow quantities: total, min, max, mean, median transacted/sent/received
   - 10 fees: total, min, max, mean, median fees & fee shares
   - 15 temporal intervals: blocks/timesteps between transactions
   - 3 counterparty distribution stats
3. Network Domain (13 features):
   - Topology & Flow: num/unique inputs/outputs, total degree, in_out_ratio, net_flow_direction
   - Forensic Pattern Flags: is_aggregation_pattern, is_peeling_chain_pattern, is_fan_out_dispersion
   - Distribution: input/output concentration, bipartite_entropy
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any


class FeatureMathEngine:
    """
    Mathematical feature calculations for Tri-Domain Elliptic++ features.
    """

    @staticmethod
    def compute_entropy(values: List[float]) -> float:
        """Computes Shannon entropy: H = -sum(p * log2(p))."""
        total = sum(values)
        if total <= 0:
            return 0.0
        entropy = 0.0
        for v in values:
            if v > 0:
                p = v / total
                entropy -= p * math.log2(p)
        return float(entropy)

    @staticmethod
    def compute_stats(arr: List[float]) -> Tuple[float, float, float, float, float]:
        """Returns min, max, mean, median, total."""
        if not arr:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        np_arr = np.array(arr, dtype=np.float64)
        return (
            float(np.min(np_arr)),
            float(np.max(np_arr)),
            float(np.mean(np_arr)),
            float(np.median(np_arr)),
            float(np.sum(np_arr)),
        )

    @staticmethod
    def compute_std(arr: List[float]) -> float:
        if not arr or len(arr) < 2:
            return 0.0
        return float(np.std(arr, ddof=1))
