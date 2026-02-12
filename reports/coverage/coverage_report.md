# Coverage Analysis Report

This report summarizes current SonarCloud coverage metrics exported to `data/`.

## Global Coverage Summary

| Metric | Value |
|---|---:|
| Overall Coverage | 0.00% |
| Line Coverage | 0.00% |
| Branch Coverage | 0.00% |
| Lines to Cover | 3331 |
| Covered Lines | 0 |
| Uncovered Lines | 3331 |
| Conditions to Cover | 0 |
| Covered Conditions | 0 |
| Uncovered Conditions | 0 |

## File-Level Insights

### Top 10 archivos con menor cobertura
| Archivo                       | Ruta                                                    |   coverage |   uncovered_lines |   lines_to_cover |
|:------------------------------|:--------------------------------------------------------|-----------:|------------------:|-----------------:|
| app.js                        | frontend/js/app.js                                      |          0 |               485 |              485 |
| sonarqube_client.py           | backend/src/services/sonarqube_client.py                |          0 |               172 |              172 |
| connections.py                | backend/src/api/connections.py                          |          0 |               130 |              130 |
| test_dashboard_api.py         | backend/tests/integration/test_dashboard_api.py         |          0 |               121 |              121 |
| projects.py                   | backend/src/api/projects.py                             |          0 |               109 |              109 |
| test_preferences_api.py       | backend/tests/integration/test_preferences_api.py       |          0 |               100 |              100 |
| utils.js                      | frontend/js/utils.js                                    |          0 |                96 |               96 |
| metrics.py                    | backend/src/api/metrics.py                              |          0 |                89 |               89 |
| charts.js                     | frontend/js/charts.js                                   |          0 |                86 |               86 |
| test_connection_validation.py | backend/tests/integration/test_connection_validation.py |          0 |                84 |               84 |

### Top 10 archivos con más líneas sin cubrir
| Archivo                       | Ruta                                                    |   coverage |   uncovered_lines |   lines_to_cover |
|:------------------------------|:--------------------------------------------------------|-----------:|------------------:|-----------------:|
| app.js                        | frontend/js/app.js                                      |          0 |               485 |              485 |
| sonarqube_client.py           | backend/src/services/sonarqube_client.py                |          0 |               172 |              172 |
| connections.py                | backend/src/api/connections.py                          |          0 |               130 |              130 |
| test_dashboard_api.py         | backend/tests/integration/test_dashboard_api.py         |          0 |               121 |              121 |
| projects.py                   | backend/src/api/projects.py                             |          0 |               109 |              109 |
| test_preferences_api.py       | backend/tests/integration/test_preferences_api.py       |          0 |               100 |              100 |
| utils.js                      | frontend/js/utils.js                                    |          0 |                96 |               96 |
| metrics.py                    | backend/src/api/metrics.py                              |          0 |                89 |               89 |
| charts.js                     | frontend/js/charts.js                                   |          0 |                86 |               86 |
| test_connection_validation.py | backend/tests/integration/test_connection_validation.py |          0 |                84 |               84 |

## Recommendations

1. Prioritize files with low coverage and high uncovered line counts.
2. Add targeted unit tests around high-risk logic branches.
3. Track coverage trend over time to ensure improvements are sustained.
4. Set minimum coverage gates in SonarCloud to prevent regressions.
