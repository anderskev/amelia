"""Tests for WorkflowRepository usage trend methods."""

from datetime import UTC, date, datetime

import pytest

from amelia.server.database.connection import Database
from amelia.server.database.repository import WorkflowRepository
from amelia.server.models.state import ServerExecutionState, rebuild_server_execution_state
from amelia.server.models.tokens import TokenUsage


# Rebuild state models to resolve forward references
rebuild_server_execution_state()


class TestUsageTrend:
    """Tests for get_usage_trend with per-model breakdown."""

    @pytest.fixture
    async def db_with_token_usage(
        self, db_with_schema: Database
    ) -> Database:
        """Create database with token usage data across multiple days and models.

        Creates test data with:
        - 3 days of data (Jan 15-17, 2026)
        - Multiple models per day
        - Multiple workflows

        Returns:
            Database with token usage records.
        """
        repo = WorkflowRepository(db_with_schema)

        # Create workflows
        wf1 = ServerExecutionState(
            id="wf-usage-1",
            issue_id="ISSUE-1",
            worktree_path="/tmp/test-usage-1",
            workflow_status="completed",
            started_at=datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC),
        )
        wf2 = ServerExecutionState(
            id="wf-usage-2",
            issue_id="ISSUE-2",
            worktree_path="/tmp/test-usage-2",
            workflow_status="completed",
            started_at=datetime(2026, 1, 16, 10, 0, 0, tzinfo=UTC),
        )
        wf3 = ServerExecutionState(
            id="wf-usage-3",
            issue_id="ISSUE-3",
            worktree_path="/tmp/test-usage-3",
            workflow_status="completed",
            started_at=datetime(2026, 1, 17, 10, 0, 0, tzinfo=UTC),
        )
        await repo.create(wf1)
        await repo.create(wf2)
        await repo.create(wf3)

        # Day 1 (Jan 15): wf1 with sonnet and opus
        await repo.save_token_usage(
            TokenUsage(
                workflow_id="wf-usage-1",
                agent="architect",
                model="claude-sonnet-4-20250514",
                input_tokens=1000,
                output_tokens=500,
                cost_usd=0.01,
                duration_ms=5000,
                num_turns=3,
                timestamp=datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC),
            )
        )
        await repo.save_token_usage(
            TokenUsage(
                workflow_id="wf-usage-1",
                agent="developer",
                model="claude-opus-4-20250514",
                input_tokens=2000,
                output_tokens=1000,
                cost_usd=0.05,
                duration_ms=10000,
                num_turns=5,
                timestamp=datetime(2026, 1, 15, 11, 0, 0, tzinfo=UTC),
            )
        )

        # Day 2 (Jan 16): wf2 with sonnet only
        await repo.save_token_usage(
            TokenUsage(
                workflow_id="wf-usage-2",
                agent="architect",
                model="claude-sonnet-4-20250514",
                input_tokens=1500,
                output_tokens=700,
                cost_usd=0.015,
                duration_ms=6000,
                num_turns=4,
                timestamp=datetime(2026, 1, 16, 10, 0, 0, tzinfo=UTC),
            )
        )
        await repo.save_token_usage(
            TokenUsage(
                workflow_id="wf-usage-2",
                agent="developer",
                model="claude-sonnet-4-20250514",
                input_tokens=2500,
                output_tokens=1200,
                cost_usd=0.025,
                duration_ms=12000,
                num_turns=6,
                timestamp=datetime(2026, 1, 16, 11, 0, 0, tzinfo=UTC),
            )
        )

        # Day 3 (Jan 17): wf3 with opus only
        await repo.save_token_usage(
            TokenUsage(
                workflow_id="wf-usage-3",
                agent="architect",
                model="claude-opus-4-20250514",
                input_tokens=3000,
                output_tokens=1500,
                cost_usd=0.08,
                duration_ms=15000,
                num_turns=7,
                timestamp=datetime(2026, 1, 17, 10, 0, 0, tzinfo=UTC),
            )
        )

        return db_with_schema

    async def test_get_usage_trend_includes_by_model(
        self, db_with_token_usage: Database
    ) -> None:
        """get_usage_trend should include per-model breakdown."""
        repo = WorkflowRepository(db_with_token_usage)

        trend = await repo.get_usage_trend(
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 17),
        )

        # Check that by_model is included
        for point in trend:
            assert "by_model" in point
            assert isinstance(point["by_model"], dict)

    async def test_get_usage_trend_by_model_has_correct_costs(
        self, db_with_token_usage: Database
    ) -> None:
        """by_model breakdown should have correct per-model costs."""
        repo = WorkflowRepository(db_with_token_usage)

        trend = await repo.get_usage_trend(
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 17),
        )

        # Find Jan 15 data point (has both sonnet and opus)
        jan15 = next(p for p in trend if p["date"] == "2026-01-15")
        assert "claude-sonnet-4-20250514" in jan15["by_model"]
        assert "claude-opus-4-20250514" in jan15["by_model"]
        assert jan15["by_model"]["claude-sonnet-4-20250514"] == pytest.approx(
            0.01, rel=1e-6
        )
        assert jan15["by_model"]["claude-opus-4-20250514"] == pytest.approx(
            0.05, rel=1e-6
        )

        # Find Jan 16 data point (sonnet only)
        jan16 = next(p for p in trend if p["date"] == "2026-01-16")
        assert "claude-sonnet-4-20250514" in jan16["by_model"]
        assert "claude-opus-4-20250514" not in jan16["by_model"]
        assert jan16["by_model"]["claude-sonnet-4-20250514"] == pytest.approx(
            0.04, rel=1e-6  # 0.015 + 0.025
        )

        # Find Jan 17 data point (opus only)
        jan17 = next(p for p in trend if p["date"] == "2026-01-17")
        assert "claude-opus-4-20250514" in jan17["by_model"]
        assert "claude-sonnet-4-20250514" not in jan17["by_model"]
        assert jan17["by_model"]["claude-opus-4-20250514"] == pytest.approx(
            0.08, rel=1e-6
        )

    async def test_get_usage_trend_by_model_empty_for_no_data(
        self, db_with_schema: Database
    ) -> None:
        """by_model should be empty dict when no usage data exists."""
        repo = WorkflowRepository(db_with_schema)

        trend = await repo.get_usage_trend(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
        )

        # Should return empty list since no data exists
        assert trend == []

    async def test_get_usage_trend_totals_still_correct(
        self, db_with_token_usage: Database
    ) -> None:
        """Adding by_model should not change existing cost_usd totals."""
        repo = WorkflowRepository(db_with_token_usage)

        trend = await repo.get_usage_trend(
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 17),
        )

        # Verify original fields still present and correct
        jan15 = next(p for p in trend if p["date"] == "2026-01-15")
        assert jan15["cost_usd"] == pytest.approx(0.06, rel=1e-6)  # 0.01 + 0.05
        assert jan15["workflows"] == 1

        jan16 = next(p for p in trend if p["date"] == "2026-01-16")
        assert jan16["cost_usd"] == pytest.approx(0.04, rel=1e-6)  # 0.015 + 0.025
        assert jan16["workflows"] == 1

        jan17 = next(p for p in trend if p["date"] == "2026-01-17")
        assert jan17["cost_usd"] == pytest.approx(0.08, rel=1e-6)
        assert jan17["workflows"] == 1
