"""Unit tests for SonarQube client helpers and request handling."""

from datetime import datetime
import requests
import pytest

from backend.src.services.sonarqube_client import (
    SonarQubeClient,
    validate_connection_url,
    parse_projects_response,
    parse_measures_response,
)
from backend.src.utils.errors import (
    ConnectionError,
    TokenExpiredError,
    RateLimitError,
    InvalidAPIResponseError,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None, json_error=False):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("invalid json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} error")


def test_validate_connection_url_accepts_valid_urls():
    assert validate_connection_url("https://sonarqube.local") is True
    assert validate_connection_url("http://localhost:9000") is True


@pytest.mark.parametrize("bad_url", ["", "ftp://host", "http://bad url"]) 
def test_validate_connection_url_rejects_invalid_urls(bad_url):
    with pytest.raises(ValueError):
        validate_connection_url(bad_url)


def test_parse_projects_response_success():
    response = {
        "components": [
            {"key": "proj1", "name": "Project 1", "description": "desc", "analysisDate": "2026-02-10T00:00:00Z"},
            {"key": "proj2", "name": "Project 2"},
        ]
    }

    parsed = parse_projects_response(response)

    assert len(parsed) == 2
    assert parsed[0]["project_key"] == "proj1"
    assert isinstance(parsed[0]["last_analysis_date"], datetime)
    assert parsed[1]["project_key"] == "proj2"


def test_parse_projects_response_invalid_shape():
    with pytest.raises(InvalidAPIResponseError):
        parse_projects_response({"components": "not-a-list"})


def test_parse_measures_response_success_with_details_and_severity():
    response = {
        "component": {
            "analysisDate": "2026-02-10T00:00:00Z",
            "measures": [
                {"metric": "bugs", "value": "2"},
                {"metric": "vulnerabilities", "value": "1"},
                {"metric": "code_smells", "value": "5"},
                {"metric": "coverage", "value": "81.5"},
                {"metric": "duplicated_lines_density", "value": "2.5"},
                {"metric": "alert_status", "value": "OK"},
                {"metric": "quality_gate_details", "value": "{\"conditions\":[]}"},
                {"metric": "blocker_violations", "value": "0"},
                {"metric": "critical_violations", "value": "1"},
                {"metric": "major_violations", "value": "2"},
                {"metric": "minor_violations", "value": "3"},
                {"metric": "info_violations", "value": "4"},
                {"metric": "ncloc", "value": "1200"},
            ],
        }
    }

    parsed = parse_measures_response(response)

    assert parsed["bugs_count"] == 2
    assert parsed["coverage_pct"] == 81.5
    assert parsed["quality_gate_status"] == "OK"
    assert parsed["quality_gate_details"] == {"conditions": []}
    assert parsed["severity_breakdown"]["critical"] == 1
    assert parsed["ncloc"] == 1200


def test_parse_measures_response_invalid_quality_gate_status():
    response = {
        "component": {
            "measures": [
                {"metric": "alert_status", "value": "BROKEN"},
            ]
        }
    }

    with pytest.raises(InvalidAPIResponseError):
        parse_measures_response(response)


def test_parse_measures_response_invalid_json_details():
    response = {
        "component": {
            "measures": [
                {"metric": "quality_gate_details", "value": "{invalid-json}"},
            ]
        }
    }

    with pytest.raises(InvalidAPIResponseError):
        parse_measures_response(response)


def test_make_request_unauthorized_raises_token_expired(monkeypatch):
    client = SonarQubeClient("https://sq.local", "token")
    monkeypatch.setattr(client.session, "request", lambda **kwargs: FakeResponse(status_code=401))

    with pytest.raises(TokenExpiredError):
        client._make_request("GET", "/api/system/status")


def test_make_request_rate_limit_raises_after_max_retries(monkeypatch):
    client = SonarQubeClient("https://sq.local", "token")
    monkeypatch.setattr("backend.src.services.sonarqube_client.sleep", lambda _: None)
    monkeypatch.setattr(
        client.session,
        "request",
        lambda **kwargs: FakeResponse(status_code=429, headers={"Retry-After": "7"}),
    )

    with pytest.raises(RateLimitError) as exc:
        client._make_request("GET", "/api/system/status")

    assert exc.value.retry_after_seconds == 7


def test_make_request_server_error_raises_connection_error(monkeypatch):
    client = SonarQubeClient("https://sq.local", "token")
    monkeypatch.setattr("backend.src.services.sonarqube_client.sleep", lambda _: None)
    monkeypatch.setattr(client.session, "request", lambda **kwargs: FakeResponse(status_code=503))

    with pytest.raises(ConnectionError):
        client._make_request("GET", "/api/system/status")


def test_make_request_invalid_json_raises_invalid_response(monkeypatch):
    client = SonarQubeClient("https://sq.local", "token")
    monkeypatch.setattr(client.session, "request", lambda **kwargs: FakeResponse(status_code=200, json_error=True))

    with pytest.raises(InvalidAPIResponseError):
        client._make_request("GET", "/api/system/status")


def test_get_project_metrics_retries_without_branch_on_404(monkeypatch):
    client = SonarQubeClient("https://sq.local", "token")

    calls = {"count": 0}

    def fake_make_request(method, endpoint, params=None, json_data=None, retry_count=0):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionError("404 not found")
        return {
            "component": {
                "analysisDate": "2026-02-10T00:00:00Z",
                "measures": [
                    {"metric": "bugs", "value": "1"},
                    {"metric": "vulnerabilities", "value": "0"},
                    {"metric": "code_smells", "value": "0"},
                    {"metric": "coverage", "value": "90"},
                    {"metric": "duplicated_lines_density", "value": "1.1"},
                    {"metric": "alert_status", "value": "OK"},
                ],
            }
        }

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = client.get_project_metrics("proj-key", branch="feature/x")

    assert calls["count"] == 2
    assert result["bugs_count"] == 1
    assert result["quality_gate_status"] == "OK"


def test_get_project_branches_invalid_response():
    client = SonarQubeClient("https://sq.local", "token")

    def fake_make_request(method, endpoint, params=None, json_data=None, retry_count=0):
        return {"branches": "invalid"}

    client._make_request = fake_make_request

    with pytest.raises(InvalidAPIResponseError):
        client.get_project_branches("proj-key")
