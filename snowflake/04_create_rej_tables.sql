USE DATABASE HOPITAL_DW;
USE SCHEMA REJ;

CREATE TABLE IF NOT EXISTS REJ.REJ_RECORD (
    REJ_ID                  INTEGER           PRIMARY KEY,
    SRC_TABLE               VARCHAR(50)       NOT NULL,  -- PATIENT, CONSULTATION, etc
    SRC_PK_VAL              VARCHAR(500),                -- Valeur PK en texte
    BATCH_DT                DATE,
    WRK_STTS_CD             VARCHAR(3),       -- 'REJ'
    REJ_COD                 VARCHAR(20)       NOT NULL,  -- NULL_MANDATORY, DUPLICATE_PK, etc
    REJ_DSC                 VARCHAR(500),                -- Description libre
    SRC_ROW_JSON            VARIANT,                     -- Ligne complète en JSON
    REJ_DTTM                TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    RECYCL_IND              BYTEINT,          -- 0 = non recyclée, 1 = recyclée
    RECYCL_DTTM             TIMESTAMP,
    RECYCL_EXEC_ID          INTEGER
);

ALTER TABLE REJ.REJ_RECORD CLUSTER BY (SRC_TABLE, BATCH_DT);
 
SHOW TABLES IN SCHEMA REJ;