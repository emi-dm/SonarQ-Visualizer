# RELIABILITY Issues Analysis Report (With Component Details)

This report was generated using AI analysis of the SonarCloud reliability issues, including specific component and file information.

# 📊 SonarCloud Reliability Issues – EMI‑DM SonarQ‑Visualizer  

*Analysis date: 2026‑02‑12*  

---  

## 1️⃣ Summary of Issue Counts & Component Distribution  

| Severity | Total Issues |
|----------|--------------|
| **CRITICAL** | **12** |
| **MAJOR**    | 1 |
| **BLOCKER**  | 1 |
| **MINOR**    | 1 |
| **TOTAL**    | **15** |

### Issues by Component (file)

| Component (file) | # Issues | Breakdown (severity) |
|------------------|----------|----------------------|
| **backend/tests/integration/test_dashboard_api.py** | **8** | 7 × CRITICAL (`datetime.utcnow`), 1 × MAJOR (float equality) |
| **backend/tests/unit/models/test_metrics_snapshot.py** | **5** | 5 × CRITICAL (`datetime.utcnow`) |
| **backend/tests/integration/test_preferences_api.py** | **1** | 1 × BLOCKER (use `content` instead of `data`) |
| **frontend/js/utils.js** | **1** | 1 × MINOR (prefer `Number.isNaN`) |

> **Observation:** 13 / 15 (≈ 87 %) of all reliability findings are **CRITICAL** and stem from the same rule: *“Don’t use `datetime.datetime.utcnow` to create this datetime object.”*  
> The two test suites (`test_dashboard_api.py` and `test_metrics_snapshot.py`) account for **13** of the 15 findings.

---

## 2️⃣ Top 5 Most Common Issue Types  

| Issue Message (rule) | Frequency | Severity |
|----------------------|-----------|----------|
| **Don’t use `datetime.datetime.utcnow` to create this datetime object.** | **12** | CRITICAL |
| Do not perform equality checks with floating point values. | 1 | MAJOR |
| Use `"content"` parameter instead of `"data"` for bytes or text. | 1 | BLOCKER |
| Prefer `Number.isNaN` over `isNaN`. | 1 | MINOR |
| *(No other distinct messages)* | – | – |

*The “datetime.utcnow” rule alone represents **80 %** of all issues.*

---

## 3️⃣ Patterns & Categories  

| Category | Description | Affected Files |
|----------|-------------|----------------|
| **Timezone‑aware datetime handling** | Use of `datetime.datetime.utcnow()` creates naïve UTC datetimes, which can lead to bugs when mixing with timezone‑aware objects. SonarCloud flags this as a reliability risk. | `backend/tests/integration/test_dashboard_api.py` (7 occurrences) <br> `backend/tests/unit/models/test_metrics_snapshot.py` (5 occurrences) |
| **Floating‑point comparison** | Direct equality (`==`) on floats can be nondeterministic due to rounding errors. | `backend/tests/integration/test_dashboard_api.py` (1 occurrence) |
| **HTTP request payload API misuse** | In the Python `requests` library, `data=` sends form‑encoded data; for raw bytes or JSON strings the `content=` (or `json=`) parameter is safer. | `backend/tests/integration/test_preferences_api.py` (1 occurrence) |
| **JavaScript NaN check** | `isNaN` performs coercion; `Number.isNaN` is stricter and avoids false positives. | `frontend/js/utils.js` (1 occurrence) |

**Key pattern:** All critical findings are concentrated in **test code** (unit & integration). Production code does not appear in this slice, but the same anti‑pattern may exist elsewhere.

---

## 4️⃣ Specific Recommendations  

### 4.1. Fixing the `datetime.datetime.utcnow` anti‑pattern  

| File | Recommended Change | Rationale |
|------|--------------------|-----------|
| `backend/tests/integration/test_dashboard_api.py` | Replace every `datetime.datetime.utcnow()` with `datetime.datetime.now(datetime.timezone.utc)` **or** use `datetime.datetime.fromtimestamp(time.time(), tz=datetime.timezone.utc)`. If the test only needs a deterministic timestamp, consider using a fixed `datetime` fixture or `freezegun`. | Produces a **timezone‑aware** UTC datetime, eliminating naïve‑datetime bugs and satisfying SonarCloud’s rule. |
| `backend/tests/unit/models/test_metrics_snapshot.py` | Same replacement as above. If the test creates many timestamps, factor the logic into a helper function (e.g., `def utc_now(): return datetime.datetime.now(datetime.timezone.utc)`) and reuse it. | Centralises the fix, reduces duplication, and makes future updates easier. |

**Additional tip:**  
- Add a **project‑wide utility** (e.g., `utils/datetime.py`) exposing `utc_now()` and import it in tests and production code. This prevents re‑introducing the pattern.  

### 4.2. Floating‑point Equality  

| File | Recommended Change |
|------|--------------------|
| `backend/tests/integration/test_dashboard_api.py` | Replace `assert value == expected` with `assert math.isclose(value, expected, rel_tol=1e-9, abs_tol=0.0)` (or `pytest.approx`). | Guarantees reliable comparison across platforms and avoids flaky tests. |

### 4.3. HTTP Request Payload (`content` vs `data`)  

| File | Recommended Change |
|------|--------------------|
| `backend/tests/integration/test_preferences_api.py` | If sending raw JSON or bytes, switch from `requests.post(..., data=payload)` to `requests.post(..., json=payload)` **or** `content=payload` (depending on the library). | Aligns with the library’s API, prevents accidental encoding, and resolves the BLOCKER issue. |

### 4.4. JavaScript `Number.isNaN`  

| File | Recommended Change |
|------|--------------------|
| `frontend/js/utils.js` | Replace `isNaN(value)` with `Number.isNaN(value)`. If the code intentionally wants the coercion behaviour, add a comment explaining why; otherwise, use the stricter check. | Removes the minor reliability warning and follows modern ECMAScript best practices. |

---

## 5️⃣ Priority Areas & Files Needing Immediate Attention  

| Priority | File | Reason |
|----------|------|--------|
| **🚨 Critical – Immediate** | `backend/tests/integration/test_dashboard_api.py` (8 issues) | Highest concentration of CRITICAL findings; test failures may be flaky or produce hidden timezone bugs. |
| **🚨 Critical – Immediate** | `backend/tests/unit/models/test_metrics_snapshot.py` (5 issues) | Same anti‑pattern, repeated across multiple test cases. |
| **⚠️ Blocker** | `backend/tests/integration/test_preferences_api.py` (1 issue) | BLOCKER severity – the request may be sending malformed payloads, potentially breaking API contracts. |
| **⚠️ Minor** | `frontend/js/utils.js` (1 issue) | Minor but easy to fix; improves JavaScript reliability. |
| **⚠️ Major** | `backend/tests/integration/test_dashboard_api.py` (float equality) | Only one occurrence, but fixing prevents flaky assertions. |

### Actionable Checklist  

1. **Create a shared UTC helper** (`utils/datetime.py`) and replace all `datetime.utcnow()` calls in the two test files.  
2. **Run the test suite** after the replacement to ensure no behavioural change (the helper returns the same value as before, just timezone‑aware).  
3. **Update floating‑point assertions** to use `math.isclose` or `pytest.approx`.  
4. **Correct the HTTP request** in `test_preferences_api.py` to use `content=` (or `json=`) as appropriate.  
5. **Patch `frontend/js/utils.js`** to use `Number.isNaN`.  
6. **Re‑run SonarCloud analysis** to verify that the 15 issues are cleared.  

---  

## 6️⃣ Closing Remarks  

- The overwhelming majority of reliability findings are **test‑code specific** and revolve around **timezone‑aware datetime creation**.  
- Addressing the UTC helper once will eliminate the current 12 CRITICAL issues and guard against future regressions.  
- The remaining non‑critical issues are isolated, low‑effort fixes that improve code correctness and API usage.  

By applying the recommendations above, the project will move from **15 reliability findings (including a BLOCKER)** to a clean SonarCloud state, reducing the risk of hidden bugs in both test and production code.