"""Dashboard Engine — 三層架構：JSON → DSL → Renderer → HTML

內嵌於 NinjaBot-Agent，從 dashboard-skill-generator 移植。
"""
from .engine import (
    generate_dashboard,
    validate_data,
    detect_data_type,
    build_fallback_dsl,
    build_data_summary,
    list_available_sources,
    generate_dsl_with_ai,
    validate_dsl,
    resolve_source,
    assemble_html,
    render_all_widgets,
    CHART_COLORS,
    COMPONENT_REGISTRY,
)

__all__ = [
    "generate_dashboard",
    "validate_data",
    "detect_data_type",
    "build_fallback_dsl",
    "build_data_summary",
    "list_available_sources",
    "generate_dsl_with_ai",
    "validate_dsl",
    "resolve_source",
    "assemble_html",
    "render_all_widgets",
    "CHART_COLORS",
    "COMPONENT_REGISTRY",
]
