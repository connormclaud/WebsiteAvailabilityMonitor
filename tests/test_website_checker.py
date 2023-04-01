import aiohttp
from website_checker import check_website, main
import pytest
from unittest.mock import patch, ANY


@pytest.mark.asyncio
async def test_check_website_success():
    async with aiohttp.ClientSession() as session:
        result = await check_website(session, "http://httpbin/get")

        assert result["url"] == "http://httpbin/get"
        assert 0 <= result["response_time"] <= 5
        assert result["status_code"] == 200
        assert result["content_check"] is None


@pytest.mark.asyncio
async def test_check_website_failure():
    async with aiohttp.ClientSession() as session:
        result = await check_website(session, "http://httpbin/status/404")

        assert result["url"] == "http://httpbin/status/404"
        assert 0 <= result["response_time"] <= 5
        assert result["status_code"] == 404
        assert result["content_check"] is None


@pytest.mark.asyncio
async def test_check_website_content_match():
    async with aiohttp.ClientSession() as session:
        pattern = r"Herman Melville"
        result = await check_website(session, "http://httpbin/html", regexp=pattern)

        assert result["url"] == "http://httpbin/html"
        assert result["content_check"]


@pytest.mark.asyncio
async def test_check_website_exception_handling():
    async with aiohttp.ClientSession() as session:
        with patch('aiohttp.ClientSession.get', side_effect=Exception("Test exception")):
            result = await check_website(session, "http://httpbin/get")
            assert result is None


@pytest.mark.asyncio
async def test_main_function():
    config = {
        "websites": [{"url": "https://example.com"}],
        "producer_interval": 60,
        "timeout": 10,
        "kafka": {
            "bootstrap_servers": "localhost:29092",
            "topic": "website_metrics",
            "security_protocol": "PLAINTEXT",
            "ssl": {}
        }
    }

    async def mock_create_website_check_tasks(*args, **kwargs):
        return []

    async def mock_process_website_checks(*args, **kwargs):
        pass

    async def mock_sleep(*args, **kwargs):
        pass

    class MockProducer:
        async def close(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            await self.close()

    with patch('website_checker.create_website_check_tasks',
               side_effect=mock_create_website_check_tasks) as mock_check_tasks:
        with patch('website_checker.process_website_checks',
                   side_effect=mock_process_website_checks) as mock_website_checks:
            with patch('website_checker.asyncio.sleep', new=mock_sleep):
                with patch('website_checker.ProducerFactory.get_producer', return_value=MockProducer()):
                    await main(config, run_once=True)

    mock_check_tasks.assert_awaited_once_with(ANY, config["websites"])
    mock_website_checks.assert_awaited_once_with([], config["timeout"], ANY, "website_metrics", ANY)
