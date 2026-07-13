"""Report generator node — renders a downloadable PDF of the analysis.

The file is written to ``settings.report_dir``; the service layer persists a
``Report`` row from the ``report`` payload this node returns.
"""

from __future__ import annotations

import os
from typing import Any

import anyio

from app.core.config import settings
from app.graphs.nodes._helpers import event, run_node


def _bullets(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


def _build_sections(state: dict[str, Any]) -> list[dict[str, Any]]:
    insights = state.get("insights") or {}
    recs = state.get("recommendations") or []
    sections: list[dict[str, Any]] = []

    if insights.get("executive_summary"):
        sections.append({"heading": "Executive Summary", "body": insights["executive_summary"]})
    if insights.get("key_findings"):
        sections.append({"heading": "Key Findings", "body": _bullets(insights["key_findings"])})
    if insights.get("root_cause"):
        sections.append({"heading": "Root Cause Analysis", "body": insights["root_cause"]})
    if recs:
        sections.append(
            {
                "heading": "Recommendations",
                "table": {
                    "columns": ["Title", "Impact", "Effort", "Detail"],
                    "rows": [
                        {
                            "Title": r.get("title", ""),
                            "Impact": r.get("impact", ""),
                            "Effort": r.get("effort", ""),
                            "Detail": r.get("detail", ""),
                        }
                        for r in recs
                    ],
                },
            }
        )
    if insights.get("risks"):
        sections.append({"heading": "Risks", "body": _bullets(insights["risks"])})
    if insights.get("opportunities"):
        sections.append({"heading": "Opportunities", "body": _bullets(insights["opportunities"])})
    return sections


def _generate(state: dict[str, Any], out_path: str, title: str) -> str:
    from app.tools.pdf_generator import generate_pdf

    sections = _build_sections(state)
    charts_b64 = [c.get("image_b64") for c in (state.get("charts") or []) if c.get("image_b64")]
    return generate_pdf(title, sections, charts_b64, out_path)


async def report_generator(state: dict[str, Any]) -> dict[str, Any]:
    async def body(s: dict[str, Any]) -> dict[str, Any]:
        question = s.get("question", "Analysis")
        summary = (s.get("insights") or {}).get("executive_summary") or question
        title = summary[:80] or "Analysis Report"
        message_id = s.get("message_id", "report")
        out_path = os.path.join(settings.report_dir, f"{message_id}.pdf")
        path = await anyio.to_thread.run_sync(_generate, s, out_path, title)
        report = {
            "message_id": message_id,
            "project_id": s.get("project_id"),
            "title": title,
            "format": "pdf",
            "file_path": path,
        }
        return {"report": report, "events": [event("artifact", "report_generator", report=report)]}

    return await run_node("report_generator", "report_generator", state, body)
