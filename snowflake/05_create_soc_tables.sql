USE DATABASE HOPITAL_DW;
USE SCHEMA SOC;

-- ─────────────────────────────────────────────────────────────────────────
-- COUCHE SOC — Party Model
--
-- Ces tables sont gérées par dbt (materialized=table, recréées chaque run).
-- Ce script est exécuté UNE SEULE FOIS par install_sid.py.
-- Les tables SOC et TCH ne sont PAS recréées si elles existent déjà
-- (CREATE TABLE IF NOT EXISTS).
--
-- Règle surrogate key : PART_ID (R_PART) et MEDC_ID (R_MEDC) sont des
-- séquences incrémentales calculées par dbt via ROW_NUMBER().
-- Ne JAMAIS utiliser IDENTITY sur ces colonnes.
-- ─────────────────────────────────────────────────────────────────────────

-- ─────────────────────────────────────────────────────────────────────────
-- TABLES DE RÉFÉRENCE (R_)
-- ─────────────────────────────────────────────────────────────────────────

-- R_PART : référentiel unifié des tiers (patients + personnel)
-- PART_ID : surrogate key calculée par dbt ROW_NUMBER() sur (SRC_ID, SRC_TYP)
CREATE TABLE IF NOT EXISTS SOC.R_PART (
    PART_ID                 INTEGER           NOT NULL PRIMARY KEY,
    SRC_ID                  INTEGER           NOT NULL,   -- ID_PATIENT ou ID_PERSONNEL
    SRC_TYP                 VARCHAR(100)      NOT NULL,   -- 'Patient' ou FONCTION_PERSONNEL
    EXEC_ID                 INTEGER
);

-- R_ROOM : référentiel des chambres
-- ROOM_NUM est la clé naturelle source — pas de surrogate key
CREATE TABLE IF NOT EXISTS SOC.R_ROOM (
    ROOM_NUM                SMALLINT          NOT NULL PRIMARY KEY,
    ROOM_NAME               VARCHAR(20),
    FLOR_NUM                BYTEINT,
    BULD_NAME               VARCHAR(20),
    ROOM_TYP                VARCHAR(10),
    ROOM_DAY_RATE           SMALLINT,
    CRTN_DT                 DATE,
    EXEC_ID                 INTEGER
);

-- R_MEDC : référentiel des médicaments
-- MEDC_ID : surrogate key calculée par dbt ROW_NUMBER() sur (MEDC_CD, MEDC_CATG, MANF_BRND)
CREATE TABLE IF NOT EXISTS SOC.R_MEDC (
    MEDC_ID                 INTEGER           NOT NULL PRIMARY KEY,
    MEDC_CD                 VARCHAR(10)       NOT NULL,
    MEDC_NAME               VARCHAR(250),
    MEDC_COND               VARCHAR(100),
    MEDC_CATG               VARCHAR(100)      NOT NULL,
    MANF_BRND               VARCHAR(100)      NOT NULL,
    EXEC_ID                 INTEGER
);

-- ─────────────────────────────────────────────────────────────────────────
-- TABLES D'OCCURRENCE (O_) — Faits et satellites
-- ─────────────────────────────────────────────────────────────────────────

-- O_INDV : détails individuels des tiers (nom, prénom, statut, naissance…)
-- PART_ID = FK → R_PART, aussi PK (une ligne par tiers)
CREATE TABLE IF NOT EXISTS SOC.O_INDV (
    PART_ID                 INTEGER           NOT NULL PRIMARY KEY,
    INDV_NAME               VARCHAR(100),
    INDV_FIRS_NAME          VARCHAR(100),
    INDV_STTS_CD            VARCHAR(50),
    CRTN_DTTM               TIMESTAMP,
    UPDT_DTTM               TIMESTAMP,
    BIRT_DT                 DATE,
    BIRT_CITY               VARCHAR(100),
    BIRT_CNTR               VARCHAR(100),
    SOCL_NUM                VARCHAR(15),
    EXEC_ID                 INTEGER
);

-- O_STFF : données RH du personnel (période d'activité, raison de départ)
-- PART_ID = FK → R_PART (personnel uniquement)
CREATE TABLE IF NOT EXISTS SOC.O_STFF (
    PART_ID                 INTEGER           NOT NULL PRIMARY KEY,
    WORK_STRT_DTTM          TIMESTAMP,
    WORK_END_DTTM           TIMESTAMP,
    WORK_END_RESN           VARCHAR(100),
    EXEC_ID                 INTEGER
);

-- O_TELP : téléphones des patients (historisé par date de validité)
-- PK composite : (PART_ID, STRT_VALD_DTTM)
CREATE TABLE IF NOT EXISTS SOC.O_TELP (
    PART_ID                 INTEGER           NOT NULL,
    STRT_VALD_DTTM          TIMESTAMP         NOT NULL,
    CNTR_IND                VARCHAR(5),
    TELP_NUM                VARCHAR(20),
    END_VALD_DTTM           TIMESTAMP,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (PART_ID, STRT_VALD_DTTM)
);

-- O_ADDR : adresses des patients (historisé par date de validité)
-- PK composite : (PART_ID, STRT_VALD_DTTM)
CREATE TABLE IF NOT EXISTS SOC.O_ADDR (
    PART_ID                 INTEGER           NOT NULL,
    STRT_VALD_DTTM          TIMESTAMP         NOT NULL,
    STRT_NUM                VARCHAR(10),
    STRT_DSC                VARCHAR(250),
    COMP_STRT               VARCHAR(250),
    POST_CD                 VARCHAR(10),
    CITY_NAME               VARCHAR(100),
    CNTR_NAME               VARCHAR(100),
    END_VALD_DTTM           TIMESTAMP,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (PART_ID, STRT_VALD_DTTM)
);

-- O_CONS : consultations
-- CONS_ID = clé naturelle source
CREATE TABLE IF NOT EXISTS SOC.O_CONS (
    CONS_ID                 INTEGER           NOT NULL PRIMARY KEY,
    STFF_ID                 INTEGER,                     -- FK → R_PART (médecin)
    PATN_ID                 INTEGER,                     -- FK → R_PART (patient)
    CONS_STRT_DTTM          TIMESTAMP,
    CONS_END_DTTM           TIMESTAMP,
    PATN_WEGH               INTEGER,
    PATN_TEMP               INTEGER,                     -- température brute (°C ou °F selon source)
    TEMP_UNIT               VARCHAR(15),                 -- 'C' ou 'F'
    BLD_PRSS                INTEGER,
    PATH_DSC                VARCHAR(250),
    DIBT_IND                BYTEINT,                     -- 1 = diabétique, 0 = non
    TRET_ID                 INTEGER,                     -- FK → O_TRET
    HOSP_IND                BYTEINT,                     -- 1 = hospitalisé, 0 = non
    EXEC_ID                 INTEGER
);

-- O_TRET : traitements prescrits
-- TRET_ID = clé naturelle source
CREATE TABLE IF NOT EXISTS SOC.O_TRET (
    TRET_ID                 INTEGER           NOT NULL PRIMARY KEY,
    MEDC_ID                 INTEGER,                     -- FK → R_MEDC
    MEDC_QTY                SMALLINT,
    DOSG_DSC                VARCHAR(100),
    CONS_ID                 INTEGER,                     -- FK → O_CONS
    TRET_CRTN_DTTM          TIMESTAMP,
    EXEC_ID                 INTEGER
);

-- O_HOSP : hospitalisations
-- HOSP_ID = clé naturelle source
CREATE TABLE IF NOT EXISTS SOC.O_HOSP (
    HOSP_ID                 INTEGER           NOT NULL PRIMARY KEY,
    CONS_ID                 INTEGER,                     -- FK → O_CONS
    ROOM_NUM                SMALLINT,                    -- FK → R_ROOM
    HOSP_STRT_DTTM          TIMESTAMP,
    HOSP_END_DTTM           TIMESTAMP,
    HOSP_FINL_RATE          DECIMAL(10,2),
    STFF_ID                 INTEGER,                     -- FK → R_PART (responsable)
    EXEC_ID                 INTEGER
);

SHOW TABLES IN SCHEMA SOC;
