"""Unit tests for pipeline/export/export_kpi.py.

Tests the export logic without a real Snowflake connection by mocking
the connector. Verifies CSV format, column headers, row count return,
and error propagation.
"""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.export.export_kpi import (
    _KPI_VIEWS,
    export_view,
    run_export,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cursor(columns: list[str], rows: list[tuple[object, ...]]) -> MagicMock:
    """Return a mock cursor pre-loaded with columns and rows."""
    cursor = MagicMock()
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.description = [(col,) for col in columns]
    cursor.fetchall.return_value = rows
    return cursor


def _make_conn(columns: list[str], rows: list[tuple[object, ...]]) -> MagicMock:
    """Return a mock Snowflake connection backed by a pre-loaded cursor."""
    conn = MagicMock()
    conn.cursor.return_value = _make_cursor(columns, rows)
    return conn


# ---------------------------------------------------------------------------
# export_view
# ---------------------------------------------------------------------------


class TestExportView:
    """Tests for export_view."""

    def test_csv_is_created(self, tmp_path: Path) -> None:
        """A CSV file is written at output_dir/<view_name>.csv."""
        conn = _make_conn(["COL_A", "COL_B"], [(1, "x"), (2, "y")])
        export_view(conn, "VW_TEST", tmp_path)
        assert (tmp_path / "vw_test.csv").exists()

    def test_header_row_matches_columns(self, tmp_path: Path) -> None:
        """The first row of the CSV contains the column names from the cursor."""
        cols = ["PATHOLOGY", "AVG_AGE", "PATIENT_COUNT"]
        conn = _make_conn(cols, [(("Diabète", 55.3, 42))])
        export_view(conn, "VW_AVG_AGE_BY_PATHOLOGY", tmp_path)

        with (tmp_path / "vw_avg_age_by_pathology.csv").open(encoding="utf-8-sig") as fh:
            reader = csv.reader(fh, delimiter=";")
            header = next(reader)
        assert header == cols

    def test_row_count_is_returned(self, tmp_path: Path) -> None:
        """export_view returns the number of data rows written."""
        conn = _make_conn(["A"], [(1,), (2,), (3,)])
        count = export_view(conn, "VW_TEST", tmp_path)
        assert count == 3

    def test_empty_view_writes_header_only(self, tmp_path: Path) -> None:
        """An empty view produces a file with a header and no data rows."""
        conn = _make_conn(["COL_A"], [])
        count = export_view(conn, "VW_EMPTY", tmp_path)
        assert count == 0

        with (tmp_path / "vw_empty.csv").open(encoding="utf-8-sig") as fh:
            lines = fh.readlines()
        assert len(lines) == 1

    def test_semicolon_delimiter(self, tmp_path: Path) -> None:
        """CSV files use semicolons as delimiter (Power BI / Excel FR compatible)."""
        conn = _make_conn(["A", "B"], [(10, 20)])
        export_view(conn, "VW_TEST", tmp_path)
        content = (tmp_path / "vw_test.csv").read_text(encoding="utf-8-sig")
        assert ";" in content

    def test_output_dir_is_created_if_missing(self, tmp_path: Path) -> None:
        """export_view creates the output directory if it does not exist."""
        nested = tmp_path / "deep" / "nested"
        conn = _make_conn(["A"], [(1,)])
        export_view(conn, "VW_TEST", nested)
        assert nested.is_dir()

    def test_sql_query_uses_view_name(self, tmp_path: Path) -> None:
        """The SELECT query targets the correct qualified view name."""
        cursor = _make_cursor(["X"], [(42,)])
        conn = MagicMock()
        conn.cursor.return_value = cursor
        export_view(conn, "VW_AVG_AGE_BY_PATHOLOGY", tmp_path)

        executed_sql: str = cursor.execute.call_args[0][0]
        assert "VW.VW_AVG_AGE_BY_PATHOLOGY" in executed_sql


# ---------------------------------------------------------------------------
# run_export
# ---------------------------------------------------------------------------


class TestRunExport:
    """Tests for run_export."""

    def test_all_six_views_are_exported(self, tmp_path: Path) -> None:
        """run_export produces one CSV file per KPI view."""
        with patch(
            "pipeline.export.export_kpi._get_snowflake_connection",
        ) as mock_conn_factory:
            mock_conn_factory.return_value = _make_conn(["COL"], [(1,)])
            results = run_export(tmp_path)

        assert set(results.keys()) == set(_KPI_VIEWS)

    def test_returns_row_count_per_view(self, tmp_path: Path) -> None:
        """run_export returns a dict mapping view name → row count."""
        with patch(
            "pipeline.export.export_kpi._get_snowflake_connection",
        ) as mock_conn_factory:
            mock_conn_factory.return_value = _make_conn(["COL"], [(1,), (2,)])
            results = run_export(tmp_path)

        assert all(v == 2 for v in results.values())

    def test_connection_is_closed_on_success(self, tmp_path: Path) -> None:
        """The Snowflake connection is always closed after export."""
        mock_conn = _make_conn(["COL"], [])
        with patch(
            "pipeline.export.export_kpi._get_snowflake_connection",
            return_value=mock_conn,
        ):
            run_export(tmp_path)

        mock_conn.close.assert_called_once()

    def test_connection_is_closed_on_error(self, tmp_path: Path) -> None:
        """The Snowflake connection is closed even when export raises."""
        broken_conn = MagicMock()
        broken_conn.cursor.side_effect = RuntimeError("db error")

        with (
            patch(
                "pipeline.export.export_kpi._get_snowflake_connection",
                return_value=broken_conn,
            ),
            pytest.raises(RuntimeError, match="db error"),
        ):
            run_export(tmp_path)

        broken_conn.close.assert_called_once()

    def test_csv_files_are_named_after_views(self, tmp_path: Path) -> None:
        """Each CSV file is named after the lowercase view name."""
        with patch(
            "pipeline.export.export_kpi._get_snowflake_connection",
        ) as mock_conn_factory:
            mock_conn_factory.return_value = _make_conn(["COL"], [])
            run_export(tmp_path)

        expected_files = {f"{v.lower()}.csv" for v in _KPI_VIEWS}
        actual_files = {f.name for f in tmp_path.iterdir() if f.suffix == ".csv"}
        assert actual_files == expected_files
