USE DATABASE HOPITAL_DW;
USE SCHEMA TCH;

-- ─────────────────────────────────────────────────────────────────────────
-- T_SUIV_RUN: Une exécution complète de la chaîne
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS TCH.T_SUIV_RUN (
    RUN_ID                  INTEGER IDENTITY(1,1) PRIMARY KEY,
    RUN_STRT_DTTM           TIMESTAMP         NOT NULL,
    RUN_END_DTTM            TIMESTAMP,
    RUN_STTS_CD             VARCHAR(10)       NOT NULL,  -- ENC / OK / KO
    -- Métadonnées optionnelles
    RUN_TYP                 VARCHAR(50),      -- INSTALL / DAILY / MANUAL
    BATCH_DT                DATE              -- Date du batch traité (si applicable)
);

-- ─────────────────────────────────────────────────────────────────────────
-- T_SUIV_TRMT: Chaque script/tâche à l'intérieur d'un run
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS TCH.T_SUIV_TRMT (
    EXEC_ID                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    RUN_ID                  INTEGER           NOT NULL,  -- FK → T_SUIV_RUN
    SCRPT_NAME              VARCHAR(250)      NOT NULL,  -- Nom du script/tâche
    EXEC_STRT_DTTM          TIMESTAMP         NOT NULL,
    EXEC_END_DTTM           TIMESTAMP,
    EXEC_STTS_CD            VARCHAR(10)       NOT NULL,  -- ENC / OK / KO
    ERR_MSG                 VARCHAR(2000),               -- Message d'erreur si KO
    FOREIGN KEY (RUN_ID) REFERENCES TCH.T_SUIV_RUN(RUN_ID)
);

SHOW TABLES IN SCHEMA TCH;
