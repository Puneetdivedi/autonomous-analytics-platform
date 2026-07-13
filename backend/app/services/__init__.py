"""Application service layer.

Services orchestrate repositories and domain logic, raising the domain
exceptions defined in :mod:`app.core.exceptions`. They are intentionally thin
and free of framework (FastAPI) concerns so they can be unit-tested directly.

Note: ``analytics_service`` and ``chat_service`` are provided by another team
and are intentionally not imported here to keep this package importable
without those modules present.
"""

from __future__ import annotations

from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.datasource_service import DataSourceService
from app.services.feedback_service import FeedbackService
from app.services.project_service import ProjectService
from app.services.report_service import ReportService
from app.services.user_service import UserService

__all__ = [
    "AuditService",
    "AuthService",
    "DataSourceService",
    "FeedbackService",
    "ProjectService",
    "ReportService",
    "UserService",
]
