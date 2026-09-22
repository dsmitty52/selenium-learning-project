# Selenium Learning Log

Running summary of Selenium concepts covered so far. Intended to be pasted into Claude (or another LLM) to generate quiz/multiple-choice questions for review.

## Environment Setup

- Installed Selenium via `pip install selenium` inside a **virtual environment** (`python -m venv venv`, then `venv\Scripts\Activate.ps1`).
- A venv is just an isolated folder holding a private Python interpreter + packages for one project — not a VM. Nothing runs in the background; there's no "stop" step, just close the terminal or run `deactivate`.
- PowerShell blocks `.ps1` scripts by default (`about_Execution_Policies`). Fixed with:
  ```
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Selenium 4.6+ ships **Selenium Manager**, which auto-downloads the correct ChromeDriver matching your installed Chrome — no manual driver download needed.
- `pip freeze > requirements.txt` documents installed dependencies for reproducibility.

## Basic Script Structure

```python
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://example.com")
print(driver.title)
driver.quit()
```

- `webdriver.Chrome()` launches a real browser session.
- `driver.get(url)` navigates and blocks until the page load completes.
- `driver.quit()` closes the browser and ends the session — always call it when done (or unreachable/undefined-reference bugs can result, see below).
- Selenium calls are **live, sequential commands executed against the real browser at that point in the script** — not declarations evaluated later. Order matters a lot.

## Locators (`By`)

```python
from selenium.webdriver.common.by import By
```

| Strategy | Example | Notes |
|---|---|---|
| `By.ID` | `By.ID, "username"` | Best when available — unique & stable |
| `By.CSS_SELECTOR` | `By.CSS_SELECTOR, "button[type='submit']"` | Preferred default — see comparison below |
| `By.XPATH` | `By.XPATH, "//button[text()='Submit']"` | Needed for text-matching or upward DOM traversal |
| `By.NAME` / `By.CLASS_NAME` / `By.LINK_TEXT` | — | Narrower use cases |

**CSS selector syntax gotcha**: attribute matching uses **square brackets**, not curly braces —
`button[type='submit']` ✅ vs `button{type='submit'}` ❌ (curly braces are for CSS rule *bodies*, not selectors).

**CSS vs. XPath — which to prefer:**
- **CSS is generally preferred**: faster (native browser query engine vs. an extra XPath engine layer), more concise, and the same syntax used in real stylesheets/JS.
- **XPath is necessary for things CSS can't do**:
  - Matching by visible text: `//button[text()='Submit']`
  - Traversing **upward** to a parent/ancestor: `//img[@alt='...']/..` or `/ancestor::a` (CSS can only go down/sideways)
  - More complex conditionals (`contains()`, `and`/`or`, positional matching)
- Rule of thumb: default to CSS, drop to XPath only when you need text-matching or upward traversal.

Attributes without a dedicated `By` shortcut (e.g. `alt` on an `<img>`) still work via XPath/CSS:
```python
driver.find_element(By.XPATH, "//img[@alt='Fork me on GitHub']")
driver.find_element(By.CSS_SELECTOR, "img[alt='Fork me on GitHub']")
```

## Interacting with Elements

- `.send_keys("text")` — types into an input field.
- `.click()` — clicks an element (button, link, etc.).
- `.text` — reads the visible text of an element (a property, not a method — must be `print()`ed or assigned to actually use the value).
- `.get_attribute("value")` — reads the current value of a form field (useful for debugging what was actually typed, using `repr(...)` to catch invisible/stray characters).

## Waits

- Avoid `time.sleep()` — it's a fixed delay: too short = flaky (element not ready yet), too long = wastes time every run.
- Use `WebDriverWait` + `expected_conditions` (`EC`) instead — polls repeatedly up to a timeout, proceeding as soon as the condition is true:

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

wait = WebDriverWait(driver, 10)   # just creates the waiter object — no action yet
message = wait.until(EC.visibility_of_element_located((By.ID, "flash")))
```

- **Ordering matters**: `wait.until(...)` must run *after* the action that triggers the awaited change (e.g. after `.click()`), and *after* `driver.get()` has navigated to the right page. Calling it too early waits against a blank/wrong page and just times out.
- `EC.element_to_be_clickable((by, locator))` — waits for an element to be both visible **and** enabled; a successful (non-timeout) result is itself proof the element is clickable, no separate check needed.

## Functions & Reuse

Wrapping a repeated flow (e.g. attempting a login) in a function avoids duplicating steps for multiple scenarios:

```python
def attempt_login(username, password):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.get("https://the-internet.herokuapp.com/login")
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    message = wait.until(EC.visibility_of_element_located((By.ID, "flash")))
    text = message.text     # pull text out BEFORE quitting — the element becomes stale after
    driver.quit()
    return text              # return must come AFTER quit(), or driver.quit() becomes unreachable code
```

Key gotcha: `message` (a `WebElement`) is tied to the live browser session. You must extract `.text` into a plain string *before* `driver.quit()`, since the element reference becomes invalid once the session ends. Similarly, `return` immediately exits a function — any code after it (like `driver.quit()`) never runs, so ordering within the function body matters.

## pytest — Turning Scripts into Real Tests

- Printing output and eyeballing it doesn't scale — `assert` lets the test itself decide pass/fail.
- Install: `pip install pytest`.
- Pytest auto-discovers functions named `test_*` inside files named `test_*.py`.

```python
def test_successful_login():
    message = attempt_login("tomsmith", "SuperSecretPassword!")   # must capture the return value!
    assert "You logged into a secure area!" in message
```

Common bug: forgetting to assign the function call's return value (`message = attempt_login(...)`) — without it, the variable used in `assert` is never defined, raising `NameError`.

- Run with: `pytest test_login.py -v` (`-v` = verbose — lists each test by name with PASSED/FAILED, vs. just terse dots + a summary count without it).
- **Save the file before running** — pytest (like `python script.py`) reads from disk, so unsaved editor changes are invisible to the test run.

## More Locator Practice: Non-`id` Attributes & Real Markup

- Inspected an `<img alt="Fork me on GitHub">` element with no `id` — located it via `By.XPATH, "//img[@alt='...']"` or `By.CSS_SELECTOR, "img[alt='...']"`.
- To confirm exact real-world markup instead of guessing, fetched the live page HTML directly (`curl`), including authenticating via a cookie jar (`curl -c cookies.txt -b cookies.txt -d "username=...&password=..." .../authenticate`) to see the **logged-in** secure-area HTML, since `/secure` redirects to `/login` when unauthenticated. Found the real logout element:
  ```html
  <a class="button secondary radius" href="/logout"><i class="icon-2x icon-signout"> Logout</i></a>
  ```
  No `id`, but `href="/logout"` makes a clean, unique selector: `By.CSS_SELECTOR, "a[href='/logout']"`.
- Lesson: when unsure of a selector, inspect the *actual* rendered markup (DevTools, or fetching the real HTML) rather than guessing — especially for elements without an `id`.

## Multi-Step Flows: Login → Logout

Added a `test_successful_logout` flow: log in, then click the logout link, then assert the post-logout flash message.

Key risk introduced: after `.click()` on the login submit button, the next page (`/secure`) may not have rendered yet — `.click()` does **not** block for navigation to finish (unlike `driver.get()`). Calling `find_element` for the logout link immediately after can race and throw `NoSuchElementException`. Fix: wait for the logout link to be clickable before interacting with it:
```python
logout_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/logout']")))
logout_link.click()
```

## Terminology Check-in

- **Helper functions** (`attempt_login`, `attempt_logout`) — perform an action and return a result; no `assert`, not discovered/run by pytest directly.
- **Test functions** (`test_successful_login`, etc.) — named `test_*`, discovered and run by pytest, contain the `assert` calls.
- **Fixtures** (`driver` in `conftest.py`) — setup/teardown providers, referenced by parameter name, not called directly.

## pytest Fixtures

A fixture is a function marked `@pytest.fixture` that provides setup/teardown for tests. Tests "request" a fixture just by naming a parameter after it — pytest matches by name and injects the result automatically, no import/explicit call needed.

```python
# conftest.py
import pytest
from selenium import webdriver

@pytest.fixture
def driver():
    d = webdriver.Chrome()   # SETUP — runs before the test
    yield d                   # value handed to the test
    d.quit()                  # TEARDOWN — runs after the test, even if it FAILED
```

Key concepts:
- **`yield` splits setup from teardown.** Code before `yield` runs first; code after runs after the test finishes — critically, even if the test raised an exception. This is what fixes the "leaked browser on failed assertion" problem that existed when `driver.quit()` lived inside `attempt_login` itself (an exception before reaching that line meant it never ran).
- **Matching is by parameter name**: `def test_x(driver):` — pytest sees the `driver` parameter, finds the fixture named `driver`, calls it, and passes in whatever it `yield`s.
- **`conftest.py`** is a special filename pytest auto-discovers — fixtures defined there are available to every test file in the same folder, with no import needed.
- **Scope** (default `function`) controls how often a fixture re-runs — default is a fresh instance per test function, which is what you want for an isolated browser session per test.

### Converting existing helpers to use the fixture

Before, `attempt_login`/`attempt_logout` each created **and quit** their own `driver` internally. After converting to use the fixture, the driver lifecycle moves entirely to `conftest.py`, and the helper functions just receive `driver` as a parameter:

```python
def attempt_login(driver, username, password):
    wait = WebDriverWait(driver, 10)
    driver.get("https://the-internet.herokuapp.com/login")
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    message = wait.until(EC.visibility_of_element_located((By.ID, "flash")))
    return message.text   # no driver.quit() here anymore, and no need to pre-extract .text into a separate variable first — the fixture's teardown runs later, after this function has already returned
```

And every test function must both **accept** `driver` as a parameter and **pass it through** to the helper:
```python
def test_successful_login(driver):
    message = attempt_login(driver, "tomsmith", "SuperSecretPassword!")
    assert "You logged into a secure area!" in message
```

**Common bug during this conversion**: updating the helper function's signature to take `driver` first, but forgetting to update the call sites (test functions) to pass it — e.g. still calling `attempt_login("tomsmith", "SuperSecretPassword!")` with only two args. Since `driver` is now the *first* parameter, the string `"tomsmith"` silently gets bound to `driver` instead, `"SuperSecretPassword!"` gets bound to `username`, and Python complains `password` is missing (`TypeError: missing 1 required positional argument: 'password'`). Lesson: changing a function's parameter list means finding and updating *every* call site, not just the definition.

## Environment Gotcha: `pytest` Not Recognized

Error seen: `pytest : The term 'pytest' is not recognized...`. Cause: the venv wasn't activated in that terminal session, so `pytest` (installed only inside `venv`) wasn't on `PATH`. Fix: `venv\Scripts\Activate.ps1` (confirm the prompt shows `(venv)`), then retry. Fallback that always works regardless of activation: `venv\Scripts\python.exe -m pytest test_login.py -v`.

## Practice Site Used

`https://the-internet.herokuapp.com/login` — a public site built specifically for Selenium practice. Known test credentials: `tomsmith` / `SuperSecretPassword!`. Also explored `/secure` (post-login page) and `/logout`.

## Putting the Project on GitHub

Took the project from a plain local folder to a public GitHub repo — not a Selenium concept itself, but a standard part of having a presentable, version-controlled portfolio project.

**`.gitignore` — root-level, not buried in subfolders.** Both `venv/` (auto-created by `python -m venv`) and `.pytest_cache/` (auto-created by pytest) come with their own internal `.gitignore` containing just `*`. These work, but are fragile/non-standard — the better approach is **one `.gitignore` at the project root** listing everything to exclude:
```
venv/
__pycache__/
.pytest_cache/
```
(`__pycache__/` — Python's compiled bytecode cache — is the same category: auto-generated, machine-specific, safe to exclude.)

**`requirements.txt` encoding gotcha.** Running `pip freeze > requirements.txt` in PowerShell saved the file as **UTF-16LE** (confirmed via the `file` command) instead of plain UTF-8 — a quirk of PowerShell's `>` redirection. This can break `pip install -r requirements.txt` for anyone else using the file. Fix: force UTF-8 explicitly:
```powershell
pip freeze | Out-File -Encoding utf8 requirements.txt
```
This was also a good moment to catch that the file was stale — it didn't list `pytest` (and its dependencies like `pluggy`, `iniconfig`, `packaging`) even though pytest had been in use for a while, since it was generated before pytest was installed.

**`README.md`** — added to explain what the project demonstrates, its file structure, and setup/run instructions, so it's legible to someone (recruiter or otherwise) landing on the repo without prior context. Decided to keep `SELENIUM_LEARNING_LOG.md` in the repo too, since this is explicitly framed as a learning project — the log itself is a reasonable signal of a deliberate, structured learning process.

**Git workflow used:**
```
git init
git add .gitignore README.md SELENIUM_LEARNING_LOG.md conftest.py requirements.txt test_login.py test_setup.py
git commit -m "Initial commit: Selenium learning project setup"
```
Naming files explicitly in `git add` (rather than `git add .`) is a good habit — it forces a glance at exactly what's being staged each time.

**Windows case-sensitivity gotcha**: `git add readme.md` initially failed to match, because the actual file is `README.md` — Windows' filesystem is case-insensitive (so Explorer treats them as "the same"), but `git add` can fail to resolve a mismatched-case pathspec depending on git's config. Lesson: run `git status` first and copy-paste exact filenames from its output rather than retyping them from memory.

**Connecting to GitHub and pushing:**
```
git remote add origin https://github.com/<username>/<repo>.git
git branch -M main
git push -u origin main
```
- `remote add origin` — tells the local repo where "GitHub" is.
- `branch -M main` — renames the default branch from `master` to `main` (GitHub's modern convention).
- `push -u origin main` — uploads commits and sets `main` to track `origin/main`, so future pushes only need `git push`.

Repo created empty on GitHub first (no auto-generated README/`.gitignore` from GitHub's UI, to avoid a conflict with the ones already committed locally).

## Headless Mode

Headless = Chrome runs with no visible window/rendering — necessary for CI runners, which have no display, and also useful locally for faster/background runs.

```python
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
d = webdriver.Chrome(options=options)
```

Made this **conditional** in the `driver` fixture so local runs stay visible (useful for watching/debugging) while CI runs go headless automatically, by checking an environment variable GitHub Actions sets on every run (`CI=true`):

```python
# conftest.py
import os
from selenium.webdriver.chrome.options import Options

options = Options()
if os.environ.get("CI") == "true":
    options.add_argument("--headless=new")

@pytest.fixture
def driver():
    d = webdriver.Chrome(options=options)
    yield d
    d.quit()
```

**Bug hit while building this**: initially added `options.add_argument("--headless=new")` both unconditionally *and* inside the `if os.environ.get("CI") == "true":` block. Since the unconditional line ran every time regardless, it silently defeated the whole point of the conditional — headless was always on, even locally, so the visible browser window stopped appearing at all. Fix: delete the unconditional line, keep only the one inside the `if`. Lesson: a duplicate/redundant line doesn't just do nothing extra — if it's *unconditional* while a nearby conditional does the "same" thing, the conditional becomes dead code.

## CI/CD with GitHub Actions

**CI (Continuous Integration)**: automatically run the test suite on a clean, temporary machine whenever code is pushed (or a PR opened) — catches "works on my machine" issues and gives an automatic pass/fail signal, rather than relying on remembering to run `pytest` locally. **CD (Continuous Deployment)** is the next step after CI — automatically shipping something once tests pass; not relevant for this project since nothing gets deployed, so CI alone was the goal here.

Configured entirely via one YAML file committed into the repo: `.github/workflows/tests.yml`. GitHub auto-discovers anything in that folder — no external service or account setup needed beyond already being on GitHub.

```yaml
name: Selenium Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest test_login.py -v
```

Key concepts:
- **`on:`** — triggers. Here: any push to `main`, or any PR targeting `main`.
- **`runs-on: ubuntu-latest`** — a fresh, temporary Linux VM GitHub spins up just for this run and destroys afterward. This is *why* headless mode is mandatory in CI — this machine has no display.
- **`uses:` vs `run:`** — `uses:` invokes a pre-built, reusable GitHub Action (e.g. `actions/checkout@v4` clones the repo onto the runner; without it, the runner is an empty VM with no code to test). `run:` executes a raw shell command directly — the same commands you'd type locally (`pip install -r requirements.txt`, `pytest ...`).
- **Matched the Python version to local** (3.14) rather than an arbitrary pin, so CI environment mirrors the real dev environment as closely as possible.
- **No manual Chrome/ChromeDriver install step needed** — `ubuntu-latest` runners come with Chrome pre-installed, and Selenium Manager auto-resolves the matching driver, same as locally.

**Result**: pushed the workflow, GitHub Actions triggered automatically on the push, and the full suite ran and passed in ~34 seconds (checked via `https://github.com/<user>/<repo>/actions`, and via the GitHub API — `GET /repos/<user>/<repo>/actions/runs` — to poll run status/conclusion programmatically). Every future push or PR to `main` now gets this same automatic pass/fail signal.

## Richer Assertions

Extended the existing tests to check more than just flash-message text, since text alone can pass even when something subtly wrong happened with app state:
- **`driver.current_url`** — verifies actual navigation/state, not just what's printed on screen.
- **Flash message CSS class** (`flash success` vs `flash error`, via `driver.find_element(By.ID, "flash").get_attribute("class")`) — more robust than matching exact wording, since copy can change without meaning behavior changed.
- **`driver.title`** — simple baseline sanity check.
- **Password field masking** — a new standalone test (`test_password_field_is_masked`) checking `password_field.get_attribute("type") == "password"`. Different from the others because it has to run *before* submitting the form (the password field only exists on the login page), so it doesn't reuse `attempt_login` at all — just navigates and checks directly.

Key enabler: these all work by using the `driver` fixture parameter directly inside the test function, *after* calling a helper like `attempt_login`. This works because `driver` stays alive for the whole test — the fixture's `d.quit()` teardown only runs after the test function fully returns — so the test can keep querying the live page even though the helper function already returned.

## The Pull Request (PR) Workflow

Practiced the standard professional git workflow: never commit directly to `main` for a "real" change — branch, change, push, open a PR, let CI gate it, merge.

```
git checkout -b add-ci-badge
# ... make changes ...
git add README.md
git commit -m "Add CI status badge to README"
git push -u origin add-ci-badge          # -u needed: first push of a *new* branch name
# open PR on GitHub (base: main, compare: add-ci-badge)
# CI runs automatically via the workflow's existing `pull_request:` trigger
# merge once checks pass
git checkout main
git pull                                  # sync local main with the merge that happened on GitHub
git branch -d add-ci-badge                # optional cleanup of the now-merged local branch
```

Added a live CI status badge to `README.md` as the practice change for this PR:
```markdown
![Selenium Tests](https://github.com/<user>/<repo>/actions/workflows/tests.yml/badge.svg)
```
This is a GitHub-hosted image URL that always reflects the latest workflow run's pass/fail state.

## Debugging a Real Flaky CI Failure (External-Site Timeout)

While the PR's CI check ran, `test_successful_logout` failed intermittently on GitHub Actions (headless/CI) despite passing locally — a genuinely realistic bug-hunting scenario, not a contrived exercise.

**First failure mode**: `AssertionError` — got the *login* success message ("You logged into a secure area!") instead of the *logout* one. Root cause: right after clicking the logout link, the *old* page's `#flash` element (from the login step) was still visible for a brief moment before navigation completed. `wait.until(EC.visibility_of_element_located((By.ID, "flash")))` doesn't know it's supposed to wait for a *new* page — it just checks "is a `#flash` visible right now," and the stale one already was. **Fix**: wait for the URL to actually change first, before checking the flash text:
```python
logout_button.click()
wait.until(EC.url_contains("/login"))   # confirm navigation actually happened first
message = wait.until(EC.visibility_of_element_located((By.ID, "flash")))
```

**Second failure mode**: after that fix, the same test later failed again on a different CI run — this time a `TimeoutException` raised directly from `wait.until(EC.url_contains("/login"))` itself, meaning the URL simply hadn't changed within the 10-second window. Diagnosed via the actual traceback (pulled from the GitHub Actions run logs) plus a strong secondary clue: that run's total suite time was **32.65s**, vs. **9.38s** on a clean passing run — evidence of genuine external slowness that run, not a logic bug. `the-internet.herokuapp.com` runs on Heroku's free tier, which is known to sleep idle apps and respond slowly on wake-up.

**Fix**: widen the wait timeout from `10` to `20` seconds in both `attempt_login` and `attempt_logout` (`WebDriverWait(driver, 20)`). This costs nothing on fast runs — `wait.until(...)` returns the instant its condition is true — it just raises the ceiling before giving up, as insurance against real-world external-service slowness.

**Lesson**: tests that depend on a real external service you don't control are inherently less reliable than tests against code/infrastructure you own. This is a well-known, accepted tradeoff in real-world test automation, not a sign of a broken test suite — the professional response is generous timeouts and tolerance for occasional retries, not assuming every failure is a logic bug.

## Up Next (not yet covered)

- Multi-window/tab handling (`driver.window_handles`, `driver.switch_to.window(...)`) — relevant once a click opens a new tab (e.g. external links).
- More complex multi-page navigation flows.
- New practice pages on the-internet.herokuapp.com (dropdowns, checkboxes, dynamic loading, JS alerts, file upload) for fresh locator/interaction challenges — dynamic loading especially, since it's a good case for waiting on an element that doesn't exist yet at all, vs. one that's just not visible/clickable yet.
- `pytest.mark.parametrize` — a cleaner way to express the 3 login-variant tests (`test_wrong_password`, `test_wrong_username`, `test_empty_credentials`) as one parameterized test instead of near-duplicate functions.
- Page Object Model (POM) — a standard pattern for structuring larger Selenium test suites (separating "how to find/interact with a page's elements" from "what the test asserts"), relevant once the suite grows beyond one page.
- CI enhancements: testing across multiple Python versions (a build matrix).
