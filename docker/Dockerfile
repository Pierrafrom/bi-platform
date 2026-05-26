# Extends the official Airflow image with project-specific dependencies.
# Base image pins both Airflow and Python versions for reproducibility.
FROM apache/airflow:2.10.4-python3.12

# Install additional Python packages needed by our DAGs:
#   dbt-snowflake  — run dbt transformations from BashOperator tasks
#   python-dotenv  — load .env in local dev (no-op in prod)
RUN pip install --no-cache-dir \
    "dbt-snowflake>=1.9" \
    "python-dotenv>=1.0"
