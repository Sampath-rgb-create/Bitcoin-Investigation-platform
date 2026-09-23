"""
Isolation Forest Anomaly Detector for Bitcoin Investigation Platform.

Trains an unsupervised Isolation Forest on the normalized feature matrix for wallets.
Uses reproducible random_state=42 and converts raw decision function output to
a deterministic [0, 1] percentile-ranked anomaly score.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


class IsolationForestDetector:
    """
    Unsupervised behavioral anomaly detector using scikit-learn's Isolation Forest.
    """

    def __init__(
        self,
        n_estimators: int = 300,
        contamination: str = "auto",
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=1,  # Deterministic execution
        )
        self.scaler = RobustScaler()
        self.feature_names: List[str] = []

    def fit_predict(
        self,
        features_df: pd.DataFrame,
        feature_cols: List[str],
    ) -> pd.DataFrame:
        """
        Fit Isolation Forest and assign an anomaly_score in [0.0, 1.0] to each row.

        Score conversion rule from PROTOTYPE.md:
        - raw_anomaly = -model.decision_function(X)
        - anomaly_score = percentile_rank(raw_anomaly)
        - 0.0 = least unusual within this case
        - 1.0 = most unusual within this case
        """
        if features_df.empty or len(features_df) == 0:
            result_df = features_df.copy()
            result_df["anomaly_score"] = 0.0
            result_df["raw_anomaly"] = 0.0
            return result_df

        self.feature_names = feature_cols
        X = features_df[feature_cols].copy().values

        # If only 1 sample, cannot meaningfully rank
        if len(features_df) == 1:
            result_df = features_df.copy()
            result_df["anomaly_score"] = 0.5
            result_df["raw_anomaly"] = 0.0
            return result_df

        # Scale features using RobustScaler (resilient to massive outliers)
        X_scaled = self.scaler.fit_transform(X)

        # Fit Isolation Forest
        self.model.fit(X_scaled)

        # Raw decision function: higher is normal, lower is anomalous
        # Negate so higher means MORE anomalous
        decision_scores = self.model.decision_function(X_scaled)
        raw_anomaly = -decision_scores

        # Compute percentile rank deterministically [0, 1]
        n_samples = len(raw_anomaly)
        # Sort indices to compute exact rank
        ranks = pd.Series(raw_anomaly).rank(method="average", ascending=True).values
        # Normalize to [0.0, 1.0]
        if n_samples > 1:
            anomaly_scores = (ranks - 1.0) / (n_samples - 1.0)
        else:
            anomaly_scores = np.array([0.5])

        result_df = features_df.copy()
        result_df["raw_anomaly"] = raw_anomaly
        result_df["anomaly_score"] = np.round(anomaly_scores, 4)

        return result_df

    def get_feature_importances(
        self,
        features_df: pd.DataFrame,
        feature_cols: List[str],
        top_k: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify top contributing deviant features for each entity using deviation from median.
        """
        entity_deviations: Dict[str, List[Dict[str, Any]]] = {}
        if features_df.empty or "entity_id" not in features_df.columns:
            return entity_deviations

        # Compute medians and interquartile ranges across case
        medians = features_df[feature_cols].median()
        q75 = features_df[feature_cols].quantile(0.75)
        q25 = features_df[feature_cols].quantile(0.25)
        iqr = (q75 - q25).replace(0, 1.0)

        for _, row in features_df.iterrows():
            entity_id = row["entity_id"]
            deviations = []
            for col in feature_cols:
                val = float(row[col])
                med = float(medians[col])
                scale = float(iqr[col])
                # Normalized z-like deviation score
                dev = abs(val - med) / scale if scale > 0 else 0.0
                deviations.append(
                    {
                        "feature": col,
                        "value": val,
                        "baseline": med,
                        "deviation": round(dev, 3),
                    }
                )

            # Sort by highest deviation
            deviations.sort(key=lambda x: x["deviation"], reverse=True)
            entity_deviations[entity_id] = deviations[:top_k]

        return entity_deviations
