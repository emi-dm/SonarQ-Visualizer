"""Property-based tests for metrics aggregation."""

from hypothesis import given, strategies as st
from backend.src.services.metrics_service import aggregate_metrics


@st.composite
def snapshot_dicts(draw):
    """Generate snapshot-like dictionaries for aggregation."""
    count = draw(st.integers(min_value=0, max_value=100))
    bugs = draw(st.integers(min_value=0, max_value=1000))
    vulns = draw(st.integers(min_value=0, max_value=1000))
    smells = draw(st.integers(min_value=0, max_value=1000))
    coverage = draw(st.one_of(st.none(), st.floats(min_value=0, max_value=100)))
    duplications = draw(st.one_of(st.none(), st.floats(min_value=0, max_value=100)))

    return {
        "bugs_count": bugs,
        "vulnerabilities_count": vulns,
        "code_smells_count": smells,
        "coverage_pct": coverage,
        "duplications_pct": duplications
    }


class TestMetricsAggregationProperties:
    """Property-based tests for aggregation helpers."""

    @given(st.lists(snapshot_dicts(), min_size=1, max_size=50))
    def test_aggregate_metrics_sums_and_averages(self, snapshots):
        """Aggregates should match sum and average of inputs."""
        result = aggregate_metrics(snapshots)

        assert result["total_bugs"] == sum(s["bugs_count"] for s in snapshots)
        assert result["total_vulnerabilities"] == sum(s["vulnerabilities_count"] for s in snapshots)
        assert result["total_code_smells"] == sum(s["code_smells_count"] for s in snapshots)

        coverage_values = [s["coverage_pct"] for s in snapshots if s["coverage_pct"] is not None]
        if coverage_values:
            expected_avg = sum(coverage_values) / len(coverage_values)
            assert result["avg_coverage"] == expected_avg
        else:
            assert result["avg_coverage"] is None

        duplication_values = [s["duplications_pct"] for s in snapshots if s["duplications_pct"] is not None]
        if duplication_values:
            expected_avg = sum(duplication_values) / len(duplication_values)
            assert result["avg_duplications"] == expected_avg
        else:
            assert result["avg_duplications"] is None
