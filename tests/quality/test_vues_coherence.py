"""Integration tests — VW layer coherence against source flat files.

Each test queries a Snowflake view via snowflake-connector-python and
compares the result against figures derived from the source .txt files.

Run with:
    uv run pytest tests/quality/test_vues_coherence.py -v

Requires env vars: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD,
SNOWFLAKE_DATABASE, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_ROLE (loaded from .env).
"""

from __future__ import annotations

import glob
import os
from collections.abc import Generator

import pandas as pd
import pytest
import snowflake.connector

# ---------------------------------------------------------------------------
# Helpers — read source files
# ---------------------------------------------------------------------------

INPUTS = os.path.join(os.path.dirname(__file__), "..", "..", "inputs", "Data Hospital")


def _source_files(table: str) -> list[str]:
    return sorted(glob.glob(f"{INPUTS}/*/{table}_*.txt"))


def _read_source(table: str) -> pd.DataFrame:
    frames = [pd.read_csv(f, sep=";", dtype=str, encoding="utf-8") for f in _source_files(table)]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ---------------------------------------------------------------------------
# Snowflake fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sf() -> Generator[snowflake.connector.SnowflakeConnection, None, None]:
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        role=os.environ.get("SNOWFLAKE_ROLE", ""),
        schema="VW",
    )
    yield conn
    conn.close()


def _query(conn: snowflake.connector.SnowflakeConnection, sql: str) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0].lower() for d in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)


# ---------------------------------------------------------------------------
# KPI 1 — vw_avg_age_by_pathology
# ---------------------------------------------------------------------------


class TestAvgAgeByPathology:
    """vw_avg_age_by_pathology coherence checks."""

    def test_no_null_columns(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT * FROM vw_avg_age_by_pathology WHERE "
            "pathology_description IS NULL OR patient_id IS NULL "
            "OR report_date IS NULL OR age_at_consultation IS NULL",
        )
        assert df.empty, f"NULLs in key columns: {df.head()}"

    def test_age_positive(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT COUNT(*) AS cnt FROM vw_avg_age_by_pathology WHERE age_at_consultation < 0",
        )
        assert df["cnt"][0] == 0, "Negative ages found"

    def test_report_date_range(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT MIN(report_date) AS mn, MAX(report_date) AS mx FROM vw_avg_age_by_pathology",
        )
        assert str(df["mn"][0]) >= "2026-04-29", f"Date too early: {df['mn'][0]}"
        assert str(df["mx"][0]) <= "2026-05-10", f"Date too late: {df['mx'][0]}"

    def test_patient_ids_exist_in_source(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        src = _read_source("PATIENT")
        src_ids = set(src["ID_PATIENT"].str.strip().dropna())
        df = _query(sf, "SELECT DISTINCT patient_id FROM vw_avg_age_by_pathology")
        view_ids = set(df["patient_id"].astype(str))
        unknown = view_ids - src_ids
        assert not unknown, f"patient_ids not in source: {unknown}"


# ---------------------------------------------------------------------------
# KPI 2 — vw_top_medication_by_pathology
# ---------------------------------------------------------------------------


class TestTopMedicationByPathology:
    """vw_top_medication_by_pathology coherence checks."""

    def test_no_null_columns(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT * FROM vw_top_medication_by_pathology WHERE "
            "pathology_description IS NULL OR medicine_code IS NULL "
            "OR medicine_name IS NULL OR total_quantity IS NULL",
        )
        assert df.empty, f"NULLs in key columns: {df.head()}"

    def test_total_quantity_positive(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT COUNT(*) AS cnt FROM vw_top_medication_by_pathology WHERE total_quantity < 0",
        )
        assert df["cnt"][0] == 0, "Negative quantities found"

    def test_total_quantity_matches_source(
        self, sf: snowflake.connector.SnowflakeConnection
    ) -> None:
        src = _read_source("TRAITEMENT")
        src_total = pd.to_numeric(src["QTE_MEDICAMENT"], errors="coerce").fillna(0).sum()
        df = _query(sf, "SELECT SUM(total_quantity) AS tot FROM vw_top_medication_by_pathology")
        view_total = float(df["tot"][0])
        # Allow small delta: view filters on non-null pathology
        assert view_total <= src_total, f"View total {view_total} exceeds source total {src_total}"
        assert view_total > 0, "Total quantity is 0"

    def test_medicine_codes_exist_in_source(
        self, sf: snowflake.connector.SnowflakeConnection
    ) -> None:
        src = _read_source("TRAITEMENT")
        src_codes = set(src["CD_MEDICAMENT"].str.strip().dropna())
        df = _query(sf, "SELECT DISTINCT medicine_code FROM vw_top_medication_by_pathology")
        view_codes = set(df["medicine_code"].astype(str))
        unknown = view_codes - src_codes
        assert not unknown, f"medicine_codes not in source: {unknown}"


# ---------------------------------------------------------------------------
# KPI 3 — vw_rooms_by_pathology
# ---------------------------------------------------------------------------


class TestRoomsByPathology:
    """vw_rooms_by_pathology coherence checks."""

    def test_no_null_columns(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT * FROM vw_rooms_by_pathology WHERE "
            "pathology_description IS NULL OR room_number IS NULL "
            "OR report_date IS NULL",
        )
        assert df.empty, f"NULLs in key columns: {df.head()}"

    def test_room_count_matches_r_room(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        """Distinct rooms in the view must be a subset of valid rooms in r_room."""
        vw = _query(
            sf,
            "SELECT COUNT(DISTINCT room_number) AS cnt FROM vw_rooms_by_pathology",
        )
        r_room = _query(sf, "SELECT COUNT(*) AS cnt FROM SOC.r_room")
        # Every room in the view must exist in r_room (room 0 filtered out)
        assert int(vw["cnt"][0]) <= int(r_room["cnt"][0]), (
            f"View has {vw['cnt'][0]} rooms, r_room only has {r_room['cnt'][0]}"
        )

    def test_no_invalid_room_zero(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT COUNT(*) AS cnt FROM vw_rooms_by_pathology WHERE room_number = 0",
        )
        assert df["cnt"][0] == 0, "Room 0 (invalid) found in view"

    def test_room_numbers_in_r_room(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT DISTINCT v.room_number FROM vw_rooms_by_pathology AS v "
            "LEFT JOIN SOC.r_room AS r ON v.room_number = r.room_num "
            "WHERE r.room_num IS NULL",
        )
        assert df.empty, f"Rooms in view not in r_room: {df['room_number'].tolist()}"


# ---------------------------------------------------------------------------
# KPI 4 — vw_doctor_speciality_by_pathology
# ---------------------------------------------------------------------------


class TestDoctorSpecialityByPathology:
    """vw_doctor_speciality_by_pathology coherence checks."""

    def test_no_null_columns(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT * FROM vw_doctor_speciality_by_pathology WHERE "
            "pathology_description IS NULL OR staff_id IS NULL "
            "OR specialty IS NULL OR report_date IS NULL",
        )
        assert df.empty, f"NULLs in key columns: {df.head()}"

    def test_staff_ids_exist_in_source(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        src = _read_source("PERSONNEL")
        src_ids = set(src["ID_PERSONNEL"].str.strip().dropna())
        df = _query(sf, "SELECT DISTINCT staff_id FROM vw_doctor_speciality_by_pathology")
        view_ids = set(df["staff_id"].astype(str))
        unknown = view_ids - src_ids
        assert not unknown, f"staff_ids not in source: {unknown}"


# ---------------------------------------------------------------------------
# KPI 5 — vw_patients_one_night
# ---------------------------------------------------------------------------


class TestPatientsOneNight:
    """vw_patients_one_night coherence checks."""

    def test_no_null_columns(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT * FROM vw_patients_one_night WHERE "
            "report_date IS NULL OR total_hospitalisations IS NULL "
            "OR one_night_plus_count IS NULL OR one_night_plus_pct IS NULL",
        )
        assert df.empty, f"NULLs in key columns: {df.head()}"

    def test_pct_not_100(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT MAX(one_night_plus_pct) AS mx, MIN(one_night_plus_pct) AS mn "
            "FROM vw_patients_one_night",
        )
        assert float(df["mx"][0]) < 100.0, (
            "one_night_plus_pct = 100% on all dates — check one-night threshold formula"
        )
        assert float(df["mn"][0]) >= 0.0, "Negative percentage found"

    def test_count_lte_total(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT COUNT(*) AS cnt FROM vw_patients_one_night "
            "WHERE one_night_plus_count > total_hospitalisations",
        )
        assert df["cnt"][0] == 0, "one_night_plus_count > total_hospitalisations"

    def test_total_hospi_matches_source(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        src = _read_source("HOSPITALISATION")
        # Exclude room 0 and apply same quality filters as WRK
        src_valid = src[
            src["ID_HOSPI"].notna()
            & (pd.to_numeric(src["ID_HOSPI"], errors="coerce") > 0)
            & src["ID_CONSULT_hospi"].notna()
            & src["NO_CHAMBRE_hospi"].notna()
            & src["TS_DEBUT_HOSPI"].notna()
            & src["ID_PERSONNEL_RESP"].notna()
        ]
        src_count = len(src_valid.drop_duplicates(subset=["ID_HOSPI"]))
        df = _query(sf, "SELECT SUM(total_hospitalisations) AS tot FROM vw_patients_one_night")
        view_count = int(df["tot"][0])
        assert view_count == src_count, (
            f"Total hospi mismatch: view={view_count}, source={src_count}"
        )


# ---------------------------------------------------------------------------
# KPI 6 — vw_empty_rooms
# ---------------------------------------------------------------------------


class TestEmptyRooms:
    """vw_empty_rooms coherence checks."""

    def test_no_null_columns(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT * FROM vw_empty_rooms WHERE "
            "report_date IS NULL OR room_num IS NULL "
            "OR occupancy_status IS NULL",
        )
        assert df.empty, f"NULLs in key columns: {df.head()}"

    def test_occupancy_status_values(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT DISTINCT occupancy_status FROM vw_empty_rooms "
            "WHERE occupancy_status NOT IN ('Occupée', 'Libre')",
        )
        assert df.empty, f"Unexpected occupancy_status values: {df}"

    def test_room_nums_in_r_room(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        df = _query(
            sf,
            "SELECT DISTINCT v.room_num FROM vw_empty_rooms AS v "
            "LEFT JOIN SOC.r_room AS r ON v.room_num = r.room_num "
            "WHERE r.room_num IS NULL",
        )
        assert df.empty, f"Rooms in view not in r_room: {df['room_num'].tolist()}"

    def test_room_count_matches_r_room(self, sf: snowflake.connector.SnowflakeConnection) -> None:
        vw = _query(sf, "SELECT COUNT(DISTINCT room_num) AS cnt FROM vw_empty_rooms")
        r_room = _query(sf, "SELECT COUNT(*) AS cnt FROM SOC.r_room")
        assert int(vw["cnt"][0]) == int(r_room["cnt"][0]), (
            f"Room count mismatch: view={vw['cnt'][0]}, r_room={r_room['cnt'][0]}"
        )
