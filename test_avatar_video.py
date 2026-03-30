"""
Tests for avatar_video.py — mocks all requests and urllib calls.
Covers: submit_job, polling, webhook management, resolve_from_webhook, download.
"""

import pathlib
import pytest
from unittest.mock import MagicMock, patch, call
from tenacity import RetryError

from avatar_video import AvatarVideoGenerator, HEYGEN_BASE, POLL_INTERVAL_S


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_cfg():
    cfg = MagicMock()
    cfg.heygen_api_key = "hg-test-key"
    cfg.heygen_template_id = "tmpl-abc123"
    return cfg


def _make_script(topic="AI topic", script_text="Full spoken script."):
    script = MagicMock()
    script.topic = topic
    script.full_spoken_script = script_text
    return script


def _mock_response(status=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


# ── _submit_job ────────────────────────────────────────────────────────────────

class TestSubmitJob:
    def test_posts_to_template_generate_url(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "vid-1"}})
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            gen._submit_job(_make_script())
        url = mock_post.call_args[0][0]
        assert url == f"{HEYGEN_BASE}/v2/template/tmpl-abc123/generate"

    def test_returns_video_id(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "vid-xyz"}})
        with patch("avatar_video.requests.post", return_value=resp):
            video_id = gen._submit_job(_make_script())
        assert video_id == "vid-xyz"

    def test_payload_contains_script_text(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "vid-1"}})
        script = _make_script(script_text="My spoken script.")
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            gen._submit_job(script)
        payload = mock_post.call_args[1]["json"]
        assert payload["variables"]["script"]["properties"]["content"] == "My spoken script."

    def test_payload_contains_topic_as_title(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "vid-1"}})
        script = _make_script(topic="My Topic")
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            gen._submit_job(script)
        payload = mock_post.call_args[1]["json"]
        assert payload["title"] == "My Topic"

    def test_callback_id_included_when_provided(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "vid-1"}})
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            gen._submit_job(_make_script(), callback_id="queue-item-42")
        payload = mock_post.call_args[1]["json"]
        assert payload["callback_id"] == "queue-item-42"

    def test_callback_id_omitted_when_none(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "vid-1"}})
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            gen._submit_job(_make_script(), callback_id=None)
        payload = mock_post.call_args[1]["json"]
        assert "callback_id" not in payload

    def test_raises_on_missing_video_id(self):
        # tenacity retries 3x then raises RetryError wrapping the RuntimeError
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {}})
        with patch("avatar_video.requests.post", return_value=resp):
            with pytest.raises(RetryError) as exc_info:
                gen._submit_job(_make_script())
        assert "video_id" in str(exc_info.value.last_attempt.exception())

    def test_raises_on_heygen_error_field(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"error": {"message": "Template not found"}})
        with patch("avatar_video.requests.post", return_value=resp):
            with pytest.raises(RetryError) as exc_info:
                gen._submit_job(_make_script())
        assert "HeyGen error" in str(exc_info.value.last_attempt.exception())

    def test_api_key_in_headers(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "v1"}})
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            gen._submit_job(_make_script())
        headers = mock_post.call_args[1]["headers"]
        assert headers["X-API-KEY"] == "hg-test-key"


# ── Public submit_job (thin wrapper) ─────────────────────────────────────────

class TestPublicSubmitJob:
    def test_passes_callback_id_through(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"video_id": "vid-public"}})
        with patch("avatar_video.requests.post", return_value=resp):
            vid = gen.submit_job(_make_script(), callback_id="cb-99")
        assert vid == "vid-public"


# ── _get_status ────────────────────────────────────────────────────────────────

class TestGetStatus:
    def test_hits_video_status_endpoint(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"status": "processing"}})
        with patch("avatar_video.requests.get", return_value=resp) as mock_get:
            gen._get_status("vid-1")
        url = mock_get.call_args[0][0]
        assert "video_status.get" in url
        assert "vid-1" in url

    def test_returns_data_dict(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"status": "completed", "video_url": "https://cdn.example.com/v.mp4"}})
        with patch("avatar_video.requests.get", return_value=resp):
            data = gen._get_status("vid-1")
        assert data["status"] == "completed"
        assert data["video_url"] == "https://cdn.example.com/v.mp4"

    def test_returns_empty_dict_when_data_missing(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={})
        with patch("avatar_video.requests.get", return_value=resp):
            data = gen._get_status("vid-1")
        assert data == {}


# ── _wait_for_completion ──────────────────────────────────────────────────────

class TestWaitForCompletion:
    def test_returns_video_url_on_completed(self):
        gen = AvatarVideoGenerator(_make_cfg())
        status_data = {"status": "completed", "video_url": "https://cdn.example.com/v.mp4"}
        with patch.object(gen, "_get_status", return_value=status_data):
            with patch("avatar_video.time.sleep"):
                url = gen._wait_for_completion("vid-1")
        assert url == "https://cdn.example.com/v.mp4"

    def test_polls_through_pending_and_processing(self):
        gen = AvatarVideoGenerator(_make_cfg())
        side_effects = [
            {"status": "pending"},
            {"status": "processing"},
            {"status": "completed", "video_url": "https://cdn.example.com/v.mp4"},
        ]
        with patch.object(gen, "_get_status", side_effect=side_effects):
            with patch("avatar_video.time.sleep") as mock_sleep:
                gen._wait_for_completion("vid-1")
        assert mock_sleep.call_count == 2

    def test_raises_on_failed_status(self):
        gen = AvatarVideoGenerator(_make_cfg())
        with patch.object(gen, "_get_status", return_value={"status": "failed", "error": "bad script"}):
            with patch("avatar_video.time.sleep"):
                with pytest.raises(RuntimeError, match="failed"):
                    gen._wait_for_completion("vid-1")

    def test_raises_timeout_when_never_completes(self):
        gen = AvatarVideoGenerator(_make_cfg())
        with patch.object(gen, "_get_status", return_value={"status": "processing"}):
            with patch("avatar_video.time.sleep"):
                from avatar_video import MAX_WAIT_S
                with pytest.raises(TimeoutError):
                    gen._wait_for_completion("vid-1")

    def test_raises_when_completed_but_no_url(self):
        gen = AvatarVideoGenerator(_make_cfg())
        with patch.object(gen, "_get_status", return_value={"status": "completed"}):
            with patch("avatar_video.time.sleep"):
                with pytest.raises(RuntimeError, match="video_url"):
                    gen._wait_for_completion("vid-1")


# ── resolve_from_webhook ──────────────────────────────────────────────────────

class TestResolveFromWebhook:
    def test_downloads_from_url_in_event_data(self, tmp_path):
        gen = AvatarVideoGenerator(_make_cfg())
        event_data = {
            "video_id": "vid-1",
            "url": "https://cdn.heygen.com/video.mp4",
            "callback_id": "queue-42",
        }
        expected_path = tmp_path / "AI_topic.mp4"
        with patch.object(gen, "_download", return_value=expected_path) as mock_dl:
            result = gen.resolve_from_webhook(event_data, output_dir=str(tmp_path), topic="AI topic")
        mock_dl.assert_called_once_with("https://cdn.heygen.com/video.mp4", "AI topic", str(tmp_path))
        assert result == expected_path

    def test_raises_when_url_missing(self):
        gen = AvatarVideoGenerator(_make_cfg())
        with pytest.raises(ValueError, match="url"):
            gen.resolve_from_webhook({"video_id": "vid-1"})


# ── Webhook management ────────────────────────────────────────────────────────

class TestWebhookManagement:
    def test_register_webhook_posts_to_endpoint_add(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"endpoint_id": "ep-1"}})
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            endpoint_id = gen.register_webhook("https://my-server.com/webhooks/heygen")
        url = mock_post.call_args[0][0]
        assert url == f"{HEYGEN_BASE}/v1/webhook/endpoint.add"
        assert endpoint_id == "ep-1"

    def test_register_webhook_sends_correct_events(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {"endpoint_id": "ep-1"}})
        with patch("avatar_video.requests.post", return_value=resp) as mock_post:
            gen.register_webhook("https://my-server.com/webhooks/heygen")
        payload = mock_post.call_args[1]["json"]
        assert "avatar_video.success" in payload["events"]
        assert "avatar_video.fail" in payload["events"]
        assert payload["url"] == "https://my-server.com/webhooks/heygen"

    def test_list_webhooks_returns_endpoints(self):
        gen = AvatarVideoGenerator(_make_cfg())
        endpoints = [{"endpoint_id": "ep-1", "url": "https://example.com"}]
        resp = _mock_response(json_data={"data": {"endpoints": endpoints}})
        with patch("avatar_video.requests.get", return_value=resp):
            result = gen.list_webhooks()
        assert result == endpoints

    def test_list_webhooks_returns_empty_list_when_missing(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(json_data={"data": {}})
        with patch("avatar_video.requests.get", return_value=resp):
            result = gen.list_webhooks()
        assert result == []

    def test_delete_webhook_sends_endpoint_id(self):
        gen = AvatarVideoGenerator(_make_cfg())
        resp = _mock_response(status=200)
        with patch("avatar_video.requests.delete", return_value=resp) as mock_del:
            gen.delete_webhook("ep-to-delete")
        url = mock_del.call_args[0][0]
        assert url == f"{HEYGEN_BASE}/v1/webhook/endpoint.delete"
        payload = mock_del.call_args[1]["json"]
        assert payload["endpoint_id"] == "ep-to-delete"


# ── _download ─────────────────────────────────────────────────────────────────

class TestDownload:
    def test_creates_mp4_in_output_dir(self, tmp_path):
        with patch("avatar_video.urllib.request.urlretrieve") as mock_dl:
            path = AvatarVideoGenerator._download(
                "https://cdn.example.com/video.mp4",
                "My AI Topic",
                str(tmp_path),
            )
        assert path.suffix == ".mp4"
        assert path.parent == tmp_path
        mock_dl.assert_called_once_with("https://cdn.example.com/video.mp4", path)

    def test_sanitises_topic_for_filename(self, tmp_path):
        with patch("avatar_video.urllib.request.urlretrieve"):
            path = AvatarVideoGenerator._download(
                "https://cdn.example.com/v.mp4",
                "Topic: With! Special@Chars",
                str(tmp_path),
            )
        assert ":" not in path.name
        assert "!" not in path.name
        assert "@" not in path.name

    def test_filename_truncated_to_60_chars(self, tmp_path):
        long_topic = "A" * 100
        with patch("avatar_video.urllib.request.urlretrieve"):
            path = AvatarVideoGenerator._download(
                "https://cdn.example.com/v.mp4",
                long_topic,
                str(tmp_path),
            )
        # stem (without .mp4) should be ≤60 chars
        assert len(path.stem) <= 60
