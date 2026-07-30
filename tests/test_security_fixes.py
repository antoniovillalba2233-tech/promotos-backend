"""Security fix verification tests (SEC-001, SEC-002, P3 hardening)."""
import os
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

load_dotenv(Path(__file__).parent.parent / ".env")

# Use PUBLIC URL as required (Kubernetes ingress)
BASE_URL = os.environ.get(
    "EXPO_PUBLIC_BACKEND_URL",
    "https://pro-motos-fix.preview.emergentagent.com",
).rstrip("/")

TEST_TOKEN = "test_paypal_token_123"
TEST_USER_ID = "user_paypaltest01"
PREMIUM_LESSON_ID = "lesson_4"
FREE_LESSON_ID = "lesson_1"
AUTH = {"Authorization": f"Bearer {TEST_TOKEN}", "Content-Type": "application/json"}


# ---------- MongoDB helpers ----------

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(scope="module")
def db():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    yield client[os.environ["DB_NAME"]]
    client.close()


@pytest.fixture(autouse=True)
def cleanup_test_payments(db):
    async def _clean():
        await db.payments.delete_many({"order_id": {"$regex": "^TEST_"}})
    _run(_clean())
    yield
    _run(_clean())


def _set_user_premium(db, is_premium: bool, expires_at):
    async def _do():
        await db.users.update_one(
            {"user_id": TEST_USER_ID},
            {"$set": {"is_premium": is_premium, "premium_expires_at": expires_at}},
        )
    _run(_do())


# ============== SEC-001: Premium expiration enforcement ==============

class TestPremiumExpirationSEC001:
    def test_expired_premium_locks_lesson_and_downgrades(self, db):
        # Set expired premium
        past = datetime.now(timezone.utc) - timedelta(days=1)
        _set_user_premium(db, True, past)

        r = requests.get(f"{BASE_URL}/api/lessons/{PREMIUM_LESSON_ID}", headers=AUTH, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("locked") is True, f"Expected locked=True, got {data}"
        assert data.get("video_url") is None, f"Expected video_url=None, got {data.get('video_url')}"

        # Auto-downgrade: is_premium should now be False in DB
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=AUTH, timeout=15)
        assert me.status_code == 200, me.text
        assert me.json().get("is_premium") is False, "User should be auto-downgraded"

    def test_future_premium_unlocks_lesson(self, db):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        _set_user_premium(db, True, future)

        r = requests.get(f"{BASE_URL}/api/lessons/{PREMIUM_LESSON_ID}", headers=AUTH, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("locked") is False, f"Expected locked=False for active premium, got {data}"
        assert data.get("video_url"), "Expected video_url to be present for active premium"

    def test_no_premium_flag_locks_lesson(self, db):
        _set_user_premium(db, False, None)
        r = requests.get(f"{BASE_URL}/api/lessons/{PREMIUM_LESSON_ID}", headers=AUTH, timeout=15)
        assert r.status_code == 200
        assert r.json().get("locked") is True

    def test_free_lesson_always_accessible(self, db):
        _set_user_premium(db, False, None)
        r = requests.get(f"{BASE_URL}/api/lessons/{FREE_LESSON_ID}", headers=AUTH, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("locked") is False
        assert data.get("video_url")


# ============== SEC-002: PayPal capture validation ==============

class TestPaypalCaptureSEC002:
    def test_replay_prevention_returns_409(self, db):
        # Insert a fake payment record
        async def _seed():
            await db.payments.insert_one({
                "payment_id": "pay_testreplay",
                "user_id": TEST_USER_ID,
                "order_id": "TEST_ORDER_REPLAY",
                "amount": 29.99,
                "currency": "USD",
                "status": "completed",
                "plan": "monthly",
                "created_at": datetime.now(timezone.utc),
            })
        _run(_seed())

        r = requests.post(
            f"{BASE_URL}/api/paypal/capture-order",
            headers=AUTH,
            json={"order_id": "TEST_ORDER_REPLAY"},
            timeout=15,
        )
        assert r.status_code == 409, r.text
        assert "already processed" in r.json().get("detail", "").lower()

    def test_capture_no_auth_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/capture-order",
            json={"order_id": "TEST_NOAUTH"},
            timeout=15,
        )
        assert r.status_code == 401

    def test_ownership_check_code_path_exists(self):
        """Verify the ownership check code lines are present in server.py."""
        src = Path(__file__).parent.parent / "server.py"
        content = src.read_text()
        assert "reference_id.startswith(f\"{user['user_id']}_\")" in content, \
            "Ownership check missing"
        assert "Order does not belong to this user" in content
        assert "expected_amount = float(expected_plan[\"amount\"])" in content, \
            "Amount validation missing"
        assert "Payment amount does not match plan price" in content
        assert "Payment currency does not match plan" in content


# ============== P3 hardening ==============

class TestP3Hardening:
    def test_unique_index_on_payments_order_id(self, db):
        async def _idx():
            return await db.payments.index_information()
        idx = _run(_idx())
        assert "order_id_1" in idx, f"Missing order_id_1 index: {idx}"
        assert idx["order_id_1"].get("unique") is True, \
            f"order_id_1 must be unique: {idx['order_id_1']}"

    def test_user_id_index_exists(self, db):
        async def _idx():
            return await db.payments.index_information()
        idx = _run(_idx())
        assert "user_id_1" in idx, f"Missing user_id_1 index: {idx}"

    def test_duplicate_order_id_insert_fails(self, db):
        async def _try_dup():
            doc = {
                "payment_id": "pay_dup1",
                "user_id": TEST_USER_ID,
                "order_id": "TEST_DUP_ORDER",
                "amount": 29.99,
                "currency": "USD",
                "status": "completed",
                "plan": "monthly",
                "created_at": datetime.now(timezone.utc),
            }
            await db.payments.insert_one(doc)
            with pytest.raises(DuplicateKeyError):
                doc["payment_id"] = "pay_dup2"
                await db.payments.insert_one(doc)
        _run(_try_dup())

    def test_session_error_returns_generic_message(self):
        """Invalid token to /api/auth/session must not leak internals."""
        r = requests.post(
            f"{BASE_URL}/api/auth/session",
            json={"session_token": "totally-invalid-token-xyz"},
            timeout=15,
        )
        # Emergent auth returns non-200 -> HTTPException(401, "Invalid session token")
        # If it hits generic except, must be "Authentication failed"
        assert r.status_code in (401, 500, 504), r.text
        detail = r.json().get("detail", "")
        # Must NOT leak stack trace / raw exception content
        forbidden = ["Traceback", "line ", "File \"/", "Exception", "motor", "httpx.", "at 0x"]
        for f in forbidden:
            assert f not in detail, f"Detail leaks internal info ({f}): {detail}"

    def test_create_order_error_generic(self):
        """Ensure create-order error returns generic message (verify code presence)."""
        src = Path(__file__).parent.parent / "server.py"
        content = src.read_text()
        assert 'detail="Failed to create payment order"' in content
        assert 'detail="Payment processing failed"' in content
        assert 'detail="Authentication failed"' in content


# ============== Regression: existing endpoints still work ==============

class TestRegression:
    def test_paypal_config_public_ok(self):
        r = requests.get(f"{BASE_URL}/api/paypal/config", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d.get("client_id")
        assert "monthly" in d.get("plans", {})

    def test_modules_with_auth_ok(self, db):
        # Ensure premium is active so lessons load fully
        _set_user_premium(db, True, datetime.now(timezone.utc) + timedelta(days=30))
        r = requests.get(f"{BASE_URL}/api/modules", headers=AUTH, timeout=15)
        assert r.status_code == 200
        modules = r.json()
        assert isinstance(modules, list)
        assert len(modules) > 0

    def test_capture_order_no_auth_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/capture-order",
            json={"order_id": "TEST_X"},
            timeout=15,
        )
        assert r.status_code == 401

    def test_create_order_with_auth_ok(self, db):
        _set_user_premium(db, True, datetime.now(timezone.utc) + timedelta(days=30))
        r = requests.post(
            f"{BASE_URL}/api/paypal/create-order",
            headers=AUTH,
            json={"plan": "monthly"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("order_id")
        assert d.get("approval_url", "").startswith("https://")
