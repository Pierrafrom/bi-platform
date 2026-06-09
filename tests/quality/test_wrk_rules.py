"""Unit tests for pipeline/quality/wrk_rules.py.

Verifies quality-control logic for the WRK (Travail) layer:
- check_consultation
- check_traitement
- check_hospitalisation

Each function is tested for:
- The happy path (all mandatory fields present and valid) → OK
- Each NULL_MANDATORY rejection case
- Each WRONG_FORMAT rejection case
"""

from __future__ import annotations

from datetime import datetime

import pytest

from pipeline.quality.wrk_rules import (
    check_consultation,
    check_hospitalisation,
    check_traitement,
)

_T0 = datetime(2026, 4, 29, 9, 0, 0)
_T1 = datetime(2026, 4, 29, 10, 0, 0)
_T_BEFORE = datetime(2026, 4, 29, 8, 0, 0)


# ---------------------------------------------------------------------------
# check_consultation
# ---------------------------------------------------------------------------


class TestCheckConsultation:
    """Tests for check_consultation."""

    def _valid(self, **overrides: object) -> dict[str, object]:
        """Return a valid consultation row, with optional field overrides.

        Args:
            **overrides: Fields to override in the base valid row.

        Returns:
            Dict representing a complete valid stg_consultation row.
        """
        base: dict[str, object] = {
            "consultation_id": 1,
            "patient_id": 10,
            "staff_id": 20,
            "started_at": _T0,
            "ended_at": _T1,
        }
        return {**base, **overrides}

    def test_valid_row_is_ok(self) -> None:
        """A fully valid row returns OK with no rejection code.

        Returns:
            None
        """
        assert check_consultation(self._valid()) == ("OK", None)

    def test_valid_row_without_ended_at_is_ok(self) -> None:
        """ended_at is optional — omitting it still produces OK.

        Returns:
            None
        """
        assert check_consultation(self._valid(ended_at=None)) == ("OK", None)

    def test_null_consultation_id_is_rejected(self) -> None:
        """Missing consultation_id triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_consultation(self._valid(consultation_id=None)) == ("REJ", "NULL_MANDATORY")

    def test_zero_consultation_id_is_rejected(self) -> None:
        """consultation_id == 0 triggers WRONG_FORMAT.

        Returns:
            None
        """
        assert check_consultation(self._valid(consultation_id=0)) == ("REJ", "WRONG_FORMAT")

    def test_negative_consultation_id_is_rejected(self) -> None:
        """Negative consultation_id triggers WRONG_FORMAT.

        Returns:
            None
        """
        assert check_consultation(self._valid(consultation_id=-5)) == ("REJ", "WRONG_FORMAT")

    def test_null_patient_id_is_rejected(self) -> None:
        """Missing patient_id triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_consultation(self._valid(patient_id=None)) == ("REJ", "NULL_MANDATORY")

    def test_null_staff_id_is_rejected(self) -> None:
        """Missing staff_id triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_consultation(self._valid(staff_id=None)) == ("REJ", "NULL_MANDATORY")

    def test_null_started_at_is_rejected(self) -> None:
        """Missing started_at triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_consultation(self._valid(started_at=None)) == ("REJ", "NULL_MANDATORY")

    def test_ended_before_started_is_rejected(self) -> None:
        """ended_at < started_at triggers WRONG_FORMAT.

        Returns:
            None
        """
        assert check_consultation(self._valid(ended_at=_T_BEFORE)) == ("REJ", "WRONG_FORMAT")

    def test_ended_equal_started_is_ok(self) -> None:
        """ended_at == started_at is valid (zero-duration consultation).

        Returns:
            None
        """
        assert check_consultation(self._valid(ended_at=_T0)) == ("OK", None)


# ---------------------------------------------------------------------------
# check_traitement
# ---------------------------------------------------------------------------


class TestCheckTraitement:
    """Tests for check_traitement."""

    def _valid(self, **overrides: object) -> dict[str, object]:
        """Return a valid treatment row, with optional field overrides.

        Args:
            **overrides: Fields to override in the base valid row.

        Returns:
            Dict representing a complete valid stg_traitement row.
        """
        base: dict[str, object] = {
            "treatment_id": 1,
            "consultation_id": 10,
            "medicine_code": "MED001",
            "medicine_category": "ANALGESIQUE",
            "manufacturer_brand": "BRAND_A",
        }
        return {**base, **overrides}

    def test_valid_row_is_ok(self) -> None:
        """A fully valid row returns OK with no rejection code.

        Returns:
            None
        """
        assert check_traitement(self._valid()) == ("OK", None)

    def test_null_treatment_id_is_rejected(self) -> None:
        """Missing treatment_id triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_traitement(self._valid(treatment_id=None)) == ("REJ", "NULL_MANDATORY")

    def test_zero_treatment_id_is_rejected(self) -> None:
        """treatment_id == 0 triggers WRONG_FORMAT.

        Returns:
            None
        """
        assert check_traitement(self._valid(treatment_id=0)) == ("REJ", "WRONG_FORMAT")

    @pytest.mark.parametrize(
        "field",
        ["consultation_id", "medicine_code", "medicine_category", "manufacturer_brand"],
    )
    def test_null_mandatory_field_is_rejected(self, field: str) -> None:
        """Any NULL mandatory field triggers NULL_MANDATORY.

        Args:
            field: Name of the mandatory field to set to None.

        Returns:
            None
        """
        assert check_traitement(self._valid(**{field: None})) == ("REJ", "NULL_MANDATORY")

    def test_optional_fields_can_be_null(self) -> None:
        """medicine_quantity and dosage_description are optional.

        Returns:
            None
        """
        row = self._valid()
        row["medicine_quantity"] = None
        row["dosage_description"] = None
        assert check_traitement(row) == ("OK", None)


# ---------------------------------------------------------------------------
# check_hospitalisation
# ---------------------------------------------------------------------------


class TestCheckHospitalisation:
    """Tests for check_hospitalisation."""

    def _valid(self, **overrides: object) -> dict[str, object]:
        """Return a valid hospitalisation row, with optional field overrides.

        Args:
            **overrides: Fields to override in the base valid row.

        Returns:
            Dict representing a complete valid stg_hospitalisation row.
        """
        base: dict[str, object] = {
            "hospi_id": 1,
            "consultation_id": 10,
            "room_number": 101,
            "started_at": _T0,
            "ended_at": _T1,
            "cost": 350.0,
        }
        return {**base, **overrides}

    def test_valid_row_is_ok(self) -> None:
        """A fully valid row returns OK with no rejection code.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid()) == ("OK", None)

    def test_valid_row_without_ended_at_is_ok(self) -> None:
        """Ongoing stays (no ended_at) are valid.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(ended_at=None)) == ("OK", None)

    def test_valid_row_without_cost_is_ok(self) -> None:
        """Missing cost is allowed.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(cost=None)) == ("OK", None)

    def test_null_hospi_id_is_rejected(self) -> None:
        """Missing hospi_id triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(hospi_id=None)) == ("REJ", "NULL_MANDATORY")

    def test_zero_hospi_id_is_rejected(self) -> None:
        """hospi_id == 0 triggers WRONG_FORMAT.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(hospi_id=0)) == ("REJ", "WRONG_FORMAT")

    def test_null_consultation_id_is_rejected(self) -> None:
        """Missing consultation_id triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(consultation_id=None)) == (
            "REJ",
            "NULL_MANDATORY",
        )

    def test_null_room_number_is_rejected(self) -> None:
        """Missing room_number triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(room_number=None)) == ("REJ", "NULL_MANDATORY")

    def test_null_started_at_is_rejected(self) -> None:
        """Missing started_at triggers NULL_MANDATORY.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(started_at=None)) == ("REJ", "NULL_MANDATORY")

    def test_ended_before_started_is_rejected(self) -> None:
        """ended_at < started_at triggers WRONG_FORMAT.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(ended_at=_T_BEFORE)) == ("REJ", "WRONG_FORMAT")

    def test_negative_cost_is_rejected(self) -> None:
        """Negative cost triggers WRONG_FORMAT.

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(cost=-10.0)) == ("REJ", "WRONG_FORMAT")

    def test_zero_cost_is_ok(self) -> None:
        """Zero cost is valid (free stay).

        Returns:
            None
        """
        assert check_hospitalisation(self._valid(cost=0.0)) == ("OK", None)
