"""Tests for content_generator.py — mocks Anthropic client entirely."""

import json
import pytest
from unittest.mock import MagicMock, patch

from content_generator import ContentGenerator, VideoScript, TOPIC_BRAINSTORM_PROMPT, SCRIPT_GENERATION_PROMPT


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_cfg(niche="AI tools", creator="Test Creator"):
    cfg = MagicMock()
    cfg.anthropic_api_key = "sk-test"
    cfg.content_niche = niche
    cfg.creator_name = creator
    return cfg


VALID_TOPICS = ["Topic A", "Topic B", "Topic C"]

VALID_SCRIPT_DATA = {
    "hook": "AI just replaced your entire ops team.",
    "body": "Here is the body text with details.",
    "cta": "Follow for more daily AI insights.",
    "caption": "A detailed caption with takeaways.\n\n- Point 1\n- Point 2\nWhat do you think?",
    "hashtags": ["AI", "Automation", "LinkedIn", "Tech", "Founders"],
}


def _mock_client(response_text: str):
    """Return a mock Anthropic client whose messages.create returns response_text."""
    client = MagicMock()
    msg = MagicMock()
    msg.content = [MagicMock(text=response_text)]
    client.messages.create.return_value = msg
    return client


# ── VideoScript dataclass ─────────────────────────────────────────────────────

class TestVideoScript:
    def _make(self, **kwargs):
        defaults = dict(
            topic="Test topic",
            hook="Hook line.",
            body="Body text.",
            cta="CTA line.",
            caption="Caption text.",
            hashtags=["AI", "Tech"],
        )
        defaults.update(kwargs)
        return VideoScript(**defaults)

    def test_full_spoken_script_joins_hook_body_cta(self):
        s = self._make()
        assert s.full_spoken_script == "Hook line.\n\nBody text.\n\nCTA line."

    def test_linkedin_post_text_appends_hashtags(self):
        s = self._make(caption="Caption.", hashtags=["AI", "#Tech"])
        text = s.linkedin_post_text
        assert "Caption." in text
        assert "#AI" in text
        assert "#Tech" in text   # strips leading # before re-adding

    def test_linkedin_post_text_empty_hashtags(self):
        s = self._make(hashtags=[])
        assert s.linkedin_post_text == "Caption text.\n\n"


# ── ContentGenerator._parse_json ─────────────────────────────────────────────

class TestParseJson:
    def test_parses_plain_json_list(self):
        result = ContentGenerator._parse_json('["a", "b"]', list)
        assert result == ["a", "b"]

    def test_parses_plain_json_dict(self):
        result = ContentGenerator._parse_json('{"key": "value"}', dict)
        assert result == {"key": "value"}

    def test_strips_markdown_fences(self):
        raw = "```json\n[\"a\"]\n```"
        result = ContentGenerator._parse_json(raw, list)
        assert result == ["a"]

    def test_strips_plain_fences(self):
        raw = "```\n{\"k\": 1}\n```"
        result = ContentGenerator._parse_json(raw, dict)
        assert result == {"k": 1}

    def test_raises_on_wrong_type(self):
        with pytest.raises(ValueError, match="Expected list"):
            ContentGenerator._parse_json('{"key": "val"}', list)

    def test_raises_on_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            ContentGenerator._parse_json("not json", list)


# ── ContentGenerator.brainstorm_topics ───────────────────────────────────────

class TestBrainstormTopics:
    def test_returns_list_of_strings(self):
        cfg = _make_cfg()
        gen = ContentGenerator(cfg)
        gen._client = _mock_client(json.dumps(VALID_TOPICS))
        topics = gen.brainstorm_topics(n=3)
        assert topics == VALID_TOPICS

    def test_calls_api_once(self):
        cfg = _make_cfg()
        gen = ContentGenerator(cfg)
        gen._client = _mock_client(json.dumps(VALID_TOPICS))
        gen.brainstorm_topics(n=3)
        gen._client.messages.create.assert_called_once()

    def test_prompt_includes_niche_and_count(self):
        cfg = _make_cfg(niche="fintech automation")
        gen = ContentGenerator(cfg)
        gen._client = _mock_client(json.dumps(["T1"]))
        gen.brainstorm_topics(n=7)
        call_kwargs = gen._client.messages.create.call_args
        prompt = call_kwargs[1]["messages"][0]["content"]
        assert "fintech automation" in prompt
        assert "7" in prompt


# ── ContentGenerator.generate_script ─────────────────────────────────────────

class TestGenerateScript:
    def test_returns_videoscript(self):
        cfg = _make_cfg()
        gen = ContentGenerator(cfg)
        gen._client = _mock_client(json.dumps(VALID_SCRIPT_DATA))
        script = gen.generate_script("Some topic")
        assert isinstance(script, VideoScript)
        assert script.topic == "Some topic"
        assert script.hook == VALID_SCRIPT_DATA["hook"]
        assert script.hashtags == VALID_SCRIPT_DATA["hashtags"]

    def test_prompt_contains_topic_and_niche(self):
        cfg = _make_cfg(niche="biotech AI")
        gen = ContentGenerator(cfg)
        gen._client = _mock_client(json.dumps(VALID_SCRIPT_DATA))
        gen.generate_script("CRISPR AI")
        prompt = gen._client.messages.create.call_args[1]["messages"][0]["content"]
        assert "CRISPR AI" in prompt
        assert "biotech AI" in prompt

    def test_missing_hashtags_defaults_to_empty_list(self):
        cfg = _make_cfg()
        gen = ContentGenerator(cfg)
        data = {**VALID_SCRIPT_DATA}
        del data["hashtags"]
        gen._client = _mock_client(json.dumps(data))
        script = gen.generate_script("topic")
        assert script.hashtags == []

    def test_creator_name_in_prompt(self):
        cfg = _make_cfg(creator="Jane Doe")
        gen = ContentGenerator(cfg)
        gen._client = _mock_client(json.dumps(VALID_SCRIPT_DATA))
        gen.generate_script("topic")
        prompt = gen._client.messages.create.call_args[1]["messages"][0]["content"]
        assert "Jane Doe" in prompt

    def test_empty_creator_uses_fallback(self):
        cfg = _make_cfg(creator="")
        gen = ContentGenerator(cfg)
        gen._client = _mock_client(json.dumps(VALID_SCRIPT_DATA))
        gen.generate_script("topic")
        prompt = gen._client.messages.create.call_args[1]["messages"][0]["content"]
        assert "the creator" in prompt


# ── ContentGenerator.pick_and_generate ───────────────────────────────────────

class TestPickAndGenerate:
    def test_uses_first_brainstormed_topic(self):
        cfg = _make_cfg()
        gen = ContentGenerator(cfg)

        topics_resp = MagicMock(content=[MagicMock(text=json.dumps(["Best Topic", "Other"]))])
        script_resp = MagicMock(content=[MagicMock(text=json.dumps(VALID_SCRIPT_DATA))])
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [topics_resp, script_resp]
        gen._client = mock_client

        script = gen.pick_and_generate()
        assert script.topic == "Best Topic"

    def test_calls_api_twice(self):
        cfg = _make_cfg()
        gen = ContentGenerator(cfg)

        topics_resp = MagicMock(content=[MagicMock(text=json.dumps(["T1"]))])
        script_resp = MagicMock(content=[MagicMock(text=json.dumps(VALID_SCRIPT_DATA))])
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [topics_resp, script_resp]
        gen._client = mock_client

        gen.pick_and_generate()
        assert mock_client.messages.create.call_count == 2
