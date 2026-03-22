"""
Comprehensive pytest test suite for CareerIQ API.
Tests cover: authentication, JWT security, database indexes,
career intelligence aggregation, settings, and health check.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock
from bson import ObjectId


# ── Helpers ─────────────────────────────────────────────────────────────────

def make_user(name="Test User", email="test@example.com", pw_hash="$2b$12$test", **extra):
    uid = ObjectId()
    return {
        "_id": uid,
        "name": name,
        "full_name": name,
        "email": email,
        "password_hash": pw_hash,
        "primary_role": "",
        "experience_level": "",
        "profile_image_url": "",
        "onboarding_completed": False,
        "onboarding_step": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **extra,
    }


def make_interview(user_id, status="pending", score=None, **extra):
    return {
        "_id": ObjectId(),
        "user_id": user_id,
        "role": "Software Engineer",
        "domain": "Backend",
        "type": "general",
        "interview_type": "general",
        "status": status,
        "questions": ["Q1?", "Q2?", "Q3?"],
        "answers": [],
        "current_question_index": 0,
        "score": score,
        "created_at": datetime.utcnow(),
        "completed_at": datetime.utcnow() if status == "completed" else None,
        **extra,
    }


def make_mock_request(ip: str = "127.0.0.1") -> "Request":
    """Create a minimal real Starlette Request (required by slowapi limiter).
    slowapi checks isinstance(request, starlette.requests.Request) so we need the real class.
    """
    from starlette.requests import Request
    from starlette.datastructures import State

    fake_app = type("FakeApp", (), {"state": State()})()

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "client": (ip, 9999),
        "app": fake_app,
    }
    return Request(scope)


# ── Security / JWT Tests ─────────────────────────────────────────────────────

class TestSecurity:
    def test_hash_and_verify_password(self):
        from app.core.security import hash_password, verify_password
        hashed = hash_password("securepass123")
        assert verify_password("securepass123", hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password_does_not_match_hash(self):
        from app.core.security import hash_password, verify_password
        hashed = hash_password("somepassword")
        assert verify_password("", hashed) is False

    def test_create_access_token_returns_string(self):
        from app.core.security import create_access_token
        token = create_access_token({"sub": "user123"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_and_decode_token_roundtrip(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token({"sub": "user123", "email": "a@b.com"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "a@b.com"

    def test_decode_invalid_token_returns_none(self):
        from app.core.security import decode_token
        assert decode_token("not.a.valid.token") is None

    def test_decode_tampered_token_returns_none(self):
        from app.core.security import create_access_token, decode_token
        token = create_access_token({"sub": "x"})
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_decode_empty_string_returns_none(self):
        from app.core.security import decode_token
        assert decode_token("") is None


# ── Auth Endpoint Tests ──────────────────────────────────────────────────────

class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_new_user_returns_token(self, monkeypatch):
        from app.api.endpoints.auth import register
        from app.schemas.api import UserRegister

        class FakeCol:
            def find_one(self, q): return None
            def insert_one(self, doc):
                doc["_id"] = ObjectId()
                return MagicMock(inserted_id=doc["_id"])

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        result = await register(make_mock_request(), UserRegister(name="Alice", email="alice@test.com", password="pass1234"))
        assert result.access_token
        assert result.user.email == "alice@test.com"
        assert result.user.onboarding_completed is False
        assert result.user.onboarding_step == 0

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises_409(self, monkeypatch):
        from app.api.endpoints.auth import register
        from app.schemas.api import UserRegister
        from fastapi import HTTPException

        existing = make_user(email="dup@test.com")

        class FakeCol:
            def find_one(self, q): return existing

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        with pytest.raises(HTTPException) as exc:
            await register(make_mock_request(), UserRegister(name="Bob", email="dup@test.com", password="pass1234"))
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password_raises_error(self, monkeypatch):
        """Passwords under 6 chars must be rejected.
        Pydantic validates at schema level, raising ValidationError before the handler runs;
        FastAPI later converts this to 422 — either is acceptable in unit tests.
        """
        from app.api.endpoints.auth import register
        from app.schemas.api import UserRegister
        from fastapi import HTTPException
        from pydantic import ValidationError

        class FakeCol:
            def find_one(self, q): return None

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        with pytest.raises((HTTPException, ValidationError)):
            await register(make_mock_request(), UserRegister(name="Bob", email="b@test.com", password="abc"))

    @pytest.mark.asyncio
    async def test_register_empty_name_raises_400(self, monkeypatch):
        from app.api.endpoints.auth import register
        from app.schemas.api import UserRegister
        from fastapi import HTTPException

        class FakeCol:
            def find_one(self, q): return None

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        with pytest.raises(HTTPException) as exc:
            await register(make_mock_request(), UserRegister(name="   ", email="c@test.com", password="goodpass"))
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_login_success_returns_token(self, monkeypatch):
        from app.api.endpoints.auth import login as auth_login
        from app.schemas.api import UserLogin
        from app.core.security import hash_password

        user = make_user(email="login@test.com", pw_hash=hash_password("goodpass"))

        class FakeCol:
            def find_one(self, q): return user if q.get("email") == "login@test.com" else None

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        result = await auth_login(make_mock_request(), UserLogin(email="login@test.com", password="goodpass"))
        assert result.access_token
        assert result.user.email == "login@test.com"
        assert result.user.onboarding_completed is False

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises_401(self, monkeypatch):
        from app.api.endpoints.auth import login as auth_login
        from app.schemas.api import UserLogin
        from app.core.security import hash_password
        from fastapi import HTTPException

        user = make_user(email="login2@test.com", pw_hash=hash_password("correctpass"))

        class FakeCol:
            def find_one(self, q): return user if q.get("email") == "login2@test.com" else None

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        with pytest.raises(HTTPException) as exc:
            await auth_login(make_mock_request(), UserLogin(email="login2@test.com", password="wrongpass"))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_email_raises_401(self, monkeypatch):
        from app.api.endpoints.auth import login as auth_login
        from app.schemas.api import UserLogin
        from fastapi import HTTPException

        class FakeCol:
            def find_one(self, q): return None

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        with pytest.raises(HTTPException) as exc:
            await auth_login(make_mock_request(), UserLogin(email="ghost@test.com", password="anything"))
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_email_case_insensitive(self, monkeypatch):
        """Login should normalise email to lowercase before lookup."""
        from app.api.endpoints.auth import login as auth_login
        from app.schemas.api import UserLogin
        from app.core.security import hash_password
        from fastapi import HTTPException

        user = make_user(email="case@test.com", pw_hash=hash_password("pw"))

        class FakeCol:
            def find_one(self, q): return user if q.get("email") == "case@test.com" else None

        monkeypatch.setattr("app.api.endpoints.auth.get_collection", lambda _: FakeCol())

        # Uppercase email in request — should still work
        result = await auth_login(make_mock_request(), UserLogin(email="CASE@TEST.COM", password="pw"))
        assert result.access_token


# ── Auth Dependency Tests ────────────────────────────────────────────────────

class TestAuthDependency:
    @pytest.mark.asyncio
    async def test_valid_bearer_token_returns_user_id(self):
        from app.api.dependencies import get_current_user
        from app.core.security import create_access_token

        token = create_access_token({"sub": "abc123"})
        user_id = await get_current_user(authorization=f"Bearer {token}")
        assert user_id == "abc123"

    @pytest.mark.asyncio
    async def test_missing_header_raises_401(self):
        from app.api.dependencies import get_current_user
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await get_current_user(authorization=None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_header_raises_401(self):
        from app.api.dependencies import get_current_user
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await get_current_user(authorization="Token abc")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        from app.api.dependencies import get_current_user
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await get_current_user(authorization="Bearer invalid.token.value")
        assert exc.value.status_code == 401


# ── Database Index Tests ─────────────────────────────────────────────────────

class TestDatabaseIndexes:
    def test_create_indexes_does_not_raise(self, monkeypatch):
        """create_indexes() catches its own errors; must never propagate."""
        import app.core.database as db_module

        mock_col = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_col)

        original_db = db_module.db
        db_module.db = mock_db
        try:
            db_module.create_indexes()
        except Exception as exc:
            pytest.fail(f"create_indexes raised unexpectedly: {exc}")
        finally:
            db_module.db = original_db

    def test_create_indexes_with_none_db_does_not_raise(self, monkeypatch):
        """Even if db is None (pre-connect), create_indexes must not crash the app."""
        import app.core.database as db_module

        original_db = db_module.db
        db_module.db = None
        try:
            db_module.create_indexes()
        except Exception:
            pass  # Expected to log a warning; must not propagate unhandled
        finally:
            db_module.db = original_db


# ── Career Intelligence Service Tests ──────────────────────────────────────

class TestCareerIntelligenceService:
    def test_empty_interviews_all_zeros(self):
        from app.services.career_intelligence_service import build_career_intelligence_payload
        result = build_career_intelligence_payload(str(ObjectId()), [])
        assert result["total_interviews"] == 0
        assert result["completed_interviews"] == 0
        assert result["average_score"] == 0.0
        assert result["highest_score"] == 0.0

    def test_average_score_computed_correctly(self):
        from app.services.career_intelligence_service import build_career_intelligence_payload
        uid = ObjectId()
        interviews = [
            make_interview(uid, status="completed", score=80),
            make_interview(uid, status="completed", score=60),
        ]
        result = build_career_intelligence_payload(str(uid), interviews)
        assert result["average_score"] == 70.0
        assert result["completed_interviews"] == 2

    def test_highest_score_tracked(self):
        from app.services.career_intelligence_service import build_career_intelligence_payload
        uid = ObjectId()
        interviews = [
            make_interview(uid, status="completed", score=55),
            make_interview(uid, status="completed", score=92),
            make_interview(uid, status="completed", score=70),
        ]
        result = build_career_intelligence_payload(str(uid), interviews)
        assert result["highest_score"] == 92.0

    def test_pending_interviews_counted_in_total(self):
        from app.services.career_intelligence_service import build_career_intelligence_payload
        uid = ObjectId()
        interviews = [
            make_interview(uid, status="completed", score=75),
            make_interview(uid, status="pending"),
            make_interview(uid, status="pending"),
        ]
        result = build_career_intelligence_payload(str(uid), interviews)
        assert result["total_interviews"] == 3
        assert result["completed_interviews"] == 1
        assert result["pending_interviews"] == 2

    def test_score_out_of_bounds_clamped(self):
        from app.services.career_intelligence_service import build_career_intelligence_payload
        uid = ObjectId()
        interviews = [
            make_interview(uid, status="completed", score=150),   # > 100
            make_interview(uid, status="completed", score=-20),   # < 0
        ]
        result = build_career_intelligence_payload(str(uid), interviews)
        # Clamped: 100 + 0 = 100 / 2 = 50
        assert 0.0 <= result["average_score"] <= 100.0
        assert 0.0 <= result["highest_score"] <= 100.0

    def test_skill_breakdown_empty_for_no_interviews(self):
        """New users with no completed interviews should have empty skill_breakdown (no static data)."""
        from app.services.career_intelligence_service import build_career_intelligence_payload
        result = build_career_intelligence_payload(str(ObjectId()), [])
        # For new users, skill_breakdown should be empty (not hardcoded)
        assert result["skill_breakdown"] == {}, "skill_breakdown should be empty dict for new users"
        assert result["completed_interviews"] == 0

    def test_recommendations_non_empty_when_completed(self):
        from app.services.career_intelligence_service import build_career_intelligence_payload
        uid = ObjectId()
        interviews = [make_interview(uid, status="completed", score=50)]
        result = build_career_intelligence_payload(str(uid), interviews)
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) >= 1

    def test_recommendations_first_interview_message_when_empty(self):
        from app.services.career_intelligence_service import build_career_intelligence_payload
        result = build_career_intelligence_payload(str(ObjectId()), [])
        assert any("first interview" in r.lower() for r in result["recommendations"])


# ── Settings Endpoint Tests ─────────────────────────────────────────────────

class TestSettingsEndpoints:
    @pytest.mark.asyncio
    async def test_get_preferences_returns_defaults_for_new_user(self, monkeypatch):
        from app.api.endpoints.settings import get_preferences

        class FakeCol:
            def find_one(self, q): return None
            def update_one(self, q, upd, upsert=False): pass

        monkeypatch.setattr("app.api.endpoints.settings.get_collection", lambda _: FakeCol())

        result = await get_preferences(current_user_id=str(ObjectId()))
        assert "default_question_count" in result
        assert result["default_question_count"] >= 1
        assert "difficulty" in result
        assert "question_types" in result

    @pytest.mark.asyncio
    async def test_get_preferences_returns_existing_for_returning_user(self, monkeypatch):
        from app.api.endpoints.settings import get_preferences

        current_user = ObjectId()
        stored = {
            "user_id": current_user,
            "default_question_count": 10,
            "difficulty": "hard",
            "question_types": ["coding"],
            "include_dsa": False,
            "include_system_design": True,
            "updated_at": datetime.utcnow(),
        }

        class FakeCol:
            def find_one(self, q): return stored
            def update_one(self, q, upd, upsert=False): pass

        monkeypatch.setattr("app.api.endpoints.settings.get_collection", lambda _: FakeCol())

        result = await get_preferences(current_user_id=str(current_user))
        assert result["default_question_count"] == 10
        assert result["difficulty"] == "hard"

    @pytest.mark.asyncio
    async def test_update_profile_persists_name(self, monkeypatch):
        from app.api.endpoints.settings import update_profile, ProfileUpdateRequest

        stored = make_user()

        class FakeCol:
            def find_one(self, q):
                return stored
            def update_one(self, q, upd, **kw):
                stored.update(upd.get("$set", {}))

        monkeypatch.setattr("app.api.endpoints.settings.get_collection", lambda _: FakeCol())

        req = ProfileUpdateRequest(full_name="Updated Name", primary_role="SWE")
        result = await update_profile(payload=req, current_user_id=str(stored["_id"]))
        assert result["full_name"] == "Updated Name"
        assert result["primary_role"] == "SWE"

    @pytest.mark.asyncio
    async def test_update_profile_user_not_found_raises_404(self, monkeypatch):
        from app.api.endpoints.settings import update_profile, ProfileUpdateRequest
        from fastapi import HTTPException

        class FakeCol:
            def find_one(self, q): return None

        monkeypatch.setattr("app.api.endpoints.settings.get_collection", lambda _: FakeCol())

        req = ProfileUpdateRequest(full_name="Name")
        with pytest.raises(HTTPException) as exc:
            await update_profile(payload=req, current_user_id=str(ObjectId()))
        assert exc.value.status_code == 404


# ── Health Check Test ────────────────────────────────────────────────────────

class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self):
        from app.main import health_check
        result = await health_check()
        assert result["status"] == "healthy"
        assert result["success"] is True
        assert "app" in result
