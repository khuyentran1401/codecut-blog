from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest
import vcr

from repo_client import get_repository_license, get_repository_summary


github_vcr = vcr.VCR(
    cassette_library_dir="tests/fixtures/cassettes",
    record_mode="once",
    match_on=["method", "scheme", "host", "port", "path", "query"],
)


@patch("requests.get")
def test_get_repository_license_with_mock(mock_get: Mock) -> None:
    mock_response = Mock()
    mock_response.json.return_value = {"license": {"spdx_id": "MIT"}}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    license_id = get_repository_license("kevin1024", "vcrpy")

    assert license_id == "MIT"


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_API_TESTS") != "1",
    reason="Set RUN_LIVE_API_TESTS=1 to call the live GitHub API.",
)
def test_get_repository_summary_live() -> None:
    summary = get_repository_summary("kevin1024", "vcrpy")

    assert summary["full_name"] == "kevin1024/vcrpy"
    assert summary["license"] == "MIT"
    assert summary["default_branch"] == "master"


@github_vcr.use_cassette("github_vcrpy.yaml")
def test_get_repository_summary_with_vcr() -> None:
    summary = get_repository_summary("kevin1024", "vcrpy")

    assert summary["full_name"] == "kevin1024/vcrpy"
    assert summary["license"] == "MIT"
    assert summary["default_branch"] == "master"
