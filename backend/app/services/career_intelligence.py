"""Compatibility wrapper for career intelligence services.

This module preserves monkeypatch behavior in existing tests by exposing
`get_collection` at this import path and syncing it into the new service module.
"""

from app.core.database import get_collection as get_collection  # noqa: F401
from app.services import career_intelligence_service as _service


def _sync_get_collection() -> None:
    _service.get_collection = get_collection


def build_career_intelligence_payload(user_id, interviews):
    return _service.build_career_intelligence_payload(user_id, interviews)


def serialize_career_intelligence(document):
    return _service.serialize_career_intelligence(document)


def rebuild_user_intelligence(user_id):
    _sync_get_collection()
    return _service.rebuild_user_intelligence(user_id)


def get_user_intelligence(user_id):
    _sync_get_collection()
    return _service.get_user_intelligence(user_id)


def get_or_create_user_intelligence(user_id):
    _sync_get_collection()
    return _service.get_or_create_user_intelligence(user_id)
