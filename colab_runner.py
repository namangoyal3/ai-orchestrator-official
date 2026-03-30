"""
colab_runner.py
───────────────
Self-contained single-file script for Google Colab (or any Python env).
No external project imports — everything is here.

── Colab setup cell (run this first) ─────────────────────────────────────────

    !pip install anthropic requests python-dotenv -q

    from google.colab import userdata
    import os
    os.environ["ANTHROPIC_API_KEY"]      = userdata.get("ANTHROPIC_API_KEY")
    os.environ["HEYGEN_API_KEY"]         = userdata.get("HEYGEN_API_KEY")
    os.environ["HEYGEN_TEMPLATE_ID"]     = userdata.get("HEYGEN_TEMPLATE_ID")
    os.environ["LINKEDIN_ACCESS_TOKEN"]  = userdata.get("LINKEDIN_ACCESS_TOKEN")
    os.environ["LINKEDIN_PERSON_URN"]    = userdata.get("LINKEDIN_PERSON_URN")

── Then paste + run this file ────────────────────────────────────────────────

HeyGen setup:
  1. Go to app.heygen.com → Templates → Create Template
  2. Add your avatar (record yourself or use an instant avatar)
  3. Add a Text variable named "script" in the template editor
  4. Save and copy the Template ID → HEYGEN_TEMPLATE_ID

LinkedIn setup:
  Run linkedin_auth.py from this repo once to get your token + person URN.
"""

from __future__ import annotations

import os
import time
import json
import requests

# ── Credentials (read from environment) ──────────────────────────────────────

ANTHROPIC_API_KEY     = os.getenv("ANTHROPIC_API_KEY")
HEYGEN_API_KEY        = os.getenv("HEYGEN_API_KEY")
HEYGEN_TEMPLATE_ID    = os.getenv("HEYGEN_TEMPLATE_ID")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN   = os.getenv("LINKEDIN_PERSON_URN")

# ── Content settings ──────────────────────────────────────────────────────────

CONTENT_NICHE  = os.getenv("CONTENT_NICHE", "AI tools, automation, and building with AI")
CREATOR_NAME   = os.getenv("CREATOR_NAME", "")
HEYGEN_BASE    = "https://api.heygen.com"

# =============================================================================
# STEP 1 — Generate script with Claude
# =============================================================================

def generate_script(topic: str | None = None) -> dict:
    """
    Uses Claude to brainstorm a viral topic (if none given) and write a
    complete script + LinkedIn caption in Varun Mayya style.

    Returns dict with: topic, hook, body, cta, caption, hashtags
    """
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Pick a topic if not provided
    if not topic:
        topic_resp = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a viral LinkedIn creator specialising in {CONTENT_NICHE}. "
                    "Give me ONE highly shareable short-video topic — specific, curiosity-sparking, "
                    "completable in 60-90 seconds. Reply with ONLY the topic string, nothing else."
                ),
            }],
        )
        topic = topic_resp.content[0].text.strip().strip('"')
        print(f"Topic selected: {topic}")

    # Generate full script
    script_resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""
You are a viral LinkedIn short-video scriptwriter. Style: Varun Mayya — rapid,
no-fluff, insight-packed, conversational. Creator persona: {CREATOR_NAME or "the creator"}.

Topic: {topic}
Niche: {CONTENT_NICHE}

Return ONLY valid JSON:
{{
  "hook": "<1-2 punchy opening sentences, max 15 words, stops the scroll>",
  "body": "<spoken body — reads naturally at ~140 wpm, targets 60-75 seconds, no markdown>",
  "cta": "<single closing sentence — follow/comment/share>",
  "caption": "<LinkedIn caption, 150-250 words, 2-3 bullet takeaways, ends with a question>",
  "hashtags": ["tag1","tag2","tag3","tag4","tag5"]
}}
""",
        }],
    )

    import re
    raw = script_resp.content[0].text
    raw = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    data = json.loads(raw)
    data["topic"] = topic
    data["full_script"] = f"{data['hook']}\n\n{data['body']}\n\n{data['cta']}"
    tags = " ".join(f"#{h.lstrip('#')}" for h in data.get("hashtags", []))
    data["linkedin_post_text"] = f"{data['caption']}\n\n{tags}"
    return data


# =============================================================================
# STEP 2 — Render avatar video with HeyGen Template API
# =============================================================================

def generate_heygen_video(script_text: str, topic: str, output_path: str = "avatar_video.mp4") -> str:
    """
    Submits script_text to your HeyGen template, polls until done, downloads MP4.

    Your template must have a text variable named "script".
    If you named it differently, change the key below.
    """
    headers = {
        "Accept": "application/json",
        "X-API-KEY": HEYGEN_API_KEY,
        "Content-Type": "application/json",
    }

    # Submit generation job
    payload = {
        "caption": False,
        "title": topic,
        "variables": {
            "script": {
                "name": "script",
                "type": "text",
                "properties": {"content": script_text},
            }
        },
    }

    resp = requests.post(
        f"{HEYGEN_BASE}/v2/template/{HEYGEN_TEMPLATE_ID}/generate",
        headers=headers,
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("error"):
        raise RuntimeError(f"HeyGen error: {data['error']}")

    video_id = data["data"]["video_id"]
    print(f"HeyGen video_id: {video_id} — polling status…")

    # Poll until complete
    status_url = f"{HEYGEN_BASE}/v1/video_status.get?video_id={video_id}"
    for _ in range(120):   # max 10 min at 5s intervals
        sr = requests.get(status_url, headers={"Accept": "application/json", "X-API-KEY": HEYGEN_API_KEY})
        sr.raise_for_status()
        sdata = sr.json()["data"]
        status = sdata["status"]
        print(f"  status: {status}")

        if status == "completed":
            video_url = sdata["video_url"]
            print(f"Downloading from: {video_url}")
            content = requests.get(video_url).content
            with open(output_path, "wb") as f:
                f.write(content)
            print(f"Saved to: {output_path}  ({len(content)//1024} KB)")
            return output_path

        if status not in ("processing", "pending", "waiting"):
            raise RuntimeError(f"HeyGen generation failed: {sdata.get('error')}")

        time.sleep(5)

    raise TimeoutError("HeyGen did not complete within 10 minutes.")


# =============================================================================
# STEP 3 — Upload to LinkedIn and post
#
# ⚠️  Uses current (non-deprecated) LinkedIn APIs:
#       Videos API  /rest/videos  (replaces /rest/assets + /v2/assets)
#       Posts API   /rest/posts   (replaces /v2/ugcPosts)
#     LinkedIn-Version header is mandatory as of 2025.
# =============================================================================

LINKEDIN_REST = "https://api.linkedin.com/rest"
LINKEDIN_VERSION = "202601"


def _li_headers(extra: dict | None = None) -> dict:
    h = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "LinkedIn-Version": LINKEDIN_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def linkedin_initialize_upload(file_size: int) -> tuple[str, list[dict], str]:
    """
    POST /rest/videos?action=initializeUpload
    Returns (video_urn, upload_instructions, upload_token).
    upload_instructions: list of {uploadUrl, firstByte, lastByte}
    Files ≤4MB → 1 instruction. Files >4MB → multiple 4MB chunks.
    """
    body = {
        "initializeUploadRequest": {
            "owner": LINKEDIN_PERSON_URN,
            "fileSizeBytes": file_size,
            "uploadCaptions": False,
            "uploadThumbnail": False,
        }
    }
    resp = requests.post(
        f"{LINKEDIN_REST}/videos?action=initializeUpload",
        headers=_li_headers(),
        json=body,
    )
    resp.raise_for_status()
    data = resp.json()["value"]
    return data["video"], data["uploadInstructions"], data.get("uploadToken", "")


def linkedin_upload_binary(video_path: str, upload_instructions: list[dict]) -> list[str]:
    """
    PUT each chunk to its uploadUrl. Returns ETags in instruction order.
    ETags are required for finalization.
    """
    etags = []
    with open(video_path, "rb") as f:
        for instr in upload_instructions:
            first, last = instr["firstByte"], instr["lastByte"]
            f.seek(first)
            chunk = f.read(last - first + 1)
            resp = requests.put(
                instr["uploadUrl"],
                data=chunk,
                headers={
                    "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                    "Content-Type": "application/octet-stream",
                },
            )
            if resp.status_code not in (200, 201):
                resp.raise_for_status()
            etags.append(resp.headers.get("ETag") or resp.headers.get("etag") or "")
    return etags


def linkedin_finalize_upload(video_urn: str, upload_token: str, etags: list[str]) -> None:
    """POST /rest/videos?action=finalizeUpload to confirm all parts."""
    body = {
        "finalizeUploadRequest": {
            "video": video_urn,
            "uploadToken": upload_token,
            "uploadedPartIds": etags,
        }
    }
    resp = requests.post(
        f"{LINKEDIN_REST}/videos?action=finalizeUpload",
        headers=_li_headers(),
        json=body,
    )
    resp.raise_for_status()


def linkedin_wait_for_processing(video_urn: str, timeout_s: int = 120) -> None:
    """Poll GET /rest/videos/{urn} until status == AVAILABLE."""
    encoded = requests.utils.quote(video_urn, safe="")
    for _ in range(timeout_s // 5):
        resp = requests.get(f"{LINKEDIN_REST}/videos/{encoded}", headers=_li_headers())
        if resp.status_code == 200 and resp.json().get("status") == "AVAILABLE":
            return
        time.sleep(5)


def linkedin_create_post(video_urn: str, topic: str, post_text: str) -> str:
    """POST /rest/posts — creates the visible LinkedIn post. Returns post URN."""
    body = {
        "author": LINKEDIN_PERSON_URN,
        "commentary": post_text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {
            "media": {
                "title": topic,
                "id": video_urn,
            }
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    resp = requests.post(
        f"{LINKEDIN_REST}/posts",
        headers=_li_headers(),
        json=body,
    )
    resp.raise_for_status()
    return resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id") or "UNKNOWN"


# =============================================================================
# ORCHESTRATOR — run the full pipeline
# =============================================================================

def run(
    topic: str | None = None,
    use_heygen: bool = True,
    existing_video_path: str | None = None,
) -> str:
    """
    Full pipeline: script → avatar video → LinkedIn post.

    Args:
        topic:               Optional explicit topic. If None, Claude picks one.
        use_heygen:          True  = generate video via HeyGen template.
                             False = use existing_video_path (skip HeyGen).
        existing_video_path: Path to an already-rendered MP4 (use_heygen=False).

    Returns:
        LinkedIn post URN.
    """
    # 1. Script
    print("\n── Step 1: Generating script ─────────────────────")
    script = generate_script(topic)
    print(f"Hook: {script['hook']}")

    # 2. Video
    print("\n── Step 2: Rendering avatar video ────────────────")
    if use_heygen:
        video_path = generate_heygen_video(script["full_script"], script["topic"])
    else:
        if not existing_video_path:
            raise ValueError("Pass existing_video_path when use_heygen=False.")
        video_path = existing_video_path
        print(f"Using existing video: {video_path}")

    # 3. LinkedIn
    print("\n── Step 3: Publishing to LinkedIn ────────────────")
    file_size = os.path.getsize(video_path)

    # 3a. Initialize — get video URN + upload URLs
    video_urn, upload_instructions, upload_token = linkedin_initialize_upload(file_size)
    print(f"Video URN: {video_urn}  ({len(upload_instructions)} chunk(s))")

    # 3b. Upload binary (chunked for >4MB)
    etags = linkedin_upload_binary(video_path, upload_instructions)
    print("Binary uploaded.")

    # 3c. Finalize
    linkedin_finalize_upload(video_urn, upload_token, etags)
    print("Upload finalized.")

    # 3d. Wait for LinkedIn to process the video
    linkedin_wait_for_processing(video_urn)
    print("Video processed (AVAILABLE).")

    # 3e. Create the post
    post_urn = linkedin_create_post(video_urn, script["topic"], script["linkedin_post_text"])
    print(f"\nPosted! URN: {post_urn}")
    return post_urn


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # ── Option A: Full end-to-end (Claude picks topic, HeyGen renders it) ──
    run(use_heygen=True)

    # ── Option B: Specific topic ────────────────────────────────────────────
    # run(topic="3 AI agents that replaced my entire ops team", use_heygen=True)

    # ── Option C: Skip HeyGen, post a video you already have ───────────────
    # run(use_heygen=False, existing_video_path="my_clip.mp4")
