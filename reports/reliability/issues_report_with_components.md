# RELIABILITY Issues Analysis Report (With Component Details)

This report was generated using AI analysis of the SonarCloud reliability issues, including specific component and file information.

# 📊 SonarCloud Reliability Issues – EMI‑DM SonarQ‑Visualizer  

*Analysis date: 2026‑02‑12*  

---  

## 1. Summary of Issue Counts & Component Distribution  

| Severity | Total Issues |
|----------|--------------|
| **CRITICAL** | **12** |
| **MAJOR**    | 1 |
| **BLOCKER**  | 1 |
| **MINOR**    | 1 |
| **TOTAL**    | **15** |

### Issues by Component (file)

| Component (file) | # Issues | Severity breakdown |
|------------------|----------|--------------------|
| **backend/tests/integration/test_dashboard_api.py** | **8** | 7 × CRITICAL (UTC datetime) + 1 × MAJOR (float equality) |
| **backend/tests/unit/models/test_metrics_snapshot.py** | **5** | 5 × CRITICAL (UTC datetime) |
| **backend/tests/integration/test_preferences_api.py** | **1** | 1 × BLOCKER (`content` vs `data`) |
| **frontend/js/utils.js** | **1** | 1 × MINOR (`Number.isNaN` vs `isNaN`) |

> **Observation:** 13 / 15 issues (≈ 87 %) are the same **CRITICAL** rule *“Don’t use `datetime.datetime.utcnow` to create this datetime object.”* and are concentrated in two test modules.

---

## 2. Top 5 Most Common Issue Types  

| Issue Message (Rule) | Frequency | Severity |
|----------------------|-----------|----------|
| **Don’t use `datetime.datetime.utcnow` to create this datetime object.** | **12** | CRITICAL |
| Do not perform equality checks with floating point values. | 1 | MAJOR |
| Use `"content"` parameter instead of `"data"` for bytes or text. | 1 | BLOCKER |
| Prefer `Number.isNaN` over `isNaN`. | 1 | MINOR |
| *(No other distinct messages)* | – | – |

*The “UTC datetime” rule accounts for **80 %** of all reliability findings.*

---

## 3. Patterns & Categories  

| Category | Description | Affected Files |
|----------|-------------|----------------|
| **Date‑time handling (CRITICAL)** | Repeated use of `datetime.datetime.utcnow()` in test code to create timestamps. SonarCloud flags this because `utcnow()` returns a *naïve* datetime (no timezone info) and is non‑deterministic for reproducible tests. | `backend/tests/integration/test_dashboard_api.py` (7 occurrences) <br> `backend/tests/unit/models/test_metrics_snapshot.py` (5 occurrences) |
| **Floating‑point comparison (MAJOR)** | Direct equality (`==`) on floats can lead to flaky tests due to rounding errors. | `backend/tests/integration/test_dashboard_api.py` |
| **HTTP request payload API misuse (BLOCKER)** | Using the `data` argument for JSON/text payloads instead of the dedicated `content` argument, which can cause incorrect request bodies. | `backend/tests/integration/test_preferences_api.py` |
| **JavaScript NaN check (MINOR)** | Using the global `isNaN` (coerces argument) rather than `Number.isNaN` (strict). | `frontend/js/utils.js` |

### Cross‑cutting observations  

* All problematic issues are **in test code**, not production code.  
* The same anti‑pattern (`datetime.datetime.utcnow`) appears in both **integration** and **unit** test suites, suggesting a shared helper or copy‑paste habit.  
* No critical issues were reported in the core application logic (e.g., API handlers, business models).  

---

## 4. Specific Recommendations  

### 4.1. Fix the “UTC datetime” anti‑pattern  

| File | Recommended change |
|------|--------------------|
| `backend/tests/integration/test_dashboard_api.py` <br> `backend/tests/unit/models/test_metrics_snapshot.py` | Replace every `datetime.datetime.utcnow()` with **timezone‑aware** UTC datetime: <br> ```python<br> from datetime import datetime, timezone<br> now = datetime.now(timezone.utc)  # aware UTC<br> ``` <br> If the intention is to generate a *fixed* timestamp for deterministic tests, consider using a **constant** or a **fixture** (e.g., `freezegun` library) to freeze time. |
| Shared test utilities (if any) | Centralise the helper in a single module, e.g., `tests/utils.py`: <br> ```python<br> def utc_now():<br>     return datetime.now(timezone.utc)<br> ``` <br> Then import `utc_now()` everywhere. This eliminates duplication and makes future updates trivial. |

**Why:**  
* Makes datetime objects **timezone‑aware**, preventing hidden bugs when mixing with aware timestamps.  
* Improves **test reproducibility** – deterministic timestamps avoid flaky failures.  

### 4.2. Float Equality Check (MAJOR)  

| File | Recommendation |
|------|----------------|
| `backend/tests/integration/test_dashboard_api.py` | Replace direct `==` with an **approximate comparison** using `math.isclose` (Python 3.5+) or `numpy.testing.assert_allclose` if NumPy is used. Example: <br> ```python<br> assert math.isclose(result, expected, rel_tol=1e-9, abs_tol=0.0)  # adjust tolerance as needed<br> ``` |

**Why:**  
Floating‑point arithmetic can produce tiny rounding differences; `isclose` provides a controlled tolerance and eliminates false negatives.

### 4.3. HTTP Request Payload (BLOCKER)  

| File | Recommendation |
|------|----------------|
| `backend/tests/integration/test_preferences_api.py` | Change the request call from: <br> ```python<br> client.post(url, data=payload)<br> ``` <br> to: <br> ```python<br> client.post(url, content=payload)  # if using httpx or requests‑like API that supports `content`<br> ``` <br> Verify the library’s signature (e.g., `requests.post(..., data=..., json=..., files=...)`). If the library does **not** have a `content` argument, switch to the appropriate parameter (`json=` for JSON bodies). |

**Why:**  
Using the wrong parameter can lead to malformed request bodies, causing API errors that may be hidden in tests.

### 4.4. JavaScript NaN Check (MINOR)  

| File | Recommendation |
|------|----------------|
| `frontend/js/utils.js` | Replace `isNaN(value)` with `Number.isNaN(value)`. Example: <br> ```js<br> if (Number.isNaN(value)) { … }<br> ``` |

**Why:**  
`Number.isNaN` does **not** coerce the argument, providing a reliable check and avoiding false positives (e.g., `isNaN('')` returns `false` vs `true` for non‑numeric strings).

---

## 5. Priority Areas & Actionable Focus  

| Priority | Files to Address | Reason |
|----------|------------------|--------|
| **P1 – Critical (date‑time handling)** | `backend/tests/integration/test_dashboard_api.py` <br> `backend/tests/unit/models/test_metrics_snapshot.py` | 12 × CRITICAL issues; directly affect test reliability and are flagged as **BLOCKER** for production quality. |
| **P2 – Major (float comparison)** | `backend/tests/integration/test_dashboard_api.py` | Single MAJOR issue that can cause flaky test failures. |
| **P3 – Blocker (HTTP payload)** | `backend/tests/integration/test_preferences_api.py` | Incorrect request payload may hide integration bugs. |
| **P4 – Minor (JS NaN check)** | `frontend/js/utils.js` | Minor style issue, easy fix, improves code correctness. |

### Suggested Immediate Steps  

1. **Create a shared datetime helper** (`tests/utils.py`) and replace all `datetime.datetime.utcnow()` calls. Run the test suite to confirm no regressions.  
2. **Update float assertions** to use `math.isclose` (or a test‑framework‑specific matcher).  
3. **Audit all HTTP client calls** in the integration test suite for misuse of `data` vs `content`/`json`.  
4. **Lint the frontend** with an ESLint rule (`prefer-number-isnan`) to automatically catch future `isNaN` usages.  

---  

## 6. Closing Remarks  

The reliability profile is dominated by a single anti‑pattern in test code. By consolidating datetime handling, tightening floating‑point assertions, and correcting request payload usage, the project will eliminate **all CRITICAL** findings and significantly improve test determinism. The remaining issues are low‑effort, isolated fixes that can be addressed in the same cleanup effort.  

---  