"""
Tests for linkedin_publisher.py — mocks all requests calls.
Verifies the 4-step LinkedIn video upload flow:
  initializeUpload → PUT chunks (+ ETags) → finalizeUpload → wait → POST /rest/posts
"""

import pytest
from unittest.mock import MagicMock, patch, call, mock_open
import pathlib

from linkedin_publisher import LinkedInPublisher, LINKEDIN_REST, LINKEDIN_VERSION


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_cfg():
    cfg = MagicMock()
    cfg.linkedin_access_token = "test-token"
    cfg.linkedin_person_urn = "urn:li:person:abc123"
    return cfg


def _mock_response(status=200, json_data=None, headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {}
    resp.headers = headers or {}
    resp.raise_for_status = MagicMock()
    return resp


# ── _headers ──────────────────────────────────────────────────────────────────

class TestHeaders:
    def test_mandatory_linkedin_version_header(self):
        pub = LinkedInPublisher(_make_cfg())
        h = pub._headers()
        assert h["LinkedIn-Version"] == LINKEDIN_VERSION

    def test_bearer_token_present(self):
        pub = LinkedInPublisher(_make_cfg())
        h = pub._headers()
        assert h["Authorization"] == "Bearer test-token"

    def test_extra_headers_merged(self):
        pub = LinkedInPublisher(_make_cfg())
        h = pub._headers({"X-Custom": "value"})
        assert h["X-Custom"] == "value"
        assert "LinkedIn-Version" in h   # not overwritten


# ── _initialize_upload ────────────────────────────────────────────────────────

class TestInitializeUpload:
    def test_posts_to_correct_url(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(json_data={
            "value": {
                "video": "urn:li:video:V1",
                "uploadInstructions": [{"uploadUrl": "https://upload.example.com", "firstByte": 0, "lastByte": 99}],
                "uploadToken": "tok123",
            }
        })
        with patch("linkedin_publisher.requests.post", return_value=resp) as mock_post:
            pub._initialize_upload(100)
            url = mock_post.call_args[0][0]
            assert url == f"{LINKEDIN_REST}/videos?action=initializeUpload"

    def test_returns_urn_instructions_token(self):
        pub = LinkedInPublisher(_make_cfg())
        instructions = [{"uploadUrl": "https://u.example.com", "firstByte": 0, "lastByte": 49}]
        resp = _mock_response(json_data={
            "value": {
                "video": "urn:li:video:V1",
                "uploadInstructions": instructions,
                "uploadToken": "tok",
            }
        })
        with patch("linkedin_publisher.requests.post", return_value=resp):
            urn, instrs, token = pub._initialize_upload(50)
        assert urn == "urn:li:video:V1"
        assert instrs == instructions
        assert token == "tok"

    def test_missing_upload_token_defaults_to_empty_string(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(json_data={
            "value": {
                "video": "urn:li:video:V1",
                "uploadInstructions": [{"uploadUrl": "u", "firstByte": 0, "lastByte": 9}],
                # no uploadToken key
            }
        })
        with patch("linkedin_publisher.requests.post", return_value=resp):
            _, _, token = pub._initialize_upload(10)
        assert token == ""

    def test_payload_contains_owner_and_file_size(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(json_data={
            "value": {
                "video": "urn:li:video:V1",
                "uploadInstructions": [],
                "uploadToken": "",
            }
        })
        with patch("linkedin_publisher.requests.post", return_value=resp) as mock_post:
            pub._initialize_upload(12345)
        payload = mock_post.call_args[1]["json"]
        req = payload["initializeUploadRequest"]
        assert req["owner"] == "urn:li:person:abc123"
        assert req["fileSizeBytes"] == 12345


# ── _upload_video (chunked PUT) ───────────────────────────────────────────────

class TestUploadVideo:
    def _make_instructions(self, chunks):
        """chunks: list of (first, last) byte ranges"""
        return [{"uploadUrl": f"https://upload.example.com/part{i}",
                 "firstByte": f, "lastByte": l}
                for i, (f, l) in enumerate(chunks)]

    def test_single_chunk_returns_one_etag(self):
        pub = LinkedInPublisher(_make_cfg())
        instructions = self._make_instructions([(0, 99)])

        put_resp = _mock_response(status=200, headers={"ETag": "etag-1"})
        fake_data = b"x" * 100
        with patch("builtins.open", mock_open(read_data=fake_data)):
            with patch("linkedin_publisher.requests.put", return_value=put_resp) as mock_put:
                # Patch the file object's seek/read behaviour
                mock_file = MagicMock()
                mock_file.__enter__ = lambda s: mock_file
                mock_file.__exit__ = MagicMock(return_value=False)
                mock_file.seek = MagicMock()
                mock_file.read.return_value = fake_data
                with patch("builtins.open", return_value=mock_file):
                    etags = pub._upload_video(pathlib.Path("test.mp4"), instructions)
        assert etags == ["etag-1"]

    def test_two_chunks_two_puts_two_etags(self):
        pub = LinkedInPublisher(_make_cfg())
        instructions = self._make_instructions([(0, 3), (4, 7)])

        responses = [
            _mock_response(status=200, headers={"ETag": "etag-a"}),
            _mock_response(status=200, headers={"ETag": "etag-b"}),
        ]
        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.seek = MagicMock()
        mock_file.read.side_effect = [b"abcd", b"efgh"]

        with patch("builtins.open", return_value=mock_file):
            with patch("linkedin_publisher.requests.put", side_effect=responses) as mock_put:
                etags = pub._upload_video(pathlib.Path("test.mp4"), instructions)

        assert etags == ["etag-a", "etag-b"]
        assert mock_put.call_count == 2

    def test_put_url_matches_instruction(self):
        pub = LinkedInPublisher(_make_cfg())
        url = "https://upload.example.com/specific-part"
        instructions = [{"uploadUrl": url, "firstByte": 0, "lastByte": 4}]

        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.seek = MagicMock()
        mock_file.read.return_value = b"hello"

        put_resp = _mock_response(status=200, headers={"ETag": "e1"})
        with patch("builtins.open", return_value=mock_file):
            with patch("linkedin_publisher.requests.put", return_value=put_resp) as mock_put:
                pub._upload_video(pathlib.Path("test.mp4"), instructions)
        assert mock_put.call_args[0][0] == url

    def test_lowercase_etag_header_accepted(self):
        """LinkedIn sometimes returns 'etag' instead of 'ETag'."""
        pub = LinkedInPublisher(_make_cfg())
        instructions = [{"uploadUrl": "https://u.example.com", "firstByte": 0, "lastByte": 2}]
        put_resp = _mock_response(status=200, headers={"etag": "lowercase-etag"})

        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.seek = MagicMock()
        mock_file.read.return_value = b"abc"

        with patch("builtins.open", return_value=mock_file):
            with patch("linkedin_publisher.requests.put", return_value=put_resp):
                etags = pub._upload_video(pathlib.Path("test.mp4"), instructions)
        assert etags == ["lowercase-etag"]

    def test_missing_etag_header_stored_as_empty_string(self):
        pub = LinkedInPublisher(_make_cfg())
        instructions = [{"uploadUrl": "https://u.example.com", "firstByte": 0, "lastByte": 2}]
        put_resp = _mock_response(status=200, headers={})

        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: mock_file
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.seek = MagicMock()
        mock_file.read.return_value = b"abc"

        with patch("builtins.open", return_value=mock_file):
            with patch("linkedin_publisher.requests.put", return_value=put_resp):
                etags = pub._upload_video(pathlib.Path("test.mp4"), instructions)
        assert etags == [""]


# ── _finalize_upload ──────────────────────────────────────────────────────────

class TestFinalizeUpload:
    def test_posts_to_correct_url(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=200)
        with patch("linkedin_publisher.requests.post", return_value=resp) as mock_post:
            pub._finalize_upload("urn:li:video:V1", "tok", ["e1", "e2"])
        url = mock_post.call_args[0][0]
        assert url == f"{LINKEDIN_REST}/videos?action=finalizeUpload"

    def test_payload_contains_urn_token_etags_in_order(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=200)
        with patch("linkedin_publisher.requests.post", return_value=resp) as mock_post:
            pub._finalize_upload("urn:li:video:V1", "mytoken", ["etag-1", "etag-2"])
        payload = mock_post.call_args[1]["json"]
        req = payload["finalizeUploadRequest"]
        assert req["video"] == "urn:li:video:V1"
        assert req["uploadToken"] == "mytoken"
        assert req["uploadedPartIds"] == ["etag-1", "etag-2"]


# ── _wait_for_processing ──────────────────────────────────────────────────────

class TestWaitForProcessing:
    def test_returns_immediately_when_available(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=200, json_data={"status": "AVAILABLE"})
        with patch("linkedin_publisher.requests.get", return_value=resp):
            with patch("linkedin_publisher.time.sleep") as mock_sleep:
                pub._wait_for_processing("urn:li:video:V1")
        mock_sleep.assert_not_called()

    def test_polls_until_available(self):
        pub = LinkedInPublisher(_make_cfg())
        responses = [
            _mock_response(status=200, json_data={"status": "PROCESSING"}),
            _mock_response(status=200, json_data={"status": "PROCESSING"}),
            _mock_response(status=200, json_data={"status": "AVAILABLE"}),
        ]
        with patch("linkedin_publisher.requests.get", side_effect=responses):
            with patch("linkedin_publisher.time.sleep") as mock_sleep:
                pub._wait_for_processing("urn:li:video:V1")
        assert mock_sleep.call_count == 2

    def test_url_encodes_urn_colons(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=200, json_data={"status": "AVAILABLE"})
        with patch("linkedin_publisher.requests.get", return_value=resp) as mock_get:
            with patch("linkedin_publisher.time.sleep"):
                pub._wait_for_processing("urn:li:video:V1")
        url = mock_get.call_args[0][0]
        assert "urn%3Ali%3Avideo%3AV1" in url

    def test_does_not_raise_on_timeout(self):
        """Should not raise — just returns and lets the caller attempt posting."""
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=200, json_data={"status": "PROCESSING"})
        with patch("linkedin_publisher.requests.get", return_value=resp):
            with patch("linkedin_publisher.time.sleep"):
                # Should complete (not raise) even if never AVAILABLE
                pub._wait_for_processing("urn:li:video:V1", timeout_s=10)


# ── _create_post ──────────────────────────────────────────────────────────────

class TestCreatePost:
    def _make_script(self):
        script = MagicMock()
        script.topic = "AI topic"
        script.linkedin_post_text = "Caption text #AI #Tech"
        return script

    def test_posts_to_rest_posts(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=201, headers={"x-restli-id": "urn:li:share:123"})
        with patch("linkedin_publisher.requests.post", return_value=resp) as mock_post:
            pub._create_post("urn:li:video:V1", self._make_script())
        url = mock_post.call_args[0][0]
        assert url == f"{LINKEDIN_REST}/posts"

    def test_returns_post_urn_from_header(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=201, headers={"x-restli-id": "urn:li:share:999"})
        with patch("linkedin_publisher.requests.post", return_value=resp):
            urn = pub._create_post("urn:li:video:V1", self._make_script())
        assert urn == "urn:li:share:999"

    def test_payload_structure(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=201, headers={"x-restli-id": "urn:li:share:1"})
        with patch("linkedin_publisher.requests.post", return_value=resp) as mock_post:
            pub._create_post("urn:li:video:V1", self._make_script())
        payload = mock_post.call_args[1]["json"]
        assert payload["author"] == "urn:li:person:abc123"
        assert payload["visibility"] == "PUBLIC"
        assert payload["lifecycleState"] == "PUBLISHED"
        assert payload["content"]["media"]["id"] == "urn:li:video:V1"
        assert payload["content"]["media"]["title"] == "AI topic"
        assert payload["commentary"] == "Caption text #AI #Tech"

    def test_uppercase_header_fallback(self):
        pub = LinkedInPublisher(_make_cfg())
        resp = _mock_response(status=201, headers={"X-RestLi-Id": "urn:li:share:456"})
        with patch("linkedin_publisher.requests.post", return_value=resp):
            urn = pub._create_post("urn:li:video:V1", self._make_script())
        assert urn == "urn:li:share:456"


# ── publish (integration) ─────────────────────────────────────────────────────

class TestPublish:
    def _make_video_path(self, size=1000, tmp_path=None):
        if tmp_path:
            p = tmp_path / "test.mp4"
            p.write_bytes(b"x" * size)
            return p
        p = MagicMock(spec=pathlib.Path)
        p.stat.return_value.st_size = size
        return p

    def test_full_flow_calls_all_steps(self, tmp_path):
        pub = LinkedInPublisher(_make_cfg())
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"x" * 100)

        instructions = [{"uploadUrl": "https://upload.example.com", "firstByte": 0, "lastByte": 99}]
        init_resp = _mock_response(json_data={
            "value": {
                "video": "urn:li:video:V1",
                "uploadInstructions": instructions,
                "uploadToken": "tok",
            }
        })
        finalize_resp = _mock_response(status=200)
        post_resp = _mock_response(status=201, headers={"x-restli-id": "urn:li:share:1"})
        status_resp = _mock_response(status=200, json_data={"status": "AVAILABLE"})

        with patch("linkedin_publisher.requests.post",
                   side_effect=[init_resp, finalize_resp, post_resp]) as mock_post:
            with patch("linkedin_publisher.requests.put",
                       return_value=_mock_response(status=200, headers={"ETag": "e1"})):
                with patch("linkedin_publisher.requests.get", return_value=status_resp):
                    with patch("linkedin_publisher.time.sleep"):
                        script = MagicMock()
                        script.topic = "T"
                        script.linkedin_post_text = "Caption"
                        result = pub.publish(video_path, script)

        assert result == "urn:li:share:1"
        # Should have called POST 3 times: initializeUpload, finalizeUpload, /rest/posts
        assert mock_post.call_count == 3
