"""Unit tests for pipeline/ingest/ingest_stg.py.

Covers pure-function helpers that contain the core logic:
- parse_batch_date
- _safe_identifier
- _typed_expression
- _merge_sql
"""

from __future__ import annotations

import argparse
from datetime import date

import pytest

from pipeline.ingest.ingest_stg import (
    _merge_sql,
    _safe_identifier,
    _typed_expression,
    parse_batch_date,
)


class TestParseBatchDate:
    """Tests for parse_batch_date."""

    def test_happy_path_returns_date(self) -> None:
        """Valid YYYY-MM-DD string is parsed into the correct date.

        Returns:
            None
        """
        result = parse_batch_date("2026-04-29")
        assert result == date(2026, 4, 29)

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "29-04-2026",
            "2026/04/29",
            "20260429",
            "not-a-date",
            "",
        ],
    )
    def test_invalid_format_raises(self, invalid_value: str) -> None:
        """Non-YYYY-MM-DD strings raise ArgumentTypeError.

        Args:
            invalid_value: A string that does not match the expected format.

        Returns:
            None
        """
        with pytest.raises(argparse.ArgumentTypeError):
            parse_batch_date(invalid_value)


class TestSafeIdentifier:
    """Tests for _safe_identifier."""

    def test_valid_identifier_returned_uppercase(self) -> None:
        """A valid lowercase identifier is uppercased and returned.

        Returns:
            None
        """
        assert _safe_identifier("id_patient") == "ID_PATIENT"

    def test_already_uppercase_identifier(self) -> None:
        """An already-uppercase identifier passes through unchanged.

        Returns:
            None
        """
        assert _safe_identifier("NO_CHAMBRE") == "NO_CHAMBRE"

    @pytest.mark.parametrize(
        "bad_identifier",
        [
            "drop table",
            "123_invalid",
            "name;injection",
            "col-name",
            "",
        ],
    )
    def test_invalid_identifier_raises(self, bad_identifier: str) -> None:
        """Identifiers with forbidden characters raise ValueError.

        Args:
            bad_identifier: A string that is not a safe Snowflake identifier.

        Returns:
            None
        """
        with pytest.raises(ValueError):
            _safe_identifier(bad_identifier)

    def test_alphanumeric_with_underscore(self) -> None:
        """Identifiers with letters, digits, and underscores are accepted.

        Returns:
            None
        """
        assert _safe_identifier("TMP_PATIENT_20260429") == "TMP_PATIENT_20260429"


class TestTypedExpression:
    """Tests for _typed_expression.

    Each assertion checks that the SQL fragment returned by _typed_expression
    contains the expected Snowflake conversion function.
    """

    @pytest.mark.parametrize(
        "table, column, expected_fragment",
        [
            # varchar — no conversion function, raw NULLIF expression
            ("PATIENT", "NOM_PATIENT", "NULLIF(NOM_PATIENT, '')"),
            # integer
            ("PATIENT", "ID_PATIENT", "TRY_TO_NUMBER("),
            # decimal
            ("HOSPITALISATION", "COUT_HOSPI", "TRY_TO_DECIMAL("),
            # date
            ("PATIENT", "DT_NAISS", "TRY_TO_DATE("),
            # timestamp
            ("PATIENT", "TS_CREATION_PATIENT", "TRY_TO_TIMESTAMP("),
            # boolean
            ("CONSULTATION", "INDIC_HOSPI", "TRY_TO_BOOLEAN("),
        ],
    )
    def test_returns_correct_sql_fragment(
        self, table: str, column: str, expected_fragment: str
    ) -> None:
        """The expression for each type contains the expected conversion call.

        Args:
            table: Source table name.
            column: Target column name whose type drives the expression.
            expected_fragment: SQL substring that must appear in the result.

        Returns:
            None
        """
        result = _typed_expression(table, column)
        assert expected_fragment in result


class TestMergeSql:
    """Tests for _merge_sql."""

    def test_contains_merge_into(self) -> None:
        """Generated SQL starts with MERGE INTO.

        Returns:
            None
        """
        sql = _merge_sql("TMP_PATIENT_20260429", "PATIENT")
        assert "MERGE INTO" in sql

    def test_contains_when_matched(self) -> None:
        """Generated SQL includes WHEN MATCHED clause.

        Returns:
            None
        """
        sql = _merge_sql("TMP_PATIENT_20260429", "PATIENT")
        assert "WHEN MATCHED" in sql

    def test_contains_when_not_matched(self) -> None:
        """Generated SQL includes WHEN NOT MATCHED clause.

        Returns:
            None
        """
        sql = _merge_sql("TMP_PATIENT_20260429", "PATIENT")
        assert "WHEN NOT MATCHED" in sql

    def test_patient_ts_maj_condition(self) -> None:
        """PATIENT merge includes TS_MAJ_PATIENT freshness guard.

        Returns:
            None
        """
        sql = _merge_sql("TMP_PATIENT_20260429", "PATIENT")
        assert "TS_MAJ_PATIENT" in sql

    def test_non_patient_table_no_ts_maj_condition(self) -> None:
        """Non-PATIENT tables do not include the TS_MAJ_PATIENT guard.

        Returns:
            None
        """
        sql = _merge_sql("TMP_CONSULTATION_20260429", "CONSULTATION")
        assert "TS_MAJ_PATIENT" not in sql

    def test_targets_qualified_table(self) -> None:
        """The target in MERGE INTO is the qualified STG table name.

        Returns:
            None
        """
        sql = _merge_sql("TMP_CONSULTATION_20260429", "CONSULTATION")
        assert "STG.CONSULTATION" in sql
