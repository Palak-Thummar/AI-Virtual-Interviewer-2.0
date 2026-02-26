from datetime import datetime
from bson import ObjectId

from app.api.endpoints import settings as settings_api


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    def find_one(self, query):
        for doc in self.docs:
            if _matches(doc, query):
                return doc
        return None

    def find(self, query=None, sort=None):
        query = query or {}
        rows = [doc for doc in self.docs if _matches(doc, query)]
        if sort:
            field, direction = sort[0]
            reverse = direction == -1
            rows = sorted(rows, key=lambda item: item.get(field), reverse=reverse)
        return rows

    def update_one(self, query, update, upsert=False):
        target = self.find_one(query)
        payload = update.get("$set", {})
        if target:
            target.update(payload)
            return
        if upsert:
            self.docs.append({**query, **payload})

    def delete_one(self, query):
        for idx, doc in enumerate(self.docs):
            if _matches(doc, query):
                self.docs.pop(idx)
                break

    def delete_many(self, query):
        self.docs = [doc for doc in self.docs if not _matches(doc, query)]



def _matches(doc, query):
    for key, value in query.items():
        if doc.get(key) != value:
            return False
    return True



def _wire(monkeypatch, *, users=None, prefs=None, notifications=None, resumes=None, interviews=None, intelligence=None):
    collections = {
        "users": FakeCollection(users or []),
        "user_preferences": FakeCollection(prefs or []),
        "user_notifications": FakeCollection(notifications or []),
        "resumes": FakeCollection(resumes or []),
        "interviews": FakeCollection(interviews or []),
        "career_intelligence": FakeCollection(intelligence or []),
    }

    def fake_get_collection(name):
        return collections[name]

    monkeypatch.setattr(settings_api, "get_collection", fake_get_collection)
    return collections


import pytest


@pytest.mark.asyncio
async def test_new_user_preferences_auto_created(monkeypatch):
    user_id = ObjectId()
    _wire(monkeypatch)

    result = await settings_api.get_preferences(str(user_id))

    assert result["default_question_count"] == 5
    assert result["difficulty"] == "medium"


@pytest.mark.asyncio
async def test_update_preferences_persists(monkeypatch):
    user_id = ObjectId()
    collections = _wire(monkeypatch)

    payload = settings_api.PreferencesRequest(
        default_question_count=8,
        difficulty="hard",
        question_types=["mcq", "coding", "theory"],
        include_dsa=True,
        include_system_design=True,
    )

    result = await settings_api.update_preferences(payload, str(user_id))

    assert result["default_question_count"] == 8
    assert collections["user_preferences"].docs[0]["difficulty"] == "hard"


@pytest.mark.asyncio
async def test_resume_replace_flow(monkeypatch):
    user_id = ObjectId()
    collections = _wire(monkeypatch)

    doc1 = {
        "user_id": user_id,
        "is_settings_resume": True,
        "file_name": "first.pdf",
        "extracted_skills": ["Python"],
        "uploaded_at": datetime.utcnow(),
    }
    collections["resumes"].docs.append(doc1)

    collections["resumes"].update_one(
        {"user_id": user_id, "is_settings_resume": True},
        {"$set": {"user_id": user_id, "is_settings_resume": True, "file_name": "second.pdf", "extracted_skills": ["Java"]}},
        upsert=True,
    )

    docs = [doc for doc in collections["resumes"].docs if doc.get("user_id") == user_id and doc.get("is_settings_resume")]
    assert len(docs) == 1
    assert docs[0]["file_name"] == "second.pdf"


@pytest.mark.asyncio
async def test_delete_account_removes_all_data(monkeypatch):
    user_id = ObjectId()
    collections = _wire(
        monkeypatch,
        users=[{"_id": user_id, "email": "x@y.com"}],
        prefs=[{"user_id": user_id}],
        notifications=[{"user_id": user_id}],
        resumes=[{"user_id": user_id, "is_settings_resume": True}],
        interviews=[{"user_id": user_id}],
        intelligence=[{"user_id": user_id}],
    )

    await settings_api.delete_account(str(user_id))

    assert not collections["users"].docs
    assert not collections["user_preferences"].docs
    assert not collections["user_notifications"].docs
    assert not collections["resumes"].docs
    assert not collections["interviews"].docs
    assert not collections["career_intelligence"].docs
