# 2.15 (2026-03-04)

* Handle `while True` loops without `break` statements (kreathon).
* Add whitelist for `ssl.SSLContext` (tunnelsociety, #392).
* Add more ruff rules (even-even).
* Drop support for Python 3.8 (Jendrik Seipp, #398).
* Add support for Python 3.14 (even-even).

# 2.14 (2024-12-08)

* Improve reachability analysis (kreathon, #270, #302).
* Add type hints for `get_unused_code` and the fields of the `Item` class (John Doknjas, #361).

# 2.13 (2024-10-02)

* Add support for Python 3.13 (Jendrik Seipp, #369).
* Add PyPI and conda-forge badges to README file (Trevor James Smith, #356).
* Include `tests/**/*.toml` in sdist (Colin Watson).

# 2.12 (2024-09-17)

* Use `ruff` for linting and formatting (Anh Trinh, #347, #349).
* Replace `tox` by `pre-commit` for linting and formatting (Anh Trinh, #349).
* Add `--config` flag to specify path to pyproject.toml configuration file (Glen Robertson, #352).

