from unittest.mock import MagicMock, patch

import pytest

from core.clickhouse.client import ClickHouseClient


@pytest.mark.repository
class TestClickHouseClient:
    def test_query_parses_jsoneachrow_response(self):
        # Arrange
        fake_response = MagicMock(text='{"idcondado":1,"ratio":2.5}\n')
        fake_response.raise_for_status = MagicMock()
        client = ClickHouseClient()

        # Act
        with patch("core.clickhouse.client.requests.post", return_value=fake_response) as post:
            result = client.query("SELECT idcondado, ratio FROM t")

        # Assert
        assert result == [{"idcondado": 1, "ratio": 2.5}]
        sent_body = post.call_args.kwargs["data"].decode("utf-8")
        assert sent_body == "SELECT idcondado, ratio FROM t FORMAT JSONEachRow"

    def test_query_returns_empty_list_for_empty_response(self):
        fake_response = MagicMock(text="")
        fake_response.raise_for_status = MagicMock()
        client = ClickHouseClient()

        with patch("core.clickhouse.client.requests.post", return_value=fake_response):
            assert client.query("SELECT 1 WHERE 1=0") == []
