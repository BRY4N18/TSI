import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.clickhouse_http_client import execute_clickhouse, insert_rows, query_clickhouse  # noqa: E402


def test_query_clickhouse_appends_format_jsoneachrow_and_parses_lines():
    # Arrange
    fake_response = MagicMock(status_code=200, text='{"a":1}\n{"a":2}\n')
    with patch("lib.clickhouse_http_client.requests.post", return_value=fake_response) as post:
        # Act
        result = query_clickhouse("SELECT a FROM t")

        # Assert
        assert result == [{"a": 1}, {"a": 2}]
        sent_body = post.call_args.kwargs["data"].decode("utf-8")
        assert sent_body == "SELECT a FROM t FORMAT JSONEachRow"


def test_query_clickhouse_returns_empty_list_for_empty_response():
    fake_response = MagicMock(status_code=200, text="")
    with patch("lib.clickhouse_http_client.requests.post", return_value=fake_response):
        assert query_clickhouse("SELECT a FROM t WHERE 1=0") == []


def test_execute_clickhouse_raises_on_non_200():
    fake_response = MagicMock(status_code=400, text="DB::Exception: boom")
    with patch("lib.clickhouse_http_client.requests.post", return_value=fake_response):
        try:
            execute_clickhouse("CREATE TABLE broken")
            assert False, "esperaba RuntimeError"
        except RuntimeError as exc:
            assert "boom" in str(exc)


def test_insert_rows_sends_jsoneachrow_payload():
    fake_response = MagicMock(status_code=200, text="")
    with patch("lib.clickhouse_http_client.requests.post", return_value=fake_response) as post:
        insert_rows("t", [{"a": 1}, {"a": 2}])

        sent_body = post.call_args.kwargs["data"].decode("utf-8")
        assert sent_body == 'INSERT INTO t FORMAT JSONEachRow\n{"a": 1}\n{"a": 2}'


def test_insert_rows_noop_when_no_rows():
    with patch("lib.clickhouse_http_client.requests.post") as post:
        insert_rows("t", [])
        post.assert_not_called()
