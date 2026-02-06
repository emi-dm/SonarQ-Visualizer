"""Property-based tests for SonarQube API response parsing."""

import pytest
from hypothesis import given, strategies as st
from backend.src.services.sonarqube_client import parse_projects_response, parse_measures_response
from backend.src.utils.errors import InvalidAPIResponseError


@st.composite
def project_entries(draw):
    key = draw(st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')), min_size=1, max_size=50))
    name = draw(st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Zs')), min_size=1, max_size=100))
    description = draw(st.one_of(st.none(), st.text(min_size=0, max_size=200)))
    analysis_date = draw(st.one_of(st.none(), st.datetimes()))
    return {
        "key": key,
        "name": name,
        "description": description,
        "analysisDate": analysis_date.isoformat() if analysis_date else None
    }


@st.composite
def measures_response(draw):
    measures = []
    numeric_str = st.integers(min_value=0, max_value=100000).map(str)
    percent_str = st.floats(min_value=0, max_value=100).map(lambda v: f"{v:.2f}")

    metrics = {
        "bugs": numeric_str,
        "vulnerabilities": numeric_str,
        "code_smells": numeric_str,
        "ncloc": numeric_str,
        "coverage": percent_str,
        "duplicated_lines_density": percent_str,
        "alert_status": st.sampled_from(["OK", "WARN", "ERROR"])
    }

    for metric, strategy in metrics.items():
        value = draw(st.one_of(st.none(), strategy))
        if value is not None:
            measures.append({"metric": metric, "value": value})

    analysis_date = draw(st.one_of(st.none(), st.datetimes()))
    return {
        "component": {
            "key": draw(st.text(min_size=1, max_size=50)),
            "analysisDate": analysis_date.isoformat() if analysis_date else None,
            "measures": measures
        }
    }


class TestSonarQubeParsingProperties:
    """Property-based tests for SonarQube response parsing."""

    @given(st.lists(project_entries(), min_size=1, max_size=20))
    def test_parse_projects_response_valid(self, components):
        response = {
            "components": components,
            "paging": {"pageIndex": 1, "pageSize": len(components), "total": len(components)}
        }
        parsed = parse_projects_response(response)
        assert len(parsed) == len(components)
        assert all("project_key" in p and "name" in p for p in parsed)

    def test_parse_projects_response_invalid(self):
        with pytest.raises(InvalidAPIResponseError):
            parse_projects_response({"bad": "data"})

    @given(measures_response())
    def test_parse_measures_response_valid(self, response):
        parsed = parse_measures_response(response)
        assert "bugs_count" in parsed
        assert "vulnerabilities_count" in parsed
        assert "code_smells_count" in parsed

    def test_parse_measures_response_invalid(self):
        with pytest.raises(InvalidAPIResponseError):
            parse_measures_response({"component": {"key": "proj"}})
