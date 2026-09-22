# Selenium Learning Project
![Selenium Tests](https://github.com/dsmitty52/selenium-learning-project/actions/workflows/tests.yml/badge.svg)

A hands-on project for learning Selenium WebDriver and pytest from scratch, with no prior professional test-automation experience. Built incrementally, one concept at a time, against a public practice site.

## What this demonstrates

- Locating elements with `By.ID`, `By.CSS_SELECTOR`, and `By.XPATH`
- Explicit waits (`WebDriverWait` + `expected_conditions`) instead of fixed `time.sleep()` delays
- Interacting with elements (`send_keys`, `click`, reading `.text`)
- Structuring reusable helper functions around a Selenium flow
- Converting manual scripts into real, assertable `pytest` tests
- `pytest` fixtures (`conftest.py`) for shared setup/teardown (a fresh browser per test, guaranteed cleanup even on failure)

See [`SELENIUM_LEARNING_LOG.md`](SELENIUM_LEARNING_LOG.md) for a running, detailed log of concepts covered, gotchas hit, and bugs debugged along the way.

## Project structure

```
.
├── conftest.py                  # pytest fixture(s) — provides a Chrome `driver` per test
├── test_login.py                # login/logout test suite (helper functions + test_* functions)
├── test_setup.py                # first smoke-test script (confirms the whole toolchain works)
├── requirements.txt             # pinned dependencies
├── SELENIUM_LEARNING_LOG.md     # running log of concepts learned, for self-quizzing
└── venv/                        # local virtual environment (not committed)
```

## Setup

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
   (If PowerShell blocks the script, run once: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Chrome must be installed locally — Selenium Manager (bundled since Selenium 4.6+) auto-downloads the matching ChromeDriver, no manual driver setup needed.

## Running the tests

```
pytest test_login.py -v
```

## Practice site used

[the-internet.herokuapp.com](https://the-internet.herokuapp.com/login) — a public site built specifically for Selenium practice. Test credentials: `tomsmith` / `SuperSecretPassword!`.
