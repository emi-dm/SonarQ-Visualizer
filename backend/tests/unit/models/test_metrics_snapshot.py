"""Unit tests for MetricsSnapshot model."""

import pytest
from datetime import datetime, timedelta
from backend.src.models.metrics_snapshot import MetricsSnapshot


class TestMetricsSnapshotModel:
    """Test cases for MetricsSnapshot validation and behavior."""

    def test_metrics_snapshot_creation_valid(self):
        """Test creating a metrics snapshot with valid data."""
        analysis_date = datetime.utcnow() - timedelta(hours=1)
        snapshot = MetricsSnapshot(
            project_id=1,
            branch_name="main",
            analysis_date=analysis_date,
            bugs_count=1,
            vulnerabilities_count=2,
            code_smells_count=3,
            coverage_pct=75.5,
            duplications_pct=1.2,
            quality_gate_status="OK",
            severity_breakdown={"blocker": 0, "critical": 1, "major": 2, "minor": 3, "info": 4},
            ncloc=1200
        )

        assert snapshot.project_id == 1
        assert snapshot.branch_name == "main"
        assert snapshot.analysis_date == analysis_date
        assert snapshot.quality_gate_status == "OK"

    def test_negative_counts_invalid(self):
        """Test that negative counts are rejected."""
        analysis_date = datetime.utcnow() - timedelta(hours=1)
        with pytest.raises(ValueError):
            MetricsSnapshot(
                project_id=1,
                branch_name="main",
                analysis_date=analysis_date,
                bugs_count=-1,
                vulnerabilities_count=0,
                code_smells_count=0,
                quality_gate_status="OK"
            )

    def test_coverage_out_of_bounds_invalid(self):
        """Test that coverage percent out of bounds is rejected."""
        analysis_date = datetime.utcnow() - timedelta(hours=1)
        with pytest.raises(ValueError):
            MetricsSnapshot(
                project_id=1,
                branch_name="main",
                analysis_date=analysis_date,
                bugs_count=0,
                vulnerabilities_count=0,
                code_smells_count=0,
                coverage_pct=120.0,
                quality_gate_status="OK"
            )

    def test_quality_gate_status_invalid(self):
        """Test that invalid quality gate status is rejected."""
        analysis_date = datetime.utcnow() - timedelta(hours=1)
        with pytest.raises(ValueError):
            MetricsSnapshot(
                project_id=1,
                branch_name="main",
                analysis_date=analysis_date,
                bugs_count=0,
                vulnerabilities_count=0,
                code_smells_count=0,
                quality_gate_status="INVALID"
            )

    def test_analysis_date_after_fetch_timestamp_invalid(self):
        """Test that analysis_date cannot be after fetch_timestamp."""
        analysis_date = datetime.utcnow() + timedelta(hours=1)
        with pytest.raises(ValueError):
            MetricsSnapshot(
                project_id=1,
                branch_name="main",
                analysis_date=analysis_date,
                bugs_count=0,
                vulnerabilities_count=0,
                code_smells_count=0,
                quality_gate_status="OK"
            )
