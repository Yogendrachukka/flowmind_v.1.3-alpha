import pytest
from unittest.mock import patch

from flowmind.router import route

@pytest.mark.asyncio
async def test_route_extra_fields():
    with patch("flowmind.router.call_with_failover") as mock_failover:
        mock_failover.return_value = {"ok": True}

        await route("default", [], 0.7, 100, extra_fields={"tools": [{"type": "function"}], "top_p": 0.9})

        assert mock_failover.call_count == 1
        payload = mock_failover.call_args[0][0]
        assert payload["tools"] == [{"type": "function"}]
        assert payload["top_p"] == 0.9
        assert payload["model"] == "default"
        assert payload["temperature"] == 0.7
