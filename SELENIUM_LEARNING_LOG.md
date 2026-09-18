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

## Up Next (not yet covered)

- Multi-window/tab handling (`driver.window_handles`, `driver.switch_to.window(...)`) — relevant once a click opens a new tab (e.g. external links).
- Headless mode (running without a visible browser window).
- More complex multi-page navigation flows.
- Additional assertions: `driver.current_url`, flash message CSS class (`success` vs `error`) via `get_attribute("class")`, page title, password field `type` attribute.
- New practice pages on the-internet.herokuapp.com (dropdowns, checkboxes, dynamic loading, JS alerts, file upload) for fresh locator/interaction challenges.
