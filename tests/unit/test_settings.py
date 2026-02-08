"""Test configuration management."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from tiktok_comment_scraper.config.settings import Settings, settings


class TestSettings:
    """Test Settings class."""

    def test_load_default_values(self):
        """Test that settings load with default values."""
        test_env = {
            "ZAI_API_KEY": "test_api_key",
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
        
        try:
            s = Settings()
            assert s.ZAI_API_KEY == "test_api_key"
            assert s.ZAI_MODEL == "glm-4.7"
            assert s.ZAI_TIMEOUT == 300
            assert s.TIKTOK_TIMEOUT == 30
            assert s.BATCH_SIZE == 50
        finally:
            for key in test_env:
                os.environ.pop(key, None)

    def test_required_api_key(self):
        """Test that ZAI_API_KEY is required."""
        with pytest.raises(ValidationError) as exc_info:
            Settings()
        assert "ZAI_API_KEY" in str(exc_info.value)

    def test_custom_values(self):
        """Test that custom values can be set."""
        test_env = {
            "ZAI_API_KEY": "custom_key",
            "ZAI_MODEL": "glm-4.6",
            "ZAI_TIMEOUT": "600",
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
        
        try:
            s = Settings()
            assert s.ZAI_API_KEY == "custom_key"
            assert s.ZAI_MODEL == "glm-4.6"
            assert s.ZAI_TIMEOUT == 600
        finally:
            for key in test_env:
                os.environ.pop(key, None)

    def test_singleton_instance(self):
        """Test that settings is a singleton instance."""
        test_env = {"ZAI_API_KEY": "singleton_test"}
        for key, value in test_env.items():
            os.environ[key] = value
        
        try:
            s1 = settings
            s2 = settings
            assert s1 is s2
        finally:
            for key in test_env:
                os.environ.pop(key, None)

    @pytest.mark.integration
    def test_load_from_env_file(self, tmp_path: Path):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "ZAI_API_KEY=env_file_key\n"
            "ZAI_MODEL=custom_model\n"
            "BATCH_SIZE=100\n"
        )
        
        os.environ["ZAI_API_KEY"] = "env_file_key"
        try:
            s = Settings(_env_file=str(env_file))
            assert s.ZAI_API_KEY == "env_file_key"
            assert s.ZAI_MODEL == "custom_model"
            assert s.BATCH_SIZE == 100
        finally:
            os.environ.pop("ZAI_API_KEY", None)
