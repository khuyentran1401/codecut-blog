from __future__ import annotations

from typing import TypedDict

import requests


class RepositorySummary(TypedDict):
    full_name: str
    description: str | None
    stars: int
    license: str | None
    default_branch: str


def get_repository_license(owner: str, repo: str) -> str | None:
    response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=10)
    response.raise_for_status()

    data = response.json()
    license_data = data.get("license")

    return license_data["spdx_id"] if license_data else None


def get_repository_summary(owner: str, repo: str) -> RepositorySummary:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    license_data = data.get("license")

    return {
        "full_name": data["full_name"],
        "description": data["description"],
        "stars": data["stargazers_count"],
        "license": license_data["spdx_id"] if license_data else None,
        "default_branch": data["default_branch"],
    }
