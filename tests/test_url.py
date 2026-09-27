import pytest

from core.downloader import validate_douyin_url


def test_valid_douyin_url():
    validate_douyin_url("https://www.douyin.com/video/123")


@pytest.mark.parametrize("url", [
    "http://www.douyin.com/video/123",
    "https://evil.example/video/123",
    "https://www.youtube.com/watch?v=x",
])
def test_invalid_url(url):
    with pytest.raises(ValueError):
        validate_douyin_url(url)
