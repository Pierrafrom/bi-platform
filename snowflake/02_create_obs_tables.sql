USE DATABASE HOPITAL_DW;
USE SCHEMA OBS;

CREATE TABLE IF NOT EXISTS OBS.CHAMBRE (
    NO_CHAMBRE              SMALLINT          NOT NULL,
    NOM_CHAMBRE             VARCHAR(100)      NOT NULL,
    NO_ETAGE                BYTEINT,
    NOM_BATIMENT            VARCHAR(100),
    TYPE_CHAMBRE            VARCHAR(50),
    PRIX_JOUR               SMALLINT          NOT NULL,
    DT_CREATION             DATE              NOT NULL,
    -- Colonnes d'audit
    BATCH_DT                DATE              NOT NULL,
    LOAD_DTTM               TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (NO_CHAMBRE, BATCH_DT)
);

CREATE TABLE IF NOT EXISTS OBS.MEDICAMENT (
    CD_MEDICAMENT           VARCHAR(20)       NOT NULL,
    CATG_MEDICAMENT         VARCHAR(50)       NOT NULL,
    MARQUE_FABRI            VARCHAR(100)      NOT NULL,
    NOM_MEDICAMENT          VARCHAR(200),
    CONDIT_MEDICAMENT       VARCHAR(50),
    BATCH_DT                DATE              NOT NULL,
    LOAD_DTTM               TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (CD_MEDICAMENT, CATG_MEDICAMENT, MARQUE_FABRI, BATCH_DT)
);

CREATE TABLE IF NOT EXISTS OBS.PERSONNEL (
    ID_PERSONNEL            INTEGER           NOT NULL,
    NOM_PERSONNEL           VARCHAR(100)      NOT NULL,
    PRENOM_PERSONNEL        VARCHAR(100)      NOT NULL,
    FONCTION_PERSONNEL      VARCHAR(50)       NOT NULL,
    TS_DEBUT_ACTIVITE       TIMESTAMP         NOT NULL,
    TS_FIN_ACTIVITE         TIMESTAMP,
    RAISON_FIN_ACTIVITE     VARCHAR(200),
    TS_CREATION_PERSONNEL   TIMESTAMP         NOT NULL,
    TS_MAJ_PERSONNEL        TIMESTAMP         NOT NULL,
    CD_STATUT_PERSONNEL     VARCHAR(10)       NOT NULL,
    BATCH_DT                DATE              NOT NULL,
    LOAD_DTTM               TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (ID_PERSONNEL, BATCH_DT)
);

CREATE TABLE IF NOT EXISTS OBS.PATIENT (
    ID_PATIENT              INTEGER           NOT NULL,
    NOM_PATIENT             VARCHAR(100)      NOT NULL,
    PRENOM_PATIENT          VARCHAR(100)      NOT NULL,
    DT_NAISS                DATE,
    VILLE_NAISS             VARCHAR(100),
    PAYS_NAISS              VARCHAR(100),
    NUM_SECU                VARCHAR(20),
    IND_PAYS_NUM_TELP       VARCHAR(5),
    NUM_TELEPHONE           VARCHAR(20),
    NUM_VOIE                VARCHAR(20),
    DSC_VOIE                VARCHAR(100),
    CMPL_VOIE               VARCHAR(100),
    CD_POSTAL               VARCHAR(10),
    VILLE                   VARCHAR(100),
    PAYS                    VARCHAR(100),
    TS_CREATION_PATIENT     TIMESTAMP         NOT NULL,
    TS_MAJ_PATIENT          TIMESTAMP         NOT NULL,
    BATCH_DT                DATE              NOT NULL,
    LOAD_DTTM               TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (ID_PATIENT, BATCH_DT)
);

CREATE TABLE IF NOT EXISTS OBS.CONSULTATION (
    ID_CONSULT              INTEGER           NOT NULL,
    ID_PERSONNEL            INTEGER           NOT NULL,
    ID_PATIENT              INTEGER           NOT NULL,
    TS_DEBUT_CONSULT        TIMESTAMP         NOT NULL,
    TS_FIN_CONSULT          TIMESTAMP         NOT NULL,
    POIDS_PATIENT           INTEGER           NOT NULL,
    TEMP_PATIENT            DECIMAL(5,2),
    UNIT_TEMP               VARCHAR(15),
    TENSION_PATIENT         INTEGER,
    DSC_PATHO               VARCHAR(500),
    INDIC_DIABETE           BOOLEAN,
    ID_TRAITEMENT           INTEGER,
    INDIC_HOSPI             BOOLEAN,
    BATCH_DT                DATE              NOT NULL,
    LOAD_DTTM               TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (ID_CONSULT, BATCH_DT)
);

CREATE TABLE IF NOT EXISTS OBS.TRAITEMENT (
    ID_TRAITEMENT           INTEGER           NOT NULL,
    CD_MEDICAMENT           VARCHAR(20)       NOT NULL,
    CATG_MEDICAMENT         VARCHAR(50)       NOT NULL,
    MARQUE_FABRI            VARCHAR(100)      NOT NULL,
    QTE_MEDICAMENT          SMALLINT,
    DSC_POSOLOGIE           VARCHAR(500)      NOT NULL,
    ID_CONSULT              INTEGER           NOT NULL,
    TS_CREATION_TRAITEMENT  TIMESTAMP         NOT NULL,
    BATCH_DT                DATE              NOT NULL,
    LOAD_DTTM               TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (ID_TRAITEMENT, BATCH_DT)
);

CREATE TABLE IF NOT EXISTS OBS.HOSPITALISATION (
    ID_HOSPI                INTEGER           NOT NULL,
    ID_CONSULT              INTEGER           NOT NULL,
    NO_CHAMBRE              SMALLINT          NOT NULL,
    TS_DEBUT_HOSPI          TIMESTAMP         NOT NULL,
    TS_FIN_HOSPI            TIMESTAMP,
    COUT_HOSPI              DECIMAL(10,2),
    ID_PERSONNEL_RESP       INTEGER           NOT NULL,
    BATCH_DT                DATE              NOT NULL,
    LOAD_DTTM               TIMESTAMP         NOT NULL,
    EXEC_ID                 INTEGER,
    PRIMARY KEY (ID_HOSPI, BATCH_DT)
);

SHOW TABLES IN SCHEMA OBS;
