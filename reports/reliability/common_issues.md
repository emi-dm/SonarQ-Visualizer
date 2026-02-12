# Common RELIABILITY Issues Summary

This document contains the counts and statistics of the most common reliability issues.


## Issue Counts Summary

### By Severity:
| Severidad   |   count |
|:------------|--------:|
| CRITICAL    |      12 |
| MAJOR       |       1 |
| BLOCKER     |       1 |
| MINOR       |       1 |

### Top 10 Most Common Issue Messages:
| Mensaje                                                              |   count |
|:---------------------------------------------------------------------|--------:|
| Don't use `datetime.datetime.utcnow` to create this datetime object. |      12 |
| Do not perform equality checks with floating point values.           |       1 |
| Use "content" parameter instead of "data" for bytes or text.         |       1 |
| Prefer `Number.isNaN` over `isNaN`.                                  |       1 |

### Top 10 Components with Issues:
| Componente (Archivo)                                                        |   count |
|:----------------------------------------------------------------------------|--------:|
| emi-dm_SonarQ-Visualizer:backend/tests/integration/test_dashboard_api.py    |       8 |
| emi-dm_SonarQ-Visualizer:backend/tests/unit/models/test_metrics_snapshot.py |       5 |
| emi-dm_SonarQ-Visualizer:backend/tests/integration/test_preferences_api.py  |       1 |
| emi-dm_SonarQ-Visualizer:frontend/js/utils.js                               |       1 |
