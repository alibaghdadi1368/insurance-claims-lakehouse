# Airflow plus the libraries our tasks call.
# dbt gets its own virtual environment so its dependencies can't clash with Airflow's.
FROM apache/airflow:3.3.2-python3.11

COPY airflow/requirements.txt /tmp/requirements.txt
# pin Airflow itself, so pip can't up- or downgrade it while installing our libraries
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /tmp/requirements.txt

RUN python -m venv /opt/airflow/dbt-venv \
    && /opt/airflow/dbt-venv/bin/pip install --no-cache-dir "dbt-snowflake>=1.10,<2.0"
