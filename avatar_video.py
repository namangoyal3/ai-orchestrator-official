"""
avatar_video.py
───────────────
Renders a talking-avatar video via the HeyGen Template API (v2).

Using the Template API is the recommended approach: you create a template once
in the HeyGen dashboard (with your avatar + voice already configured), then
just inject the script text at generation time.

Flow — polling mode (default):
  1. POST to /v2/template/{template_id}/generate → get video_id
  2. Poll /v1/video_status.get until status == "completed"
  3. Download the MP4 locally
  4. Return the local file path

Flow — webhook mode (recommended for production):
  Set HEYGEN_WEBHOOK_URL in your .env. This module will:
  1. Register a webhook endpoint (once at startup via register_webhook())
  2. Submit the video job with a callback_id tied to your queue item
  3. Your FastAPI webhook handler calls resolve_from_webhook(event_data)
     which downloads the MP4 and returns the path
  Polling is always available as a fallback via generate_with_poll().

HeyGen docs:
  https://docs.heygen.com/docs/quick-start
  https://docs.heygen.com/reference/generate-from-template
  https://docs.heygen.com/reference/webhook-overview
"""

from __future__ import annotations

import time
import pathlib
import urllib.request

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config
from content_generator import VideoScript


HEYGEN_BASE = "https://api.heygen.com"
POLL_INTERVAL_S = 5    # seconds between status checks
MAX_WAIT_S = 600        # 10 min timeout for rendering


class AvatarVideoGenerator:
    def __init__(self, cfg: Config):
        self._api_key = cfg.heygen_api_key
        self._template_id = cfg.heygen_template_id
        self._headers = {
            "Accept": "application/json",
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(self, script: VideoScript, output_dir: str = ".") -> pathlib.Path:
        """
        Render the avatar video for `script` and save the MP4 to `output_dir`.
        Uses polling. For webhook-driven production pipelines, call
        submit_job() instead and handle completion via resolve_from_webhook().
        Returns the Path of the downloaded file.
        """
        video_id = self._submit_job(script)
        video_url = self._wait_for_completion(video_id)
        return self._download(video_url, script.topic, output_dir)

    def submit_job(self, script: VideoScript, callback_id: str | None = None) -> str:
        """
        Submit a video generation job and return the video_id immediately.
        Use this in webhook-driven pipelines: store the video_id in your
        content queue, then call resolve_from_webhook() when HeyGen delivers
        the avatar_video.success event.

        callback_id: optional identifier HeyGen echoes back in the webhook
                     payload — use your queue item ID so you can look it up.
        """
        return self._submit_job(script, callback_id=callback_id)

    def resolve_from_webhook(
        self,
        event_data: dict,
        output_dir: str = ".",
        topic: str = "video",
    ) -> pathlib.Path:
        """
        Called from your webhook handler after receiving avatar_video.success.
        event_data is the 'event_data' dict from the HeyGen webhook payload:
          { "video_id": "...", "url": "...", "gif_download_url": "...",
            "callback_id": "..." }
        Downloads the MP4 and returns the local path.
        """
        video_url = event_data.get("url")
        if not video_url:
            raise ValueError(f"No 'url' in HeyGen webhook event_data: {event_data}")
        return self._download(video_url, topic, output_dir)

    # ── Webhook management ────────────────────────────────────────────────────

    def register_webhook(self, callback_url: str) -> str:
        """
        Register a webhook endpoint with HeyGen for avatar_video.success/fail.
        Only needs to be called once (during deploy/setup).
        Returns the endpoint_id.

        HeyGen validates the endpoint with a quick OPTIONS request — your
        server must respond within 1 second.
        """
        resp = requests.post(
            f"{HEYGEN_BASE}/v1/webhook/endpoint.add",
            headers=self._headers,
            json={
                "url": callback_url,
                "events": ["avatar_video.success", "avatar_video.fail"],
            },
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("endpoint_id", "")

    def list_webhooks(self) -> list[dict]:
        """List all registered webhook endpoints."""
        resp = requests.get(
            f"{HEYGEN_BASE}/v1/webhook/endpoint.list",
            headers=self._headers,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("endpoints", [])

    def delete_webhook(self, endpoint_id: str) -> None:
        """Remove a webhook endpoint by ID."""
        resp = requests.delete(
            f"{HEYGEN_BASE}/v1/webhook/endpoint.delete",
            headers=self._headers,
            json={"endpoint_id": endpoint_id},
        )
        resp.raise_for_status()

    # ── HeyGen API calls ──────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=20))
    def _submit_job(self, script: VideoScript, callback_id: str | None = None) -> str:
        """
        POST to HeyGen Template API to start video generation.
        Returns video_id.

        The template must already have your avatar and voice configured in the
        HeyGen dashboard. The script text is injected via template variables.

        Template variable names depend on your template setup. The default here
        assumes a single text variable named "script". Adjust the key to match
        whatever variable name you used when building the template.
        """
        payload = {
            "caption": False,
            "title": script.topic,
            "variables": {
                "script": {
                    "name": "script",
                    "type": "text",
                    "properties": {"content": script.full_spoken_script},
                }
                # If your template splits content across multiple scenes, add
                # more entries here, e.g. "scene_2_script", "scene_3_script".
            },
        }
        if callback_id:
            payload["callback_id"] = callback_id

        url = f"{HEYGEN_BASE}/v2/template/{self._template_id}/generate"
        resp = requests.post(url, headers=self._headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        if data.get("error"):
            raise RuntimeError(f"HeyGen error: {data['error']}")

        video_id = data.get("data", {}).get("video_id")
        if not video_id:
            raise RuntimeError(f"HeyGen did not return a video_id. Response: {data}")
        return video_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=20))
    def _get_status(self, video_id: str) -> dict:
        resp = requests.get(
            f"{HEYGEN_BASE}/v1/video_status.get?video_id={video_id}",
            headers={"Accept": "application/json", "X-API-KEY": self._api_key},
        )
        resp.raise_for_status()
        return resp.json().get("data", {})

    def _wait_for_completion(self, video_id: str) -> str:
        """Poll until video is ready. Returns the video download URL."""
        elapsed = 0
        while elapsed < MAX_WAIT_S:
            status_data = self._get_status(video_id)
            status = status_data.get("status")

            if status == "completed":
                video_url = status_data.get("video_url")
                if not video_url:
                    raise RuntimeError("Status is 'completed' but no video_url found.")
                return video_url

            if status == "failed":
                raise RuntimeError(
                    f"HeyGen video generation failed. Reason: {status_data.get('error')}"
                )

            time.sleep(POLL_INTERVAL_S)
            elapsed += POLL_INTERVAL_S

        raise TimeoutError(f"Video {video_id} did not complete within {MAX_WAIT_S}s.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _download(url: str, topic: str, output_dir: str) -> pathlib.Path:
        safe_name = "".join(c if c.isalnum() or c in "_ -" else "_" for c in topic)[:60]
        filename = f"{safe_name}.mp4"
        dest = pathlib.Path(output_dir) / filename
        dest.parent.mkdir(parents=True, exist_ok=True)

        urllib.request.urlretrieve(url, dest)
        return dest
