"""Tests for pinterest_automation/postiz.py::PostizClient.

The HTTP session is replaced with a fake so no network is touched. Covers the
integration lookup across response shapes, upload validation, the create-post
request body, and error propagation.

Run with:
    cd /home/user/claude- && python3 -m pytest tests/test_postiz_client.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pinterest_automation.postiz as postiz  # noqa: E402


class _FakeResp:
    def __init__(self, status_code=200, json_data=None, text="", content=b"x"):
        self.status_code = status_code
        self._json = json_data
        self.text = text
        self.content = content

    def json(self):
        return self._json


class _FakeSession:
    """Records requests and returns queued responses keyed by (method, path-suffix)."""

    def __init__(self):
        self.headers = {}
        self.calls = []
        self._responses = {}

    def queue(self, method, suffix, resp):
        self._responses[(method, suffix)] = resp

    def _match(self, method, url):
        for (m, suffix), resp in self._responses.items():
            if m == method and url.endswith(suffix):
                return resp
        raise AssertionError(f"no fake response for {method} {url}")

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return self._match("GET", url)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self._match("POST", url)


def _client(monkeypatch):
    client = postiz.PostizClient(api_key="key-123")
    session = _FakeSession()
    client._session = session
    return client, session


def test_client_requires_api_key():
    with pytest.raises(postiz.PostizError):
        postiz.PostizClient(api_key="")


def test_auth_header_has_no_bearer_prefix():
    client = postiz.PostizClient(api_key="key-123")
    assert client._session.headers["Authorization"] == "key-123"


def test_find_pinterest_integration_matches_identifier(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue(
        "GET", "/integrations",
        _FakeResp(json_data=[
            {"id": "1", "identifier": "facebook"},
            {"id": "2", "provider": "pinterest"},
        ]),
    )
    assert client.find_pinterest_integration_id() == "2"


def test_find_pinterest_integration_unwraps_dict_payload(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue(
        "GET", "/integrations",
        _FakeResp(json_data={"integrations": [{"integrationId": "9", "identifier": "Pinterest"}]}),
    )
    assert client.find_pinterest_integration_id() == "9"


def test_find_pinterest_integration_raises_when_absent(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue("GET", "/integrations", _FakeResp(json_data=[{"id": "1", "identifier": "tiktok"}]))
    with pytest.raises(postiz.PostizError):
        client.find_pinterest_integration_id()


def test_list_integrations_raises_on_http_error(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue("GET", "/integrations", _FakeResp(status_code=500, text="boom"))
    with pytest.raises(postiz.PostizError):
        client.list_integrations()


def test_upload_image_returns_id_and_path(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue("POST", "/upload", _FakeResp(json_data={"id": "media-1", "path": "/m/1.jpg"}))
    out = client.upload_image(b"bytes", "p.jpg")
    assert out == {"id": "media-1", "path": "/m/1.jpg"}


def test_upload_image_raises_when_id_missing(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue("POST", "/upload", _FakeResp(json_data={"path": "/m/1.jpg"}))
    with pytest.raises(postiz.PostizError):
        client.upload_image(b"bytes", "p.jpg")


def test_post_pin_builds_expected_body_and_returns_id(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue("POST", "/upload", _FakeResp(json_data={"id": "media-1", "path": "/m/1.jpg"}))
    session.queue("POST", "/posts", _FakeResp(json_data={"id": "post-7"}))

    post_id = client.post_pin(
        integration_id="int-1",
        title="t" * 200,  # over the 100-char Pinterest title cap
        description="desc",
        link="https://x.com/p",
        image_bytes=b"img",
        filename="p.jpg",
        board="board-1",
    )

    assert post_id == "post-7"
    body = next(kw["json"] for (m, url, kw) in session.calls if url.endswith("/posts"))
    post = body["posts"][0]
    assert post["integration"] == {"id": "int-1"}
    assert post["settings"]["__type"] == "pinterest"
    assert len(post["settings"]["title"]) == 100   # title clamped
    assert post["settings"]["board"] == "board-1"
    assert post["value"][0]["content"] == "desc"
    assert post["value"][0]["image"][0]["id"] == "media-1"


def test_post_pin_raises_on_create_error(monkeypatch):
    client, session = _client(monkeypatch)
    session.queue("POST", "/upload", _FakeResp(json_data={"id": "media-1"}))
    session.queue("POST", "/posts", _FakeResp(status_code=400, text="bad"))
    with pytest.raises(postiz.PostizError):
        client.post_pin(
            integration_id="int-1", title="t", description="d", link="l",
            image_bytes=b"i", filename="p.jpg",
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
