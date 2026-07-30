"""Tests for new payment methods (CBU/AstroPay/WhatsApp) - PayPal removed."""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/") if os.environ.get("EXPO_PUBLIC_BACKEND_URL") else None
if not BASE_URL:
    # fallback via frontend .env
    import re
    fe_env = Path("/app/frontend/.env").read_text()
    m = re.search(r"EXPO_PUBLIC_BACKEND_URL=(\S+)", fe_env)
    BASE_URL = m.group(1).rstrip("/")

TEST_TOKEN = "test_paypal_token_123"
AUTH = {"Authorization": f"Bearer {TEST_TOKEN}"}


# ============= PayPal removal verification =============
class TestPayPalRemoved:
    def test_paypal_config_gone(self):
        r = requests.get(f"{BASE_URL}/api/paypal/config", timeout=15)
        assert r.status_code == 404, f"PayPal config still available: {r.status_code}"

    def test_paypal_create_order_gone(self):
        r = requests.post(f"{BASE_URL}/api/paypal/create-order", json={"plan": "monthly"}, headers=AUTH, timeout=15)
        assert r.status_code == 404

    def test_paypal_capture_order_gone(self):
        r = requests.post(f"{BASE_URL}/api/paypal/capture-order", json={"order_id": "x"}, headers=AUTH, timeout=15)
        assert r.status_code == 404


# ============= Payment Config (public) =============
class TestPaymentConfig:
    def test_config_public(self):
        r = requests.get(f"{BASE_URL}/api/payment/config", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "plans" in data and "methods" in data
        # plans
        assert data["plans"]["monthly"]["amount_usd"] == "15.00"
        assert data["plans"]["monthly"]["amount_ars"] == "15000"
        assert data["plans"]["yearly"]["amount_usd"] == "150.00"
        assert data["plans"]["yearly"]["amount_ars"] == "150000"
        # methods
        cbu = data["methods"]["cbu"]
        assert cbu["cbu"] == "1430001713015367820013"
        assert cbu["alias"] == "ser.bru.22"
        assert cbu["holder"] == "Sergio Antonio Villalba"
        assert cbu["bank"] == "Bruban"
        astropay = data["methods"]["astropay"]
        assert astropay["email"] == "servillalba.49.sv@gmail.com"
        assert astropay["cbu_ars"] == "0000177500099546600465"
        assert astropay["account_number"] == "848422020650"
        assert astropay["routing_number"] == "043087080"
        assert astropay["swift"] == "SSBAUS32"
        wa = data["methods"]["whatsapp"]
        assert wa["number"] == "+5491122728226"


# ============= Payment Request =============
class TestPaymentRequest:
    def test_request_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/payment/request", json={"plan": "monthly", "method": "cbu"}, timeout=15)
        assert r.status_code == 401

    def test_request_monthly_cbu(self):
        r = requests.post(f"{BASE_URL}/api/payment/request",
                          json={"plan": "monthly", "method": "cbu"}, headers=AUTH, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["plan"] == "monthly"
        assert d["method"] == "cbu"
        assert d["amount_usd"] == "15.00"
        assert d["amount_ars"] == "15000"
        assert d["status"] == "pending"
        assert d["payment_id"].startswith("pay_")
        assert "wa.me" in d["whatsapp_url"]
        assert "5491122728226" in d["whatsapp_url"]
        assert d["payment_info"]["cbu"] == "1430001713015367820013"
        pytest.pay_id_monthly = d["payment_id"]

    def test_request_yearly_astropay(self):
        r = requests.post(f"{BASE_URL}/api/payment/request",
                          json={"plan": "yearly", "method": "astropay"}, headers=AUTH, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["plan"] == "yearly"
        assert d["method"] == "astropay"
        assert d["amount_usd"] == "150.00"
        assert d["amount_ars"] == "150000"
        assert d["payment_info"]["swift"] == "SSBAUS32"
        pytest.pay_id_yearly = d["payment_id"]

    def test_request_whatsapp(self):
        r = requests.post(f"{BASE_URL}/api/payment/request",
                          json={"plan": "monthly", "method": "whatsapp"}, headers=AUTH, timeout=15)
        assert r.status_code == 200
        assert r.json()["payment_info"]["number"] == "+5491122728226"

    def test_invalid_plan(self):
        r = requests.post(f"{BASE_URL}/api/payment/request",
                          json={"plan": "weekly", "method": "cbu"}, headers=AUTH, timeout=15)
        assert r.status_code == 400

    def test_invalid_method(self):
        r = requests.post(f"{BASE_URL}/api/payment/request",
                          json={"plan": "monthly", "method": "bitcoin"}, headers=AUTH, timeout=15)
        assert r.status_code == 400


# ============= Confirm + Status + List =============
class TestPaymentLifecycle:
    def test_confirm_payment(self):
        pid = getattr(pytest, "pay_id_monthly", None)
        assert pid, "monthly payment_id missing (previous test failed)"
        r = requests.post(f"{BASE_URL}/api/payment/confirm",
                          json={"payment_id": pid, "transfer_reference": "TEST-REF-001"},
                          headers=AUTH, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "awaiting_verification"

    def test_get_status_after_confirm(self):
        pid = getattr(pytest, "pay_id_monthly", None)
        r = requests.get(f"{BASE_URL}/api/payment/status/{pid}", headers=AUTH, timeout=15)
        assert r.status_code == 200
        assert r.json()["status"] == "awaiting_verification"

    def test_status_requires_auth(self):
        pid = getattr(pytest, "pay_id_monthly", "pay_nope")
        r = requests.get(f"{BASE_URL}/api/payment/status/{pid}", timeout=15)
        assert r.status_code == 401

    def test_my_payments(self):
        r = requests.get(f"{BASE_URL}/api/payment/my-payments", headers=AUTH, timeout=15)
        assert r.status_code == 200
        payments = r.json()
        assert isinstance(payments, list)
        assert len(payments) >= 2
        # ensure no _id leaked
        for p in payments:
            assert "_id" not in p


# ============= Regression: Existing endpoints =============
class TestRegression:
    def test_auth_me(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=AUTH, timeout=15)
        assert r.status_code == 200
        assert r.json()["user_id"] == "user_paypaltest01"

    def test_auth_me_unauth(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 401

    def test_modules(self):
        r = requests.get(f"{BASE_URL}/api/modules", headers=AUTH, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_modules_unauth(self):
        r = requests.get(f"{BASE_URL}/api/modules", timeout=15)
        assert r.status_code == 401

    def test_progress(self):
        r = requests.get(f"{BASE_URL}/api/progress", headers=AUTH, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "overall_progress" in d and "modules" in d
