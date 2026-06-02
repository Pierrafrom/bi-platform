USE DATABASE HOPITAL_DW;
USE SCHEMA SOC;

-- ─────────────────────────────────────────────────────────────────────────
-- DIMENSIONS
-- ─────────────────────────────────────────────────────────────────────────

-- R_PART: Dimension Party (Patients + Personnel unifiés)
CREATE TABLE IF NOT EXISTS SOC.R_PART (
    PART_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    PART_ID                 VARCHAR(50)       NOT NULL,     -- ID source (ID_PATIENT ou ID_PERSONNEL)
    PART_TYP                VARCHAR(20)       NOT NULL,     -- PATIENT / PERSONNEL / AUTRE
    NOM                     VARCHAR(100),
    PRENOM                  VARCHAR(100),
    DT_NAISS                DATE,
    TS_CRT                  TIMESTAMP,
    TS_MAJ                  TIMESTAMP,
    EXEC_ID                 INTEGER
);

-- R_ROOM: Dimension Chambre
CREATE TABLE IF NOT EXISTS SOC.R_ROOM (
    ROOM_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    ROOM_ID                 SMALLINT          NOT NULL,
    NOM_CHAMBRE             VARCHAR(100),
    NO_ETAGE                BYTEINT,
    NOM_BATIMENT            VARCHAR(100),
    TYPE_CHAMBRE            VARCHAR(50),
    PRIX_JOUR               SMALLINT,
    EXEC_ID                 INTEGER
);

-- R_MEDC: Dimension Médicament
CREATE TABLE IF NOT EXISTS SOC.R_MEDC (
    MEDC_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    CD                      VARCHAR(20)       NOT NULL,
    CATG                    VARCHAR(50)       NOT NULL,
    MARQUE                  VARCHAR(100)      NOT NULL,
    NOM                     VARCHAR(200),
    CONDIT                  VARCHAR(50),
    EXEC_ID                 INTEGER
);

-- ─────────────────────────────────────────────────────────────────────────
-- FAITS (Occurrences)
-- ─────────────────────────────────────────────────────────────────────────

-- O_CONS: Consultations (Fait)
CREATE TABLE IF NOT EXISTS SOC.O_CONS (
    CONS_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    CONS_ID                 INTEGER           NOT NULL,
    PART_SK_PATIENT         INTEGER,          -- FK → R_PART (patient)
    PART_SK_MEDECIN         INTEGER,          -- FK → R_PART (médecin)
    TS_DEBUT                TIMESTAMP,
    TS_FIN                  TIMESTAMP,
    POIDS_KG                INTEGER,
    TEMP_C                  DECIMAL(5,2),     -- Normalisée en °C
    DIBT_IND                BYTEINT,          -- Diabète: 1/0
    HOSP_IND                BYTEINT,          -- Hospitalisation: 1/0
    DSC_PATHO               VARCHAR(500),
    TENSION                 INTEGER,
    EXEC_ID                 INTEGER
);

-- O_TRET: Traitements (Fait)
CREATE TABLE IF NOT EXISTS SOC.O_TRET (
    TRET_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    TRET_ID                 INTEGER           NOT NULL,
    CONS_SK                 INTEGER,          -- FK → O_CONS
    MEDC_SK                 INTEGER,          -- FK → R_MEDC
    QTE                     SMALLINT,
    DSC_POSOLOGIE           VARCHAR(500),
    TS_CRT                  TIMESTAMP,
    EXEC_ID                 INTEGER
);

-- O_HOSP: Hospitalisations (Fait)
CREATE TABLE IF NOT EXISTS SOC.O_HOSP (
    HOSP_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    HOSP_ID                 INTEGER           NOT NULL,
    CONS_SK                 INTEGER,          -- FK → O_CONS
    ROOM_SK                 INTEGER,          -- FK → R_ROOM
    PART_SK_RESP            INTEGER,          -- FK → R_PART (responsable)
    TS_DEBUT                TIMESTAMP,
    TS_FIN                  TIMESTAMP,
    COUT                    DECIMAL(10,2),
    EXEC_ID                 INTEGER
);

-- ─────────────────────────────────────────────────────────────────────────
-- TABLES SATELLITES (Données additionnelles)
-- ─────────────────────────────────────────────────────────────────────────

-- O_ADDR: Adresses
CREATE TABLE IF NOT EXISTS SOC.O_ADDR (
    ADDR_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    PART_SK                 INTEGER,          -- FK → R_PART
    NUM_VOIE                VARCHAR(20),
    DSC_VOIE                VARCHAR(100),
    CMPL_VOIE               VARCHAR(100),
    CD_POSTAL               VARCHAR(10),
    VILLE                   VARCHAR(100),
    PAYS                    VARCHAR(100),
    EXEC_ID                 INTEGER
);

-- O_TELP: Téléphones
CREATE TABLE IF NOT EXISTS SOC.O_TELP (
    TELP_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    PART_SK                 INTEGER,          -- FK → R_PART
    IND_PAYS                VARCHAR(5),
    NUM_TELP                VARCHAR(20),
    EXEC_ID                 INTEGER
);

-- O_INDV: Détails individuels (patients)
CREATE TABLE IF NOT EXISTS SOC.O_INDV (
    INDV_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    PART_SK                 INTEGER,          -- FK → R_PART (patient only)
    DT_NAISS                DATE,
    VILLE_NAISS             VARCHAR(100),
    PAYS_NAISS              VARCHAR(100),
    NUM_SECU                VARCHAR(20),
    EXEC_ID                 INTEGER
);

-- O_STFF: Staff (personnels)
CREATE TABLE IF NOT EXISTS SOC.O_STFF (
    STFF_SK                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    PART_SK                 INTEGER,          -- FK → R_PART (personnel only)
    FONCTION                VARCHAR(50),
    TS_DEBUT_ACTV           TIMESTAMP,
    TS_FIN_ACTV             TIMESTAMP,
    RAISON_FIN              VARCHAR(200),
    CD_STATUT               VARCHAR(10),
    EXEC_ID                 INTEGER
);

SHOW TABLES IN SCHEMA SOC;
