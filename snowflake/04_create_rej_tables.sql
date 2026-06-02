USE DATABASE HOPITAL_DW;
USE SCHEMA REJ;

-- ─────────────────────────────────────────────────────────────────────────
-- REJ.REJ_RECORD — Table centrale des rejets (toutes sources confondues)
--
-- Gérée par dbt (materialized=incremental).
-- Ce script est exécuté UNE SEULE FOIS par install_sid.py.
-- REJ_ID : surrogate key calculée par dbt_utils.generate_surrogate_key()
--          → VARCHAR(64), jamais IDENTITY.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS REJ.REJ_RECORD (
    REJ_ID                  VARCHAR(64)       NOT NULL PRIMARY KEY, -- hash dbt_utils
    SRC_TABLE               VARCHAR(50)       NOT NULL,             -- PATIENT, CONSULTATION…
    SRC_PK_VAL              VARCHAR(500),                           -- PK source sérialisée en texte
    BATCH_DT                DATE,
    WRK_STTS_CD             VARCHAR(3),                             -- toujours 'REJ'
    REJ_COD                 VARCHAR(20)       NOT NULL,             -- NULL_MANDATORY, DUPLICATE_PK…
    REJ_DSC                 VARCHAR(500),
    SRC_ROW_JSON            VARCHAR,                                -- ligne source complète en JSON
    REJ_DTTM                TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    RECYCL_IND              BYTEINT,                                -- 0 = non recyclée, 1 = recyclée
    RECYCL_DTTM             TIMESTAMP,
    RECYCL_EXEC_ID          INTEGER
);

ALTER TABLE REJ.REJ_RECORD CLUSTER BY (SRC_TABLE, BATCH_DT);

SHOW TABLES IN SCHEMA REJ;
