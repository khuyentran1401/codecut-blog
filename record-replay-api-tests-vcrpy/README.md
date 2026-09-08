# VCR.py API Test Examples

Companion code for the article *Stop Letting Public APIs Break Your Python
Tests: Record Them Once with VCR.py*.

## Files

| Path | What it holds |
| --- | --- |
| `repo_client.py` | Small GitHub API client used in the article |
| `test_repo_client.py` | Mock, live API, and VCR.py pytest examples |
| `tests/fixtures/cassettes/github_vcrpy.yaml` | Recorded GitHub API response for replay |

## Setup

From this folder:

```bash
uv pip install vcrpy requests pytest
```

## Run the Reproducible Tests

These tests do not need a live GitHub API call because the VCR.py test replays
the recorded cassette:

```bash
pytest test_repo_client.py
```

The live API test is skipped by default. To run it intentionally:

```bash
RUN_LIVE_API_TESTS=1 pytest test_repo_client.py
```

To re-record the cassette, delete
`tests/fixtures/cassettes/github_vcrpy.yaml` and run the tests again with
network access.
