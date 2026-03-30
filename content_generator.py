"""
content_generator.py
────────────────────
Uses Claude to generate short-form video scripts in Varun Mayya's signature
style: punchy hook → insight-packed body → clear CTA, optimised for LinkedIn.
"""

import json
import re
from dataclasses import dataclass

import anthropic

from config import Config


# ── Data model ──────────────────────────────────────────────────────────────

@dataclass
class VideoScript:
    topic: str
    hook: str          # First 3–5 seconds – grabs attention
    body: str          # Main content (spoken by avatar, ≤ 90 s)
    cta: str           # Call-to-action line at the end
    caption: str       # Full LinkedIn post caption (text under the video)
    hashtags: list[str]

    @property
    def full_spoken_script(self) -> str:
        """Complete script fed to the avatar TTS engine."""
        return f"{self.hook}\n\n{self.body}\n\n{self.cta}"

    @property
    def linkedin_post_text(self) -> str:
        tags = " ".join(f"#{h.lstrip('#')}" for h in self.hashtags)
        return f"{self.caption}\n\n{tags}"


# ── Prompt templates ─────────────────────────────────────────────────────────

TOPIC_BRAINSTORM_PROMPT = """\
You are a viral LinkedIn creator who specialises in {niche}.
Your style: direct, insight-dense, slightly provocative – like Varun Mayya.

Generate {n} highly shareable short-video TOPICS for LinkedIn.
Each topic must:
- Be specific, not generic ("5 AI agents replacing entire teams" > "AI is changing work")
- Spark curiosity or mild controversy
- Be completable in a 60–90 second avatar video

Return ONLY a JSON array of strings, no extra text.
Example: ["Topic one", "Topic two"]
"""

SCRIPT_GENERATION_PROMPT = """\
You are a viral LinkedIn short-video scriptwriter. Style: Varun Mayya — rapid,
no-fluff, insight-packed, conversational. Creator persona: {creator_name}.

Topic: {topic}
Niche: {niche}

Write a complete video package. Return ONLY valid JSON matching this schema:
{{
  "hook": "<opening line that stops the scroll — 1-2 punchy sentences, max 15 words>",
  "body": "<spoken body — facts, examples, mini-story — reads naturally at ~140 wpm, targets 60-75 seconds>",
  "cta": "<single closing sentence — tell viewers to follow/comment/share>",
  "caption": "<LinkedIn caption: expand on the idea, add 2-3 bullet takeaways, conversational tone, 150-250 words>",
  "hashtags": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>"]
}}

Rules:
- body must be plain spoken prose (no markdown, no headers)
- hook must hook in the FIRST WORD (use "I", "You", a number, or a bold claim)
- caption ends with a question to drive comments
- hashtags: mix broad (#AI) and niche (#AIAutomation)
"""


# ── Generator class ───────────────────────────────────────────────────────────

class ContentGenerator:
    def __init__(self, cfg: Config):
        self._client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
        self._niche = cfg.content_niche
        self._creator = cfg.creator_name
        self._model = "claude-opus-4-6"

    # ── Public API ────────────────────────────────────────────────────────────

    def brainstorm_topics(self, n: int = 5) -> list[str]:
        """Return `n` trending topic ideas."""
        prompt = TOPIC_BRAINSTORM_PROMPT.format(niche=self._niche, n=n)
        raw = self._call(prompt)
        return self._parse_json(raw, expected_type=list)

    def generate_script(self, topic: str) -> VideoScript:
        """Generate a complete VideoScript for the given topic."""
        prompt = SCRIPT_GENERATION_PROMPT.format(
            topic=topic,
            niche=self._niche,
            creator_name=self._creator or "the creator",
        )
        raw = self._call(prompt)
        data = self._parse_json(raw, expected_type=dict)
        return VideoScript(
            topic=topic,
            hook=data["hook"],
            body=data["body"],
            cta=data["cta"],
            caption=data["caption"],
            hashtags=data.get("hashtags", []),
        )

    def pick_and_generate(self) -> VideoScript:
        """Convenience: brainstorm topics, pick the best one, generate script."""
        topics = self.brainstorm_topics(n=5)
        # Pick the first — Claude already ranks them by virality potential
        return self.generate_script(topics[0])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _call(self, user_prompt: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=1500,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    @staticmethod
    def _parse_json(text: str, expected_type: type):
        # Strip markdown fences if present
        text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
        data = json.loads(text)
        if not isinstance(data, expected_type):
            raise ValueError(f"Expected {expected_type.__name__}, got {type(data).__name__}")
        return data
