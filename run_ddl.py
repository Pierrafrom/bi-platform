"""Execute all Snowflake DDL setup scripts in order."""

import os

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    role=os.getenv("SNOWFLAKE_ROLE"),
)

scripts = [
    "snowflake/00_create_databases.sql",
    "snowflake/01_create_stg_tables.sql",
    "snowflake/02_create_soc_tables.sql",
    "snowflake/06_create_tch_tables.sql",
]

for path in scripts:
    print(f"\n--- {path} ---")
    with open(path) as fh:
        sql = fh.read()
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    cur = conn.cursor()
    for stmt in statements:
        try:
            cur.execute(stmt)
            print(f"  OK: {stmt[:80].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"  ERR: {e}")
    cur.close()

conn.close()
print("\nDone.")
