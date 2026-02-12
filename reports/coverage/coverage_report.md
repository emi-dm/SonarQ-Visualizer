# Coverage Analysis Report

    This report summarizes current SonarCloud coverage metrics exported to `data/`.

    ## Global Coverage Summary

    | Metric | Value |
    |---|---:|
    | Overall Coverage | 46.50% |
    | Line Coverage | 46.50% |
    | Branch Coverage | 0.00% |
    | Lines to Cover | 1716 |
    | Covered Lines | 798 |
    | Uncovered Lines | 918 |
    | Conditions to Cover | 0 |
    | Covered Conditions | 0 |
    | Uncovered Conditions | 0 |

    ## File-Level Insights

    ### Top 10 archivos con menor cobertura
| Archivo       | Ruta                             |   coverage |   uncovered_lines |   lines_to_cover |
|:--------------|:---------------------------------|-----------:|------------------:|-----------------:|
| schema.sql    | backend/src/db/schema.sql        |          0 |                 3 |                3 |
| __init__.py   | backend/src/__init__.py          |          0 |                 0 |                0 |
| __init__.py   | backend/src/utils/__init__.py    |          0 |                 0 |                0 |
| __init__.py   | backend/src/models/__init__.py   |          0 |                 0 |                0 |
| __init__.py   | backend/src/api/__init__.py      |          0 |                 0 |                0 |
| __init__.py   | backend/src/db/__init__.py       |          0 |                 0 |                0 |
| __init__.py   | backend/src/services/__init__.py |          0 |                 0 |                0 |
| api-client.js | frontend/js/api-client.js        |          0 |                 0 |                0 |
| app.js        | frontend/js/app.js               |          0 |                 0 |                0 |
| charts.js     | frontend/js/charts.js            |          0 |                 0 |                0 |

### Top 10 archivos con más líneas sin cubrir
| Archivo                   | Ruta                                                  |   coverage |   uncovered_lines |   lines_to_cover |
|:--------------------------|:------------------------------------------------------|-----------:|------------------:|-----------------:|
| sonarqube_client.py       | backend/src/services/sonarqube_client.py              |       10.5 |               150 |              174 |
| connections.py            | backend/src/api/connections.py                        |       35.6 |               100 |              162 |
| projects.py               | backend/src/api/projects.py                           |       48.4 |                77 |              153 |
| metrics.py                | backend/src/api/metrics.py                            |       44.5 |                62 |              115 |
| connection_repository.py  | backend/src/db/repositories/connection_repository.py  |       17.7 |                61 |               78 |
| preferences.py            | backend/src/api/preferences.py                        |       28.4 |                61 |               86 |
| project_service.py        | backend/src/services/project_service.py               |       16.7 |                60 |               76 |
| preferences_service.py    | backend/src/services/preferences_service.py           |       18.1 |                51 |               68 |
| project_repository.py     | backend/src/db/repositories/project_repository.py     |       25.8 |                42 |               58 |
| preferences_repository.py | backend/src/db/repositories/preferences_repository.py |       21.9 |                40 |               54 |

    ## Recommendations

    1. Prioritize files with low coverage and high uncovered line counts.
    2. Add targeted unit tests around high-risk logic branches.
    3. Track coverage trend over time to ensure improvements are sustained.
    4. Set minimum coverage gates in SonarCloud to prevent regressions.
    