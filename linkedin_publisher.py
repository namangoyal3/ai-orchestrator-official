"""
linkedin_publisher.py
─────────────────────
Posts a video to LinkedIn using the current (non-deprecated) REST APIs.

⚠️  Migration note (2024-2025):
    The UGC Posts API (/v2/ugcPosts) and Assets API (/v2/assets, /rest/assets)
    are deprecated. This module uses the current APIs exclusively:
      • Videos API  — /rest/videos
      • Posts API   — /rest/posts
    See: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/videos-api
         https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api

Flow (LinkedIn's 4-step video upload):
  1. initializeUpload → get video URN + upload URL(s) + uploadToken
  2. PUT the binary MP4 (chunked for >4MB files) → collect ETag(s)
  3. finalizeUpload  → confirm all parts uploaded
  4. POST /rest/posts → create the visible LinkedIn post

Required OAuth scope: w_member_social
Required header:      LinkedIn-Version: 202601  (mandatory; valid for 1 year)
"""

from __future__ import annotations

import math
import pathlib
import time

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config
from content_generator import VideoScript


LINKEDIN_REST = "https://api.linkedin.com/rest"
LINKEDIN_VERSION = "202601"
CHUNK_SIZE = 4 * 1024 * 1024   # 4 MB — LinkedIn's required chunk size for multipart


class LinkedInPublisher:
    def __init__(self, cfg: Config):
        self._token = cfg.linkedin_access_token
        self._person_urn = cfg.linkedin_person_urn

    def _headers(self, extra: dict | None = None) -> dict:
        h = {
            "Authorization": f"Bearer {self._token}",
            "LinkedIn-Version": LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    # ── Public API ────────────────────────────────────────────────────────────

    def publish(self, video_path: pathlib.Path, script: VideoScript) -> str:
        """
        Upload the video and create a LinkedIn post.
        Returns the URN of the created post (from x-restli-id header).
        """
        file_size = video_path.stat().st_size
        video_urn, upload_instructions, upload_token = self._initialize_upload(file_size)
        etags = self._upload_video(video_path, upload_instructions)
        self._finalize_upload(video_urn, upload_token, etags)
        self._wait_for_processing(video_urn)
        return self._create_post(video_urn, script)

    # ── Step 1: Initialize upload ─────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _initialize_upload(self, file_size: int) -> tuple[str, list[dict], str]:
        """
        POST /rest/videos?action=initializeUpload
        Returns (video_urn, upload_instructions, upload_token).
        upload_instructions is a list of {uploadUrl, firstByte, lastByte} dicts.
        """
        payload = {
            "initializeUploadRequest": {
                "owner": self._person_urn,
                "fileSizeBytes": file_size,
                "uploadCaptions": False,
                "uploadThumbnail": False,
            }
        }
        resp = requests.post(
            f"{LINKEDIN_REST}/videos?action=initializeUpload",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()["value"]
        video_urn: str = data["video"]
        upload_token: str = data.get("uploadToken", "")
        upload_instructions: list[dict] = data["uploadInstructions"]
        return video_urn, upload_instructions, upload_token

    # ── Step 2: Upload binary (single or multipart) ───────────────────────────

    def _upload_video(self, video_path: pathlib.Path, upload_instructions: list[dict]) -> list[str]:
        """
        PUT each chunk to its corresponding uploadUrl.
        Returns list of ETags in instruction order — required for finalization.
        Files ≤4MB → one chunk. Files >4MB → multiple 4MB chunks.
        """
        etags: list[str] = []
        with open(video_path, "rb") as f:
            for instruction in upload_instructions:
                url = instruction["uploadUrl"]
                first_byte = instruction["firstByte"]
                last_byte = instruction["lastByte"]
                chunk_size = last_byte - first_byte + 1

                f.seek(first_byte)
                chunk = f.read(chunk_size)
                etag = self._put_chunk(url, chunk)
                etags.append(etag)
        return etags

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
    def _put_chunk(self, upload_url: str, chunk: bytes) -> str:
        """PUT a single binary chunk. Returns the ETag response header."""
        resp = requests.put(
            upload_url,
            data=chunk,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/octet-stream",
            },
        )
        if resp.status_code not in (200, 201):
            resp.raise_for_status()
        return resp.headers.get("ETag", resp.headers.get("etag", ""))

    # ── Step 3: Finalize upload ───────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _finalize_upload(self, video_urn: str, upload_token: str, etags: list[str]) -> None:
        """
        POST /rest/videos?action=finalizeUpload
        Confirms all parts were uploaded successfully.
        etags must be in the same order as the original upload instructions.
        """
        payload = {
            "finalizeUploadRequest": {
                "video": video_urn,
                "uploadToken": upload_token,
                "uploadedPartIds": etags,
            }
        }
        resp = requests.post(
            f"{LINKEDIN_REST}/videos?action=finalizeUpload",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()

    # ── Step 3.5: Wait for processing ─────────────────────────────────────────

    def _wait_for_processing(self, video_urn: str, timeout_s: int = 120) -> None:
        """
        Poll GET /rest/videos/{urn} until status == "AVAILABLE".
        LinkedIn needs a moment after finalize before the video can be posted.
        """
        encoded_urn = requests.utils.quote(video_urn, safe="")
        url = f"{LINKEDIN_REST}/videos/{encoded_urn}"
        elapsed = 0
        while elapsed < timeout_s:
            resp = requests.get(url, headers=self._headers())
            if resp.status_code == 200:
                status = resp.json().get("status", "")
                if status == "AVAILABLE":
                    return
            time.sleep(5)
            elapsed += 5
        # Don't raise — attempt to post anyway; worst case LinkedIn returns an error
        # which the caller can surface.

    # ── Step 4: Create post ───────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _create_post(self, video_urn: str, script: VideoScript) -> str:
        """
        POST /rest/posts — creates the visible LinkedIn post.
        Returns the post URN from the x-restli-id response header.
        """
        payload = {
            "author": self._person_urn,
            "commentary": script.linkedin_post_text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "content": {
                "media": {
                    "title": script.topic,
                    "id": video_urn,
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        resp = requests.post(
            f"{LINKEDIN_REST}/posts",
            headers=self._headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id") or ""
