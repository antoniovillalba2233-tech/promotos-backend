"""Test lesson video URLs after seed update - verifies no Rickroll and real motorcycle videos."""
import os
import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

BASE_URL = os.environ.get('EXPO_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    # fall back to reading frontend .env (uses EXPO_PUBLIC_BACKEND_URL)
    frontend_env = Path('/app/frontend/.env')
    if frontend_env.exists():
        for line in frontend_env.read_text().splitlines():
            if line.startswith('EXPO_PUBLIC_BACKEND_URL=') or line.startswith('EXPO_BACKEND_URL='):
                BASE_URL = line.split('=', 1)[1].strip().strip('"').rstrip('/')
                break
assert BASE_URL, "Could not resolve backend base URL"

TEST_TOKEN = "test_paypal_token_123"
RICKROLL = "dQw4w9WgXcQ"


@pytest.fixture(scope="module")
def auth_headers():
    return {"Authorization": f"Bearer {TEST_TOKEN}", "Content-Type": "application/json"}


class TestVideoURLsFix:
    """Verify seed_data.py update replaced Rickroll with real motorcycle videos."""

    def test_auth_me_works(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=15)
        assert r.status_code == 200, f"Auth failed: {r.status_code} {r.text}"
        data = r.json()
        assert data.get("user_id") == "user_paypaltest01"
        assert data.get("is_premium") is True, "Test user must be premium to access all lessons"

    def test_modules_returned(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/modules", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        modules = r.json()
        assert isinstance(modules, list)
        assert len(modules) == 10, f"Expected 10 modules, got {len(modules)}"
        # Each module must have lessons
        total_lessons = sum(len(m.get("lessons", [])) for m in modules)
        assert total_lessons == 37, f"Expected 37 lessons, got {total_lessons}"

    def test_no_rickroll_in_any_lesson(self, auth_headers):
        """CRITICAL: No lesson should have the Rickroll placeholder URL."""
        r = requests.get(f"{BASE_URL}/api/modules", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        modules = r.json()
        rickroll_lessons = []
        for m in modules:
            for lesson in m.get("lessons", []):
                if lesson.get("video_url") and RICKROLL in lesson["video_url"]:
                    rickroll_lessons.append(f"{m['module_id']}/{lesson['lesson_id']}: {lesson['title']}")
        assert not rickroll_lessons, f"Rickroll still present in: {rickroll_lessons}"

    def test_frenos_disco_lesson_has_correct_video(self, auth_headers):
        """The specific bug: 'Frenos a disco' must show yf8TKWxwO2I."""
        r = requests.get(f"{BASE_URL}/api/modules", headers=auth_headers, timeout=15)
        modules = r.json()
        frenos_mod = next((m for m in modules if m["module_id"] == "mod_frenos"), None)
        assert frenos_mod is not None
        # Find the 'Frenos a disco' lesson
        disco_lesson = next((l for l in frenos_mod["lessons"] if "disco" in l["title"].lower() and "circuito" not in l["title"].lower() and "verificacion" not in l["title"].lower()), None)
        assert disco_lesson is not None, f"Frenos a disco lesson not found. Lessons: {[l['title'] for l in frenos_mod['lessons']]}"
        # Fetch specific lesson detail
        r2 = requests.get(f"{BASE_URL}/api/lessons/{disco_lesson['lesson_id']}", headers=auth_headers, timeout=15)
        assert r2.status_code == 200
        lesson_detail = r2.json()
        assert "yf8TKWxwO2I" in lesson_detail["video_url"], f"Expected yf8TKWxwO2I, got: {lesson_detail['video_url']}"

    def test_all_lesson_urls_are_youtube(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/modules", headers=auth_headers, timeout=15)
        modules = r.json()
        bad = []
        for m in modules:
            for lesson in m.get("lessons", []):
                url = lesson.get("video_url", "")
                if not url or "youtube.com/watch?v=" not in url:
                    bad.append(f"{lesson['lesson_id']}: {url}")
        assert not bad, f"Non-YouTube URLs: {bad}"

    def test_multiple_unique_videos(self, auth_headers):
        """Ensure video URL diversity - at least 15 unique videos across 37 lessons."""
        r = requests.get(f"{BASE_URL}/api/modules", headers=auth_headers, timeout=15)
        modules = r.json()
        urls = set()
        for m in modules:
            for lesson in m.get("lessons", []):
                if lesson.get("video_url"):
                    urls.add(lesson["video_url"])
        assert len(urls) >= 15, f"Expected >=15 unique videos, got {len(urls)}"

    def test_module_specific_videos_relevant(self, auth_headers):
        """Spot check: frenos module should reference brake videos, motor module engine videos."""
        r = requests.get(f"{BASE_URL}/api/modules", headers=auth_headers, timeout=15)
        modules = r.json()
        # Expected IDs from seed_data.py mapping
        expected_map = {
            "mod_frenos": ["yf8TKWxwO2I", "1CLyr16IeBE", "on7rXmdyFpU", "ourxQgjQAsA"],
            "mod_motores": ["4FPUS5CwhUo", "ddSJXcuM2EI", "tzGitXVmRiw", "BcqgAKv9rg4"],
            "mod_carburador": ["dfg_zVLAccc", "StUYZlsq46I", "2LtkjG-IYbE"],
            "mod_electricidad": ["m67FZEMxAAA", "2z4JY1Ibhw4"],
        }
        for mod_id, expected_ids in expected_map.items():
            mod = next((m for m in modules if m["module_id"] == mod_id), None)
            assert mod is not None, f"Module {mod_id} missing"
            urls_str = " ".join(l.get("video_url", "") for l in mod["lessons"])
            found = [vid for vid in expected_ids if vid in urls_str]
            assert len(found) >= 1, f"None of expected videos {expected_ids} found in {mod_id}. URLs: {urls_str}"

    def test_lesson_by_id_returns_video_url_for_premium(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/lessons/lesson_1", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("video_url"), "video_url missing"
        assert RICKROLL not in data["video_url"], "Rickroll in lesson_1"
        assert data.get("locked") is False
