from datetime import datetime, timedelta
from bson import ObjectId

from app.services import career_intelligence as ci


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    def create_index(self, *args, **kwargs):
        return None

    def find(self, query=None, sort=None):
        query = query or {}
        filtered = [doc for doc in self.docs if _matches_query(doc, query)]
        if sort:
            field, direction = sort[0]
            reverse = direction == -1
            filtered = sorted(filtered, key=lambda item: item.get(field), reverse=reverse)
        return filtered

    def find_one(self, query):
        for doc in self.docs:
            if _matches_query(doc, query):
                return doc
        return None

    def update_one(self, query, update, upsert=False):
        existing = self.find_one(query)
        payload = update.get("$set", {})
        if existing:
            existing.update(payload)
            return

        if upsert:
            new_doc = {**query, **payload}
            self.docs.append(new_doc)


def _matches_query(doc, query):
    for key, value in query.items():
        if doc.get(key) != value:
            return False
    return True


def _wire_fake_db(monkeypatch, interviews_docs=None, intelligence_docs=None):
    interviews = FakeCollection(interviews_docs or [])
    intelligence = FakeCollection(intelligence_docs or [])

    def fake_get_collection(name):
        if name == "interviews":
            return interviews
        if name == "career_intelligence":
            return intelligence
        raise KeyError(name)

    monkeypatch.setattr(ci, "get_collection", fake_get_collection)
    return interviews, intelligence


def _completed_doc(user_id, role, score, created_at):
    return {
        "_id": ObjectId(),
        "user_id": user_id,
        "role": role,
        "status": "completed",
        "total_score": score,
        "skill_scores": {
            "DSA": score,
            "System Design": score - 5,
            "Behavioral": score - 10,
            "Communication": score - 8,
        },
        "created_at": created_at,
        "completed_at": created_at,
    }


def test_complete_one_interview_updates_intelligence(monkeypatch):
    user_id = ObjectId()
    created_at = datetime.utcnow()
    interview = _completed_doc(user_id, "Backend Developer", 82, created_at)
    _wire_fake_db(monkeypatch, interviews_docs=[interview])

    result = ci.rebuild_user_intelligence(str(user_id))

    assert result["total_interviews"] == 1
    assert result["completed_interviews"] == 1
    assert result["average_score"] == 82


def test_complete_three_interviews_average_is_correct(monkeypatch):
    user_id = ObjectId()
    now = datetime.utcnow()
    interviews = [
        _completed_doc(user_id, "Backend Developer", 60, now - timedelta(days=3)),
        _completed_doc(user_id, "Backend Developer", 80, now - timedelta(days=2)),
        _completed_doc(user_id, "Backend Developer", 100, now - timedelta(days=1)),
    ]
    _wire_fake_db(monkeypatch, interviews_docs=interviews)

    result = ci.rebuild_user_intelligence(str(user_id))

    assert result["completed_interviews"] == 3
    assert result["average_score"] == 80


def test_delete_interview_rebuilds_totals(monkeypatch):
    user_id = ObjectId()
    now = datetime.utcnow()
    interviews = [
        _completed_doc(user_id, "Backend Developer", 70, now - timedelta(days=2)),
        _completed_doc(user_id, "Backend Developer", 90, now - timedelta(days=1)),
    ]
    interviews_collection, _ = _wire_fake_db(monkeypatch, interviews_docs=interviews)

    first = ci.rebuild_user_intelligence(str(user_id))
    assert first["total_interviews"] == 2

    interviews_collection.docs.pop()
    second = ci.rebuild_user_intelligence(str(user_id))
    assert second["total_interviews"] == 1
    assert second["average_score"] == 70


def test_role_breakdown_for_multiple_roles(monkeypatch):
    user_id = ObjectId()
    now = datetime.utcnow()
    interviews = [
        _completed_doc(user_id, "Backend Developer", 75, now - timedelta(days=3)),
        _completed_doc(user_id, "Data Engineer", 85, now - timedelta(days=2)),
        _completed_doc(user_id, "Data Engineer", 95, now - timedelta(days=1)),
    ]
    _wire_fake_db(monkeypatch, interviews_docs=interviews)

    result = ci.rebuild_user_intelligence(str(user_id))

    role_breakdown = {item["role"]: item for item in result["role_breakdown"]}
    assert role_breakdown["Backend Developer"]["average_score"] == 75
    assert role_breakdown["Data Engineer"]["average_score"] == 90


def test_get_or_create_avoids_not_found(monkeypatch):
    user_id = ObjectId()
    now = datetime.utcnow()
    interviews = [_completed_doc(user_id, "Backend Developer", 88, now)]
    _wire_fake_db(monkeypatch, interviews_docs=interviews, intelligence_docs=[])

    result = ci.get_or_create_user_intelligence(str(user_id))

    assert result["total_interviews"] == 1
    assert result["average_score"] == 88


def test_new_user_auto_generates_empty_intelligence(monkeypatch):
    user_id = ObjectId()
    _wire_fake_db(monkeypatch, interviews_docs=[], intelligence_docs=[])

    result = ci.get_or_create_user_intelligence(str(user_id))

    assert result["total_interviews"] == 0
    assert result["completed_interviews"] == 0
    assert result["average_score"] == 0
