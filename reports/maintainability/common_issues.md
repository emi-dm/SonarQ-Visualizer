# Common MAINTAINABILITY Issues Summary

This document contains the counts and statistics of the most common maintainability issues.


## Issue Counts Summary

### By Severity:
| Severidad   |   count |
|:------------|--------:|
| BLOCKER     |      19 |
| MAJOR       |      15 |
| CRITICAL    |      15 |
| MINOR       |      12 |

### Top 10 Most Common Issue Messages:
| Mensaje                                                                              |   count |
|:-------------------------------------------------------------------------------------|--------:|
| Use "Annotated" type hints for FastAPI dependency injection                          |      17 |
| Add replacement fields or use a normal string instead of an f-string.                |      13 |
| Don't use `datetime.datetime.utcnow` to create this datetime object.                 |      12 |
| Unexpected negated condition.                                                        |       6 |
| Handle this exception or don't catch it at all.                                      |       2 |
| Prefer `childNode.remove()` over `parentNode.removeChild(childNode)`.                |       1 |
| Refactor this function to reduce its Cognitive Complexity from 17 to the 15 allowed. |       1 |
| Use "content" parameter instead of "data" for bytes or text.                         |       1 |
| Refactor this function to reduce its Cognitive Complexity from 22 to the 15 allowed. |       1 |
| Refactor this method to not always return the same value.                            |       1 |

### Top 10 Components with Issues:
| Componente (Archivo)                                                        |   count |
|:----------------------------------------------------------------------------|--------:|
| emi-dm_SonarQ-Visualizer:backend/src/api/dashboard.py                       |       7 |
| emi-dm_SonarQ-Visualizer:backend/tests/integration/test_dashboard_api.py    |       7 |
| emi-dm_SonarQ-Visualizer:frontend/js/app.js                                 |       6 |
| emi-dm_SonarQ-Visualizer:backend/tests/unit/models/test_metrics_snapshot.py |       5 |
| emi-dm_SonarQ-Visualizer:backend/src/api/metrics.py                         |       4 |
| emi-dm_SonarQ-Visualizer:backend/src/api/projects.py                        |       4 |
| emi-dm_SonarQ-Visualizer:scripts/test_individual_metrics.py                 |       4 |
| emi-dm_SonarQ-Visualizer:scripts/test_sonarcloud_access.py                  |       4 |
| emi-dm_SonarQ-Visualizer:frontend/js/utils.js                               |       4 |
| emi-dm_SonarQ-Visualizer:scripts/verify_dashboard.py                        |       3 |
