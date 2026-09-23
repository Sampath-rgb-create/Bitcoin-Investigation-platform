"""
Investigation Report Generator for Bitcoin Investigation Platform.

Exports structured JSON and Markdown investigation reports including:
- Case overview & run metadata
- Alert summaries by priority tier (CRITICAL, HIGH, MEDIUM, LOW)
- Complete evidence provenance chain and triggered rules
- Top entities of interest with graph and network telemetry context
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
from pathlib import Path


class ReportGenerator:
    """
    Generates JSON and Markdown investigation reports.
    """

    def __init__(self):
        pass

    @staticmethod
    def generate_json_report(
        case_id: str,
        run_id: str,
        alerts: List[Dict[str, Any]],
        graph_stats: Dict[str, Any],
        config: Dict[str, Any],
        dataset_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Produce comprehensive JSON report dictionary.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        tier_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for a in alerts:
            sev = a.get("severity", "LOW")
            tier_counts[sev] = tier_counts.get(sev, 0) + 1

        return {
            "report_version": "1.0",
            "generated_at": now_str,
            "case_id": case_id,
            "run_id": run_id,
            "dataset_info": dataset_info or {},
            "graph_summary": graph_stats,
            "scoring_config": config,
            "alert_summary": {
                "total_alerts": len(alerts),
                "by_tier": tier_counts,
            },
            "alerts": alerts,
        }

    @staticmethod
    def generate_markdown_report(report_data: Dict[str, Any]) -> str:
        """
        Render structured Markdown report suitable for law enforcement / intelligence analysts.
        """
        lines = []
        lines.append(f"# Case Investigation Report: {report_data.get('case_id')}")
        lines.append(f"**Analysis Run:** `{report_data.get('run_id')}`  ")
        lines.append(f"**Generated At (UTC):** {report_data.get('generated_at')}  ")
        lines.append(f"**Report Classification:** LAW ENFORCEMENT / FORENSIC INTELLIGENCE  \n")

        # 1. Summary
        lines.append("## 1. Executive Summary")
        summary = report_data.get("alert_summary", {})
        by_tier = summary.get("by_tier", {})
        lines.append(
            f"The automated forensic pipeline analyzed the uploaded Bitcoin transaction and "
            f"network telemetry dataset. A total of **{summary.get('total_alerts', 0)} entities** were evaluated."
        )
        lines.append("")
        lines.append("| Priority Tier | Count | Description |")
        lines.append("|---|---|---|")
        lines.append(f"| **CRITICAL** | {by_tier.get('CRITICAL', 0)} | Immediate investigative escalation |")
        lines.append(f"| **HIGH** | {by_tier.get('HIGH', 0)} | Strong behavioral & structural anomalies |")
        lines.append(f"| **MEDIUM** | {by_tier.get('MEDIUM', 0)} | Moderate deviations warranting monitoring |")
        lines.append(f"| **LOW** | {by_tier.get('LOW', 0)} | Standard / baseline transaction behavior |")
        lines.append("")

        # 2. Graph Topography
        lines.append("## 2. Entity Graph Topology")
        gstats = report_data.get("graph_summary", {})
        lines.append(f"- **Total Nodes:** {gstats.get('total_nodes', 0)}")
        lines.append(f"- **Total Edges:** {gstats.get('total_edges', 0)}")
        lines.append(f"- **Connected Subgraphs:** {gstats.get('connected_components', 0)}")
        lines.append(f"- **Graph Density:** {gstats.get('density', 0.0):.6f}")
        lines.append("")

        # 3. High Priority Alerts
        lines.append("## 3. High & Critical Priority Entities")
        alerts = report_data.get("alerts", [])
        high_priority = [a for a in alerts if a.get("severity") in ("CRITICAL", "HIGH")]

        if not high_priority:
            lines.append("*No entities met the High or Critical priority threshold.*")
        else:
            for idx, a in enumerate(high_priority, 1):
                eid = a.get("entity_id", "Unknown")
                score = a.get("priority_score", 0.0)
                sev = a.get("severity", "HIGH")
                sc = a.get("score_components", {})

                lines.append(f"### 3.{idx} Entity: `{eid}` — [{sev}] Score: {score}/100")
                lines.append(
                    f"- **Score Breakdown:** Anomaly: `{sc.get('anomaly_score', 0):.2f}` | "
                    f"Behavior: `{sc.get('behavior_score', 0):.2f}` | "
                    f"Graph: `{sc.get('graph_score', 0):.2f}` | "
                    f"Network: `{sc.get('network_score', 0):.2f}`"
                )
                reasons = a.get("top_reasons", [])
                if reasons:
                    lines.append("- **Top Findings:**")
                    for r in reasons:
                        text = r.get("text") if isinstance(r, dict) else str(r)
                        lines.append(f"  - {text}")

                ev_pack = a.get("evidence_pack", [])
                if ev_pack:
                    lines.append("- **Provenance Sources:**")
                    for ev in ev_pack[:3]:
                        src_ids = ev.get("source_record_ids", [])
                        if src_ids:
                            lines.append(f"  - `{ev.get('feature')}`: verified against source records `{', '.join(src_ids[:5])}`")
                lines.append("")

        lines.append("---")
        lines.append("*Generated deterministically by Bitcoin Investigation Platform (SIH26146).*")
        return "\n".join(lines)

    def export_reports(
        self,
        output_dir: str or Path,
        run_id: str,
        report_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Save both JSON and Markdown reports to the case reports directory.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        json_file = out_path / f"run_{run_id}.json"
        md_file = out_path / f"run_{run_id}.md"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        md_content = self.generate_markdown_report(report_data)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {
            "json_report": str(json_file),
            "markdown_report": str(md_file),
        }
