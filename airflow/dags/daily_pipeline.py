"""
One run per business day:

    generate --> upload_to_s3 ----------------------> copy_into_bronze --> dbt_build --> export_demo
             \-> produce_claims --> consume_claims -/
"""

from datetime import datetime, timedelta
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT = "/opt/project"
DBT = "/opt/airflow/dbt-venv/bin/dbt"
DBT_ARGS = f"--project-dir {PROJECT}/dbt --profiles-dir {PROJECT}/dbt"

def step(task_id, command):
    return BashOperator(task_id=task_id, bash_command=f"cd {PROJECT} && {command}")

with DAG(
    dag_id="daily_insurance_pipeline",
    start_date=datetime(2026, 10, 1),
    schedule="@daily",
    catchup=False, # missed days are not replayed; the next run just adds one day
    max_active_runs=1, # one business day at a time
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["insurance"],
) as dag:
    generate = step("generate", "python -m generator daily")
    upload = step("upload_to_s3", "python -m pipeline.s3_upload --date latest")
    produce = step("produce_claims", "python -m streaming.producer")
    consume = step("consume_claims", "python -m streaming.consumer --stop-when-idle 20")
    copy = step("copy_into_bronze", "python -m pipeline.bronze_load")
    # build runs models, snapshots and tests in dependency order
    build = step("dbt_build", f"{DBT} build {DBT_ARGS}")
    export = step("export_demo", "python -m pipeline.export_demo")

    generate >> [upload, produce]
    produce >> consume
    [upload, consume] >> copy >> build >> export
