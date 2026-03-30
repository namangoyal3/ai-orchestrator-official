"""
Tests for config.py and pipeline.py.
- Config: validates _require, from_env, defaults
- Pipeline: verifies orchestration (all 3 steps called, result dict structure)
"""

import os
import pathlib
import pytest
from unittest.mock import MagicMock, patch

from config import Config, _require


# ═════════════════════════════════════════════════════════════════════════════
# Config
# ═════════════════════════════════════════════════════════════════════════════

class TestRequire:
    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY_XYZ", "hello")
        assert _require("TEST_KEY_XYZ") == "hello"

    def test_raises_environment_error_when_missing(self, monkeypatch):
        monkeypatch.delenv("MISSING_KEY_XYZ", raising=False)
        with pytest.raises(EnvironmentError, match="MISSING_KEY_XYZ"):
            _require("MISSING_KEY_XYZ")

    def test_raises_when_empty_string(self, monkeypatch):
        monkeypatch.setenv("EMPTY_KEY_XYZ", "")
        with pytest.raises(EnvironmentError):
            _require("EMPTY_KEY_XYZ")


class TestConfigFromEnv:
    _REQUIRED = {
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "HEYGEN_API_KEY": "hg-test",
        "HEYGEN_TEMPLATE_ID": "tmpl-test",
        "LINKEDIN_CLIENT_ID": "li-client",
        "LINKEDIN_CLIENT_SECRET": "li-secret",
        "LINKEDIN_ACCESS_TOKEN": "li-token",
        "LINKEDIN_PERSON_URN": "urn:li:person:test",
    }

    def _set_env(self, monkeypatch, overrides=None):
        env = {**self._REQUIRED}
        if overrides:
            env.update(overrides)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        # Clear optional vars so defaults kick in
        for k in ["POST_TIME_UTC", "VIDEOS_PER_RUN", "CONTENT_NICHE", "CREATOR_NAME"]:
            monkeypatch.delenv(k, raising=False)

    def test_loads_all_required_fields(self, monkeypatch):
        self._set_env(monkeypatch)
        cfg = Config.from_env()
        assert cfg.anthropic_api_key == "sk-ant-test"
        assert cfg.heygen_api_key == "hg-test"
        assert cfg.heygen_template_id == "tmpl-test"
        assert cfg.linkedin_access_token == "li-token"
        assert cfg.linkedin_person_urn == "urn:li:person:test"

    def test_post_time_defaults_to_0900(self, monkeypatch):
        self._set_env(monkeypatch)
        cfg = Config.from_env()
        assert cfg.post_time_utc == "09:00"

    def test_videos_per_run_defaults_to_1(self, monkeypatch):
        self._set_env(monkeypatch)
        cfg = Config.from_env()
        assert cfg.videos_per_run == 1

    def test_content_niche_default(self, monkeypatch):
        self._set_env(monkeypatch)
        cfg = Config.from_env()
        assert "AI" in cfg.content_niche

    def test_custom_post_time(self, monkeypatch):
        self._set_env(monkeypatch, {"POST_TIME_UTC": "14:30"})
        monkeypatch.setenv("POST_TIME_UTC", "14:30")
        cfg = Config.from_env()
        assert cfg.post_time_utc == "14:30"

    def test_custom_videos_per_run(self, monkeypatch):
        self._set_env(monkeypatch)
        monkeypatch.setenv("VIDEOS_PER_RUN", "3")
        cfg = Config.from_env()
        assert cfg.videos_per_run == 3

    def test_raises_when_required_key_missing(self, monkeypatch):
        self._set_env(monkeypatch)
        monkeypatch.delenv("ANTHROPIC_API_KEY")
        with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
            Config.from_env()

    def test_config_is_immutable(self, monkeypatch):
        self._set_env(monkeypatch)
        cfg = Config.from_env()
        with pytest.raises((AttributeError, TypeError)):
            cfg.anthropic_api_key = "new-value"  # type: ignore[misc]


# ═════════════════════════════════════════════════════════════════════════════
# Pipeline
# ═════════════════════════════════════════════════════════════════════════════

def _make_cfg():
    cfg = MagicMock(spec=Config)
    cfg.anthropic_api_key = "sk-test"
    cfg.heygen_api_key = "hg-test"
    cfg.heygen_template_id = "tmpl-test"
    cfg.linkedin_access_token = "li-token"
    cfg.linkedin_person_urn = "urn:li:person:test"
    cfg.content_niche = "AI tools"
    cfg.creator_name = "Test"
    return cfg


def _make_script():
    script = MagicMock()
    script.topic = "Pipeline Test Topic"
    script.hook = "Hook line."
    script.cta = "CTA line."
    script.linkedin_post_text = "Caption #AI"
    return script


class TestRunPipeline:
    def test_returns_dict_with_required_keys(self, tmp_path):
        from pipeline import run_pipeline

        cfg = _make_cfg()
        script = _make_script()
        fake_video = tmp_path / "test_video.mp4"
        fake_video.write_bytes(b"x" * 100)

        with patch("pipeline.ContentGenerator") as MockGen, \
             patch("pipeline.AvatarVideoGenerator") as MockAvatar, \
             patch("pipeline.LinkedInPublisher") as MockLI, \
             patch("pipeline.tempfile.TemporaryDirectory") as MockTmp:

            MockGen.return_value.pick_and_generate.return_value = script
            MockAvatar.return_value.generate.return_value = fake_video
            MockLI.return_value.publish.return_value = "urn:li:share:42"
            MockTmp.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            MockTmp.return_value.__exit__ = MagicMock(return_value=False)

            result = run_pipeline(cfg)

        assert "topic" in result
        assert "post_urn" in result
        assert "video_path" in result

    def test_uses_provided_topic(self, tmp_path):
        from pipeline import run_pipeline

        cfg = _make_cfg()
        script = _make_script()
        fake_video = tmp_path / "test_video.mp4"
        fake_video.write_bytes(b"x" * 100)

        with patch("pipeline.ContentGenerator") as MockGen, \
             patch("pipeline.AvatarVideoGenerator") as MockAvatar, \
             patch("pipeline.LinkedInPublisher") as MockLI, \
             patch("pipeline.tempfile.TemporaryDirectory") as MockTmp:

            MockGen.return_value.generate_script.return_value = script
            MockAvatar.return_value.generate.return_value = fake_video
            MockLI.return_value.publish.return_value = "urn:li:share:99"
            MockTmp.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            MockTmp.return_value.__exit__ = MagicMock(return_value=False)

            run_pipeline(cfg, topic="My explicit topic")

            # Should call generate_script, NOT pick_and_generate
            MockGen.return_value.generate_script.assert_called_once_with("My explicit topic")
            MockGen.return_value.pick_and_generate.assert_not_called()

    def test_auto_picks_topic_when_none_given(self, tmp_path):
        from pipeline import run_pipeline

        cfg = _make_cfg()
        script = _make_script()
        fake_video = tmp_path / "test_video.mp4"
        fake_video.write_bytes(b"x" * 100)

        with patch("pipeline.ContentGenerator") as MockGen, \
             patch("pipeline.AvatarVideoGenerator") as MockAvatar, \
             patch("pipeline.LinkedInPublisher") as MockLI, \
             patch("pipeline.tempfile.TemporaryDirectory") as MockTmp:

            MockGen.return_value.pick_and_generate.return_value = script
            MockAvatar.return_value.generate.return_value = fake_video
            MockLI.return_value.publish.return_value = "urn:li:share:1"
            MockTmp.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            MockTmp.return_value.__exit__ = MagicMock(return_value=False)

            run_pipeline(cfg, topic=None)

            MockGen.return_value.pick_and_generate.assert_called_once()
            MockGen.return_value.generate_script.assert_not_called()

    def test_post_urn_in_result(self, tmp_path):
        from pipeline import run_pipeline

        cfg = _make_cfg()
        script = _make_script()
        fake_video = tmp_path / "test_video.mp4"
        fake_video.write_bytes(b"x" * 100)

        with patch("pipeline.ContentGenerator") as MockGen, \
             patch("pipeline.AvatarVideoGenerator") as MockAvatar, \
             patch("pipeline.LinkedInPublisher") as MockLI, \
             patch("pipeline.tempfile.TemporaryDirectory") as MockTmp:

            MockGen.return_value.pick_and_generate.return_value = script
            MockAvatar.return_value.generate.return_value = fake_video
            MockLI.return_value.publish.return_value = "urn:li:share:FINAL"
            MockTmp.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            MockTmp.return_value.__exit__ = MagicMock(return_value=False)

            result = run_pipeline(cfg)

        assert result["post_urn"] == "urn:li:share:FINAL"
        assert result["topic"] == script.topic
