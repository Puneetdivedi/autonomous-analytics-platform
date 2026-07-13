"""Agent tools package.

Each tool module exposes a plain, well-typed callable core (importable by graph
nodes without an LLM) plus a ``langchain_core.tools``-wrapped variant (``*_tool``)
for exposure to agents.
"""

from __future__ import annotations

from app.tools.chart_tool import build_chart_data, chart_tool, render_chart
from app.tools.csv_loader import infer_schema, load_csv
from app.tools.excel_loader import list_sheets, load_excel
from app.tools.file_writer import resolve_path, write_bytes, write_text
from app.tools.memory_tool import memory_tool, recall, remember
from app.tools.pandas_tool import (
    dataframe_from_rows,
    profile_dataframe,
    to_records,
)
from app.tools.pdf_generator import generate_docx, generate_pdf, generate_xlsx
from app.tools.python_tool import python_tool, run_python
from app.tools.sql_tool import run_sql, sql_tool, validate_sql
from app.tools.statistics_tool import (
    correlations,
    describe_columns,
    detect_trends,
    forecast,
    full_report,
    linear_regression,
)

#: LangChain-style tools exposed to agents.
AGENT_TOOLS = [sql_tool, python_tool, chart_tool, memory_tool]

__all__ = [
    # LangChain tool wrappers
    "sql_tool",
    "python_tool",
    "chart_tool",
    "memory_tool",
    "AGENT_TOOLS",
    # SQL
    "run_sql",
    "validate_sql",
    # Python
    "run_python",
    # pandas
    "dataframe_from_rows",
    "profile_dataframe",
    "to_records",
    # loaders
    "load_csv",
    "infer_schema",
    "load_excel",
    "list_sheets",
    # charts
    "render_chart",
    "build_chart_data",
    # file writing
    "write_bytes",
    "write_text",
    "resolve_path",
    # report generation
    "generate_pdf",
    "generate_docx",
    "generate_xlsx",
    # statistics
    "describe_columns",
    "correlations",
    "linear_regression",
    "forecast",
    "detect_trends",
    "full_report",
    # memory
    "remember",
    "recall",
]
