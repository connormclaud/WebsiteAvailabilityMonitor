import aiohttp
from website_checker import check_website
import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_check_website_success():
    async with aiohttp.ClientSession() as session:
        result = await check_website(session, "https://httpbin.org/get")

        assert result["url"] == "https://httpbin.org/get"
        assert 0 <= result["response_time"] <= 5
        assert result["status_code"] == 200
        assert result["content_check"] is None


@pytest.mark.asyncio
async def test_check_website_failure():
    async with aiohttp.ClientSession() as session:
        result = await check_website(session, "https://httpbin.org/status/404")

        assert result["url"] == "https://httpbin.org/status/404"
        assert 0 <= result["response_time"] <= 5
        assert result["status_code"] == 404
        assert result["content_check"] is None


@pytest.mark.asyncio
async def test_check_website_content_match():
    async with aiohttp.ClientSession() as session:
        pattern = r"Herman Melville"
        result = await check_website(session, "https://httpbin.org/html", regexp=pattern)

        assert result["url"] == "https://httpbin.org/html"
        assert result["content_check"]


@pytest.mark.asyncio
async def test_check_website_exception_handling():
    async with aiohttp.ClientSession() as session:
        with patch('aiohttp.ClientSession.get', side_effect=Exception("Test exception")):
            result = await check_website(session, "https://httpbin.org/get")
            assert result is None


@pytest.mark.asyncio
async def test_main_function():
    async def mock_check_website(*args, **kwargs):
        return {
            "url": "https://httpbin.org/get",
            "response_time": 0.1,
            "status_code": 200,
            "content_check": None,
        }

    async def mock_sleep(*args, **kwargs):
        return None

    config = {"websites": [{"url": "https://example.com"}], "kafka": {"producer_interval": 60}}
    with patch('website_checker.check_website', side_effect=mock_check_website) as mock_check_website:
        with patch('website_checker.asyncio.sleep', new=mock_sleep):
            from website_checker import main
            await main(config, run_once=True)
            mock_check_website.assert_called()
