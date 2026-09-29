import pytest
import asyncio
from unittest.mock import patch

from flowmind.failover import call_with_failover
from flowmind.router import route
import flowmind.config as cfg
import flowmind.providers.gemini as gemini

@pytest.fixture
def setup_mock_config():
    original_get_keys = cfg.get_keys
    original_get_provider_priority = cfg.get_provider_priority
    cfg.get_keys = lambda p: ["fake-key"]
    cfg.get_provider_priority = lambda: ["gemini"]
    yield
    cfg.get_keys = original_get_keys
    cfg.get_provider_priority = original_get_provider_priority

@pytest.mark.asyncio
async def test_extra_parameters_forwarded_to_failover_and_attempt(setup_mock_config):
    with patch("flowmind.failover._attempt") as mock_attempt:
        mock_attempt.return_value = {"choices": [{"message": {"content": "ok"}}]}

        await route("default", [{"role": "user", "content": "hello"}], 0.7, 100, {"top_p": 0.9, "tools": []})

        assert mock_attempt.call_count == 1
        args, kwargs = mock_attempt.call_args
        payload = args[2]

        assert payload["top_p"] == 0.9
        assert payload["tools"] == []
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 100
        assert payload["model"] == gemini.DEFAULT_MODEL
