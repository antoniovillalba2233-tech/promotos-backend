"""PayPal integration backend tests."""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Use internal backend URL for testing (per review request)
BASE_URL = "http://localhost:8001"
TEST_TOKEN = "test_paypal_token_123"
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}", "Content-Type": "application/json"}


# ============== /api/paypal/config (public) ==============

class TestPaypalConfig:
    def test_config_public_returns_200(self):
        r = requests.get(f"{BASE_URL}/api/paypal/config", timeout=10)
        assert r.status_code == 200, r.text

    def test_config_returns_client_id(self):
        r = requests.get(f"{BASE_URL}/api/paypal/config", timeout=10)
        data = r.json()
        assert data.get("client_id") == os.environ["PAYPAL_CLIENT_ID"]

    def test_config_mode_is_sandbox(self):
        r = requests.get(f"{BASE_URL}/api/paypal/config", timeout=10)
        assert r.json().get("mode") == "sandbox"

    def test_config_has_monthly_and_yearly_plans(self):
        data = requests.get(f"{BASE_URL}/api/paypal/config", timeout=10).json()
        plans = data.get("plans", {})
        assert "monthly" in plans and "yearly" in plans
        assert plans["monthly"]["amount"] == "29.99"
        assert plans["yearly"]["amount"] == "299.99"
        assert plans["monthly"]["currency"] == "USD"
        assert plans["yearly"]["currency"] == "USD"


# ============== /api/paypal/create-order (protected) ==============

class TestPaypalCreateOrder:
    def test_create_order_no_auth_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/create-order",
            json={"plan": "monthly"},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_create_order_bad_token_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/create-order",
            headers={"Authorization": "Bearer INVALID", "Content-Type": "application/json"},
            json={"plan": "monthly"},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_create_order_invalid_plan_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/create-order",
            headers=AUTH_HEADERS,
            json={"plan": "weekly"},
            timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "invalid plan" in r.json().get("detail", "").lower()

    def test_create_order_monthly_success(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/create-order",
            headers=AUTH_HEADERS,
            json={"plan": "monthly"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "order_id" in data and data["order_id"]
        assert "status" in data
        # PayPal statuses on create: CREATED / PAYER_ACTION_REQUIRED
        assert data["status"] in ("CREATED", "PAYER_ACTION_REQUIRED")
        assert "approval_url" in data and data["approval_url"]
        assert "sandbox.paypal.com" in data["approval_url"], data["approval_url"]

    def test_create_order_yearly_success(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/create-order",
            headers=AUTH_HEADERS,
            json={"plan": "yearly"},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("order_id")
        assert data.get("approval_url")
        assert "sandbox.paypal.com" in data["approval_url"]


# ============== /api/paypal/capture-order (protected) ==============

class TestPaypalCaptureOrder:
    def test_capture_no_auth_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/capture-order",
            json={"order_id": "FAKE_ORDER_ID_123"},
            timeout=15,
        )
        assert r.status_code == 401, r.text

    def test_capture_fake_order_returns_500(self):
        r = requests.post(
            f"{BASE_URL}/api/paypal/capture-order",
            headers=AUTH_HEADERS,
            json={"order_id": "FAKE_ORDER_ID_123"},
            timeout=20,
        )
        # PayPal responds with error -> backend returns 500
        assert r.status_code == 500, r.text
