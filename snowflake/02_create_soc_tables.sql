USE DATABASE HOPITAL_DW;

-- ─────────────────────────────────────────────────────────────────────────
-- SOC tables — CREATE TABLE IF NOT EXISTS (never recreated after deployment).
-- dbt populates these tables on each daily run via the marts layer.
-- ─────────────────────────────────────────────────────────────────────────

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_ROOM — Référentiel des chambres
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_ROOM (
    ROOM_NUM                INTEGER           NOT NULL,
    ROOM_NAME               VARCHAR(100)      NOT NULL,
    FLOR_NUM                SMALLINT,
    BULD_NAME               VARCHAR(100),
    ROOM_TYP                VARCHAR(50),
    ROOM_DAY_RATE           DECIMAL(8, 2)     NOT NULL,
    CRTN_DT                 DATE              NOT NULL,
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (ROOM_NUM)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_MEDC — Référentiel des médicaments
-- PK composite métier : (MEDC_CD, MEDC_CATG, MANF_BRND)
-- MEDC_ID : clé de substitution générée par ROW_NUMBER dans dbt
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_MEDC (
    MEDC_ID                 INTEGER           NOT NULL,
    MEDC_CD                 VARCHAR(20)       NOT NULL,
    MEDC_NAME               VARCHAR(200),
    MEDC_COND               VARCHAR(50),
    MEDC_CATG               VARCHAR(50)       NOT NULL,
    MANF_BRND               VARCHAR(100)      NOT NULL,
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (MEDC_ID),
    UNIQUE (MEDC_CD, MEDC_CATG, MANF_BRND)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_PART — Référentiel des parties (patients + personnel)
-- PART_ID : clé de substitution générée par ROW_NUMBER dans dbt
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_PART (
    PART_ID                 INTEGER           NOT NULL,
    SRC_ID                  INTEGER           NOT NULL,
    SRC_TYP                 VARCHAR(100)      NOT NULL,
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (PART_ID),
    UNIQUE (SRC_TYP, SRC_ID)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_INDIV — Référentiel des patients
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_INDIV (
    INDIV_ID                INTEGER           NOT NULL,
    LAST_NAME               VARCHAR(100)      NOT NULL,
    FIRST_NAME              VARCHAR(100)      NOT NULL,
    SOCIAL_SECURITY_NUMBER  VARCHAR(50),
    BIRTH_DATE              DATE,
    BIRTH_CITY              VARCHAR(100),
    BIRTH_COUNTRY           VARCHAR(100),
    CREATED_AT              TIMESTAMP_NTZ     NOT NULL,
    UPDATED_AT              TIMESTAMP_NTZ     NOT NULL,
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (INDIV_ID)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_STF — Référentiel du personnel
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_STF (
    STAFF_ID                INTEGER           NOT NULL,
    LAST_NAME               VARCHAR(100)      NOT NULL,
    FIRST_NAME              VARCHAR(100)      NOT NULL,
    JOB_TITLE               VARCHAR(100)      NOT NULL,
    WORK_START_AT           TIMESTAMP_NTZ     NOT NULL,
    WORK_END_AT             TIMESTAMP_NTZ,
    WORK_END_REASON         VARCHAR(200),
    STATUS_CODE             VARCHAR(10)       NOT NULL,
    CREATED_AT              TIMESTAMP_NTZ     NOT NULL,
    UPDATED_AT              TIMESTAMP_NTZ     NOT NULL,
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (STAFF_ID)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_ADDR — Adresses postales des patients
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_ADDR (
    INDIV_ID                INTEGER           NOT NULL,
    STREET_NUMBER           VARCHAR(20),
    STREET_NAME             VARCHAR(200),
    ADDRESS_COMPLEMENT      VARCHAR(200),
    POSTAL_CODE             VARCHAR(20),
    CITY                    VARCHAR(100),
    COUNTRY                 VARCHAR(100),
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (INDIV_ID),
    FOREIGN KEY (INDIV_ID) REFERENCES SOC.R_INDIV(INDIV_ID)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_TEL — Numéros de téléphone des patients
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_TEL (
    INDIV_ID                INTEGER           NOT NULL,
    PHONE_COUNTRY_CODE      VARCHAR(10),
    PHONE_NUMBER            VARCHAR(30)       NOT NULL,
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (INDIV_ID),
    FOREIGN KEY (INDIV_ID) REFERENCES SOC.R_INDIV(INDIV_ID)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_TRMT — Traitements prescrits
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_TRMT (
    TREATMENT_ID            INTEGER           NOT NULL,
    CONSULTATION_ID         INTEGER           NOT NULL,
    MEDICINE_CODE           VARCHAR(20)       NOT NULL,
    MEDICINE_CATEGORY       VARCHAR(50)       NOT NULL,
    MANUFACTURER_BRAND      VARCHAR(100)      NOT NULL,
    MEDICINE_QUANTITY       DECIMAL(10, 2),
    DOSAGE_DESCRIPTION      VARCHAR(500)      NOT NULL,
    CREATED_AT              TIMESTAMP_NTZ,
    EXEC_ID                 INTEGER           NOT NULL,
    PRIMARY KEY (TREATMENT_ID)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.R_HOSPI — Hospitalisations
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.R_HOSPI (
    HOSPI_ID                INTEGER           NOT NULL,
    CONSULTATION_ID         INTEGER           NOT NULL,
    ROOM_NUMBER             INTEGER           NOT NULL,
    RESPONSIBLE_STAFF_ID    INTEGER           NOT NULL,
    STARTED_AT              TIMESTAMP_NTZ     NOT NULL,
    ENDED_AT                TIMESTAMP_NTZ,
    COST                    DECIMAL(10, 2),
    EXEC_ID                 INTEGER           NOT NULL,
    DURATION_DAYS           INTEGER,
    PRIMARY KEY (HOSPI_ID),
    FOREIGN KEY (ROOM_NUMBER)          REFERENCES SOC.R_ROOM(ROOM_NUM),
    FOREIGN KEY (RESPONSIBLE_STAFF_ID) REFERENCES SOC.R_STF(STAFF_ID)
);

-- ─────────────────────────────────────────────────────────────────────────
-- SOC.FAIT_CONSULT — Table de faits centrale (consultations)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS SOC.FAIT_CONSULT (
    CONSULTATION_ID         INTEGER           NOT NULL,
    PATIENT_ID              INTEGER           NOT NULL,
    STAFF_ID                INTEGER           NOT NULL,
    TREATMENT_ID            INTEGER,
    STARTED_AT              TIMESTAMP_NTZ     NOT NULL,
    ENDED_AT                TIMESTAMP_NTZ     NOT NULL,
    PATIENT_WEIGHT_KG       DECIMAL(6, 2),
    PATIENT_TEMPERATURE     DECIMAL(5, 2),
    TEMPERATURE_UNIT        VARCHAR(5),
    BLOOD_PRESSURE          VARCHAR(20),
    PATHOLOGY_DESCRIPTION   VARCHAR(500),
    DIABETES_INDICATOR      BOOLEAN,
    HOSPITALISATION_INDICATOR BOOLEAN,
    EXEC_ID                 INTEGER           NOT NULL,
    DURATION_MINUTES        INTEGER,
    PRIMARY KEY (CONSULTATION_ID),
    FOREIGN KEY (PATIENT_ID)   REFERENCES SOC.R_INDIV(INDIV_ID),
    FOREIGN KEY (STAFF_ID)     REFERENCES SOC.R_STF(STAFF_ID),
    FOREIGN KEY (TREATMENT_ID) REFERENCES SOC.R_TRMT(TREATMENT_ID)
);

SHOW TABLES IN SCHEMA SOC;
