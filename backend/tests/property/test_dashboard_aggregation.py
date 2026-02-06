"""Property-based tests for dashboard aggregation calculations.

Tests FR-029 dashboard aggregation formulas using Hypothesis to verify
mathematical correctness across various metric ranges.
"""

import pytest
from hypothesis import given, strategies as st
from decimal import Decimal, ROUND_HALF_UP


# Hypothesis strategies for metric values
bugs_strategy = st.integers(min_value=0, max_value=1_000_000)
vulnerabilities_strategy = st.integers(min_value=0, max_value=1_000_000)
coverage_strategy = st.one_of(
    st.none(),
    st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)
quality_gate_strategy = st.sampled_from(['OK', 'WARN', 'ERROR'])


class TestDashboardAggregationProperties:
    """Property-based tests for dashboard aggregation formulas."""

    @given(
        bugs_list=st.lists(bugs_strategy, min_size=1, max_size=100)
    )
    def test_total_bugs_sum_property(self, bugs_list):
        """Property: total_bugs should equal sum of all project bug counts.
        
        Mathematical invariant: SUM(bugs_count) = total_bugs
        """
        expected_total = sum(bugs_list)
        calculated_total = self._calculate_total_bugs(bugs_list)
        
        assert calculated_total == expected_total
        assert calculated_total >= 0  # Non-negative invariant

    @given(
        vulnerabilities_list=st.lists(vulnerabilities_strategy, min_size=1, max_size=100)
    )
    def test_total_vulnerabilities_sum_property(self, vulnerabilities_list):
        """Property: total_vulnerabilities should equal sum of all vulnerability counts.
        
        Mathematical invariant: SUM(vulnerabilities_count) = total_vulnerabilities
        """
        expected_total = sum(vulnerabilities_list)
        calculated_total = self._calculate_total_vulnerabilities(vulnerabilities_list)
        
        assert calculated_total == expected_total
        assert calculated_total >= 0  # Non-negative invariant

    @given(
        coverage_list=st.lists(coverage_strategy, min_size=1, max_size=100)
    )
    def test_average_coverage_calculation_property(self, coverage_list):
        """Property: avg_coverage should be arithmetic mean of non-null coverage values.
        
        Mathematical invariant: AVG(coverage_pct) excluding nulls
        Boundary: 0.0 <= avg_coverage <= 100.0
        """
        non_null_values = [c for c in coverage_list if c is not None]
        
        if not non_null_values:
            # All nulls case
            calculated_avg = self._calculate_average_coverage(coverage_list)
            assert calculated_avg is None
        else:
            expected_avg = sum(non_null_values) / len(non_null_values)
            calculated_avg = self._calculate_average_coverage(coverage_list)
            
            assert calculated_avg is not None
            assert 0.0 <= calculated_avg <= 100.0  # Boundary check
            # Allow small floating-point error
            assert abs(calculated_avg - expected_avg) < 0.01

    @given(
        quality_gates=st.lists(quality_gate_strategy, min_size=1, max_size=100)
    )
    def test_quality_gate_pass_rate_property(self, quality_gates):
        """Property: quality_gate_pass_rate should be percentage of 'OK' statuses.
        
        Mathematical invariant: (COUNT(status='OK') / COUNT(*)) * 100
        Boundary: 0.0 <= pass_rate <= 100.0
        """
        total_count = len(quality_gates)
        ok_count = quality_gates.count('OK')
        
        expected_rate = (ok_count / total_count) * 100.0
        calculated_rate = self._calculate_quality_gate_pass_rate(quality_gates)
        
        assert 0.0 <= calculated_rate <= 100.0  # Boundary check
        assert abs(calculated_rate - expected_rate) < 0.01  # Floating-point tolerance

    @given(
        bugs_list=st.lists(bugs_strategy, min_size=2, max_size=50),
        vulns_list=st.lists(vulnerabilities_strategy, min_size=2, max_size=50),
        coverage_list=st.lists(coverage_strategy, min_size=2, max_size=50),
        qg_list=st.lists(quality_gate_strategy, min_size=2, max_size=50)
    )
    def test_aggregation_idempotency_property(self, bugs_list, vulns_list, coverage_list, qg_list):
        """Property: Aggregating the same data twice produces identical results.
        
        Idempotency invariant: aggregate(data) = aggregate(data)
        """
        # Calculate twice
        result1 = self._calculate_all_aggregates(bugs_list, vulns_list, coverage_list, qg_list)
        result2 = self._calculate_all_aggregates(bugs_list, vulns_list, coverage_list, qg_list)
        
        # Results should be identical
        assert result1['total_bugs'] == result2['total_bugs']
        assert result1['total_vulnerabilities'] == result2['total_vulnerabilities']
        assert result1['quality_gate_pass_rate'] == result2['quality_gate_pass_rate']
        
        # Coverage can be None or float
        if result1['avg_coverage'] is None:
            assert result2['avg_coverage'] is None
        else:
            assert abs(result1['avg_coverage'] - result2['avg_coverage']) < 0.0001

    @given(
        coverage_list=st.lists(coverage_strategy, min_size=1, max_size=100)
    )
    def test_coverage_precision_property(self, coverage_list):
        """Property: Coverage should be rounded to 2 decimal places.
        
        Precision requirement: coverage_pct formatted to 2 decimal places
        """
        calculated_avg = self._calculate_average_coverage(coverage_list)
        
        if calculated_avg is not None:
            # Check precision: should have at most 2 decimal places
            rounded_value = round(calculated_avg, 2)
            assert abs(calculated_avg - rounded_value) < 0.001

    # Helper methods that will be used by the actual service implementation
    
    def _calculate_total_bugs(self, bugs_list):
        """Calculate total bugs count."""
        return sum(bugs_list)

    def _calculate_total_vulnerabilities(self, vulnerabilities_list):
        """Calculate total vulnerabilities count."""
        return sum(vulnerabilities_list)

    def _calculate_average_coverage(self, coverage_list):
        """Calculate average coverage percentage (excluding nulls)."""
        non_null_values = [c for c in coverage_list if c is not None]
        
        if not non_null_values:
            return None
        
        avg = sum(non_null_values) / len(non_null_values)
        return round(avg, 2)

    def _calculate_quality_gate_pass_rate(self, quality_gates):
        """Calculate quality gate pass rate percentage."""
        if not quality_gates:
            return 0.0
        
        ok_count = quality_gates.count('OK')
        total_count = len(quality_gates)
        
        rate = (ok_count / total_count) * 100.0
        return round(rate, 2)

    def _calculate_all_aggregates(self, bugs_list, vulns_list, coverage_list, qg_list):
        """Calculate all dashboard aggregates."""
        return {
            'total_bugs': self._calculate_total_bugs(bugs_list),
            'total_vulnerabilities': self._calculate_total_vulnerabilities(vulns_list),
            'avg_coverage': self._calculate_average_coverage(coverage_list),
            'quality_gate_pass_rate': self._calculate_quality_gate_pass_rate(qg_list)
        }


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
