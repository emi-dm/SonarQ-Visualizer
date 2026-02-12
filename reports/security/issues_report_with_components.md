# SECURITY Issues Analysis Report (With Component Details)

This report was generated using AI analysis of the SonarCloud security issues, including specific component and file information.

# SonarCloud Security Code‑Quality Report  
**Project:** `emi-dm_SonarQ-Visualizer`  
**Date:** 2026‑02‑12  

---

## 1. Summary of Issue Counts & Component Distribution  

| Severity | Total Issues |
|----------|--------------|
| **BLOCKER** | **7** |
| **MINOR**   | **1** |
| **Grand Total** | **8** |

### Issues by Component  

| Component (File) | # of Issues | Severity Breakdown |
|------------------|------------|--------------------|
| `backend/tests/integration/test_connection_validation.py` | **3** | 3 × BLOCKER |
| `scripts/refresh_all_metrics.py` | **1** | 1 × BLOCKER |
| `scripts/test_direct_requests.py` | **1** | 1 × BLOCKER |
| `scripts/test_individual_metrics.py` | **1** | 1 × BLOCKER |
| `scripts/test_metrics.py` | **1** | 1 × BLOCKER |
| `backend/src/api/preferences.py` | **1** | 1 × MINOR |
| **Total** | **8** | 7 × BLOCKER, 1 × MINOR |

> **Observation:** All blocker issues are concentrated in test‑related scripts and one integration test file. The only minor issue lives in the API preferences module.

---

## 2. Top 5 Most Common Issue Types  

| Issue Message (Pattern) | Frequency | Category |
|--------------------------|-----------|----------|
| **Hard‑coded secret – “token”** | 6 | Secret Management |
| **Hard‑coded secret – “TOKEN”** | 1 | Secret Management |
| **Logging user‑controlled data** | 1 | Logging / Data Exposure |
| *(No other distinct messages)* | – | – |

*The “token” messages represent **7/8** (87.5 %) of all findings, making hard‑coded secrets the dominant problem.*

---

## 3. Patterns & Affected Areas  

| Pattern | Description | Affected Files |
|---------|-------------|----------------|
| **Hard‑coded authentication tokens** | Literal strings `"token"` or `"TOKEN"` appear in source code, typically as test fixtures or script constants. SonarCloud flags them as potential secrets that could be committed to the repository. | `scripts/refresh_all_metrics.py`, `scripts/test_direct_requests.py`, `scripts/test_individual_metrics.py`, `scripts/test_metrics.py`, `backend/tests/integration/test_connection_validation.py` (3 occurrences) |
| **Logging of user‑controlled data** | Direct logging of values that originate from request payloads or query parameters without sanitisation. | `backend/src/api/preferences.py` |
| **Test‑code leakage** | The majority of hard‑coded token findings are inside **test** scripts, suggesting that test data (e.g., mock API keys) is being committed. While tests are not shipped to production, they still expose secrets in the repo and can be inadvertently used in CI pipelines. | All `scripts/*.py` and `backend/tests/integration/*.py` files listed above |

### Why These Patterns Matter  

| Risk | Impact |
|------|--------|
| **Hard‑coded secrets** | If the repository is public or accessed by many developers, tokens can be extracted and used to call external services, leading to data breaches, quota exhaustion, or financial loss. |
| **Logging user data** | Logs may be stored long‑term, indexed, or shipped to external log aggregators. Unfiltered user input can lead to credential leakage, injection attacks, or GDPR‑non‑compliance. |
| **Test‑code exposure** | CI/CD pipelines often run with elevated permissions. Exposed test tokens can be harvested by malicious actors who gain read access to the CI logs or artifact storage. |

---

## 4. Component‑Specific Recommendations  

### 4.1 `backend/tests/integration/test_connection_validation.py` (3 BLOCKER)

| Recommendation | Rationale |
|----------------|-----------|
| **Replace literal `"token"` strings with environment‑variable look‑ups** (e.g., `os.getenv("TEST_API_TOKEN")`). | Keeps the token out of source control; CI can inject a safe dummy value. |
| **Externalise test credentials** into a dedicated secrets file that is **git‑ignored** (e.g., `tests/.secrets.yml`). Load it only in test setup. | Allows developers to use real tokens locally while the repo never contains them. |
| **Add a comment or Sonar “NOSONAR” suppression** *only* after the secret is safely externalised, and document why suppression is safe. | Prevents false‑positive noise while keeping the rule active for other files. |
| **Run a pre‑commit hook** (e.g., `detect-secrets`) to catch any new hard‑coded tokens before commit. | Provides a safety net for future contributions. |

### 4.2 `scripts/refresh_all_metrics.py` (1 BLOCKER – “TOKEN”)

| Recommendation | Rationale |
|----------------|-----------|
| **Rename the literal to a constant that reads from a secure source** (`TOKEN = os.getenv("REFRESH_METRICS_TOKEN")`). | Aligns with the same strategy used for tests. |
| **If the script is only used in CI**, store the token in the CI secret store and inject it at runtime. | Avoids persisting the token in the repo. |
| **Document the required environment variable** in the script’s docstring or a `README.md` under a “Setup” section. | Improves onboarding and reduces the temptation to re‑hard‑code. |

### 4.3 `scripts/test_direct_requests.py`, `scripts/test_individual_metrics.py`, `scripts/test_metrics.py` (each 1 BLOCKER)

| Recommendation | Rationale |
|----------------|-----------|
| **Consolidate token handling**: create a small helper module `scripts/_test_secrets.py` that reads the token from env vars. Import it wherever needed. | Centralises secret management and reduces duplication. |
| **Mark the helper module as ignored by Sonar** (e.g., `sonar.exclusions=**/_test_secrets.py`) **only after** it contains no hard‑coded values. | Keeps the rule active for production code while allowing test helpers. |
| **Add unit tests** for the helper to ensure it raises a clear error when the env var is missing, preventing silent failures. | Guarantees that missing secrets are caught early. |

### 4.4 `backend/src/api/preferences.py` (1 MINOR – logging user‑controlled data)

| Recommendation | Rationale |
|----------------|-----------|
| **Sanitise any user‑provided values before logging** – e.g., `logger.info("Preference updated: %s", safe_repr(value))` where `safe_repr` strips or masks PII. | Prevents accidental leakage of sensitive data. |
| **Consider lowering log level** for user‑input events (e.g., `debug` instead of `info`) or remove the log statement if it isn’t needed for production diagnostics. | Reduces the amount of data stored in logs. |
| **Add a unit test** that verifies the logger does not output raw user data. | Guarantees the fix remains in place. |

---

## 5. Priority Areas & Actionable Focus  

| Priority | Files to Address | Why |
|----------|------------------|-----|
| **P1 – Blocker – Hard‑coded Secrets** | `backend/tests/integration/test_connection_validation.py` (3), `scripts/refresh_all_metrics.py`, `scripts/test_direct_requests.py`, `scripts/test_individual_metrics.py`, `scripts/test_metrics.py` | These expose authentication tokens. Immediate remediation prevents credential leakage. |
| **P2 – Minor – Logging of User Data** | `backend/src/api/preferences.py` | While less severe, it can still lead to data exposure and compliance issues. |
| **P3 – Process Improvements** | All test‑related scripts & CI pipeline | Implement secret‑management conventions, pre‑commit checks, and documentation to avoid recurrence. |

### Quick “Start‑Fix” Checklist  

1. **Search & Replace** all literal `"token"` / `"TOKEN"` occurrences with `os.getenv("<NAME>")`.  
2. **Create a `.env.example`** file listing required env vars (e.g., `REFRESH_METRICS_TOKEN=`). Add it to repo; keep real values out of version control.  
3. **Add a `.gitignore` entry** for any local secrets file you introduce (`tests/.secrets*`).  
4. **Update CI configuration** to provide the needed env vars from the secret store.  
5. **Run SonarCloud again** after changes to confirm that the 7 blocker issues are cleared.  

---

## 6. Concluding Remarks  

- **Hard‑coded tokens dominate the security debt** (7/8 issues). Removing them and moving to environment‑based secret handling will resolve the bulk of the risk.  
- The **single logging issue** is minor but should be fixed to maintain good data‑privacy hygiene.  
- By **centralising secret access** and **adding automated detection** (pre‑commit hooks, CI secret scans), the team can prevent future regressions.  

Implement the recommendations above, re‑run the SonarCloud analysis, and verify that the blocker count drops to zero. This will bring the project back into a secure baseline and improve overall code‑quality hygiene.  