import os
import logging

from airflow import DAG
from airflow.utils.dates import days_ago

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator, BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")

path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'citibike_project')


default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="project_gcs_2_bq",
    schedule_interval="@daily",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=['dtc-de'],
) as dag:
    
    #create a folder for all the repos seperately.
    gcs_2_gcs_project_task = GCSToGCSOperator(
        task_id="gcs_2_gcs_project_task",
        source_bucket=BUCKET,
        source_object='new_raw/*.parquet',
        destination_bucket=BUCKET,
        destination_object="new_citi_bike_files/",
        move_object=False,
    )

     #create an External table from the files in the datalake above
    bigquery_external_table_task = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_task",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": "new_citibike_table",
            },
            "externalDataConfiguration": {
                "autodetect": True,
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{BUCKET}/new_raw/*"],
            },
        },
    )



gcs_2_gcs_project_task >> bigquery_external_table_task


#gcs_2_gcs -- helps re-organise our files to a better folder structure
#airflow already provides google integrated libraries