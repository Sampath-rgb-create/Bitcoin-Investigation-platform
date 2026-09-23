"""
Parquet analytical table store.
Columnar, efficient local storage using PyArrow and Pandas for:
- validated/transactions.parquet, network.parquet
- normalized/transactions.parquet, network.parquet
- correlated/network_transaction_links.parquet
- features/transaction_features.parquet, wallet_features.parquet, etc.
"""
import os
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class ParquetStore:
    """
    Manages reading and writing columnar Parquet tables.
    Handles serialization of complex types (lists, dicts) when storing in Parquet.
    """

    @staticmethod
    def write_records(
        records: List[Dict[str, Any]],
        file_path: str,
        compression: str = "snappy"
    ) -> int:
        """
        Writes a list of dictionary records to a Parquet file.
        Ensures nested structures (like list of addresses/amounts) are correctly preserved.
        Returns the number of rows written.
        """
        if not records:
            # Create an empty table
            df = pd.DataFrame()
        else:
            # Normalize complex types like set -> list so pyarrow handles them seamlessly
            cleaned = []
            for r in records:
                row_copy = {}
                for k, v in r.items():
                    if isinstance(v, (set, frozenset, tuple)):
                        row_copy[k] = list(v)
                    else:
                        row_copy[k] = v
                cleaned.append(row_copy)
            df = pd.DataFrame(cleaned)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Write to parquet
        df.to_parquet(file_path, index=False, engine="pyarrow", compression=compression)
        return len(df)

    @staticmethod
    def read_records(file_path: str) -> List[Dict[str, Any]]:
        """
        Reads a Parquet file and returns a list of dictionary records.
        """
        if not os.path.exists(file_path):
            return []
        df = pd.read_parquet(file_path, engine="pyarrow")
        records = df.to_dict(orient="records")

        # Convert numpy types to native Python types where needed
        clean_records = []
        for r in records:
            clean_r = {}
            for k, v in r.items():
                if isinstance(v, (list, tuple)):
                    clean_r[k] = list(v)
                elif hasattr(v, "tolist"):
                    clean_r[k] = v.tolist()
                elif pd.isna(v):
                    clean_r[k] = None
                else:
                    clean_r[k] = v
            clean_records.append(clean_r)

        return clean_records

    @staticmethod
    def read_dataframe(file_path: str) -> pd.DataFrame:
        """
        Loads Parquet file directly into a pandas DataFrame.
        """
        if not os.path.exists(file_path):
            return pd.DataFrame()
        return pd.read_parquet(file_path, engine="pyarrow")

    @staticmethod
    def write_dataframe(
        df: pd.DataFrame,
        file_path: str,
        compression: str = "snappy"
    ) -> int:
        """
        Writes a pandas DataFrame directly to Parquet.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_parquet(file_path, index=False, engine="pyarrow", compression=compression)
        return len(df)


parquet_store = ParquetStore()
