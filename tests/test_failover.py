import pytest
import asyncio
from unittest.mock import patch, MagicMock

import flowmind.config as cfg
from flowmind.failover import call_with_failover, AllProvidersExhausted, _RetryableError
from flowmind import health_cache

@pytest.fixture
def mock_config():
    with patch("flowmind.failover.cfg") as mock_cfg:
        mock_cfg.get_provider_priority.return_value = ["gemini", "openrouter"]
        mock_cfg.get_keys.side_effect = lambda p: ["gemini-key"] if p == "gemini" else ["openrouter-key"]
        mock_cfg.get_best_model.side_effect = lambda p: "gemini-model" if p == "gemini" else "or-model"
        yield mock_cfg

@pytest.fixture
def mock_health_cache():
    with patch("flowmind.failover.health_cache") as mock_hc:
        mock_hc.is_available.return_value = True
        yield mock_hc

@pytest.fixture
def mock_attempt():
    with patch("flowmind.failover._attempt") as mock_att:
        yield mock_att

@pytest.mark.asyncio
async def test_failover_success_first_try(mock_config, mock_health_cache, mock_attempt):
    payload = {"model": "default", "messages": []}
    mock_attempt.return_value = {"choices": [{"message": {"content": "ok"}}]}

    result = await call_with_failover(payload)

    assert mock_attempt.call_count == 1
    args = mock_attempt.call_args[0]
    assert args[0].PROVIDER_NAME == "gemini"
    assert args[2]["model"] == "gemini-model"
    assert result["_flowmind"]["provider"] == "gemini"

@pytest.mark.asyncio
async def test_failover_to_second_provider(mock_config, mock_health_cache, mock_attempt):
    payload = {"model": "default", "messages": []}

    def attempt_side_effect(mod, api_key, payload_arg):
        if mod.PROVIDER_NAME == "gemini":
            raise _RetryableError("mock failure")
        return {"choices": [{"message": {"content": "ok"}}]}

    mock_attempt.side_effect = attempt_side_effect

    result = await call_with_failover(payload)

    assert mock_attempt.call_count == 2
    args = mock_attempt.call_args_list
    assert args[0][0][0].PROVIDER_NAME == "gemini"
    assert args[1][0][0].PROVIDER_NAME == "openrouter"
    assert args[1][0][2]["model"] == "or-model"
    assert result["_flowmind"]["provider"] == "openrouter"

@pytest.mark.asyncio
async def test_failover_exhausted(mock_config, mock_health_cache, mock_attempt):
    payload = {"model": "default", "messages": []}
    mock_attempt.side_effect = _RetryableError("mock failure")

    with pytest.raises(AllProvidersExhausted):
        await call_with_failover(payload)

    assert mock_attempt.call_count == 2
    assert mock_health_cache.mark_failed.call_count == 2
