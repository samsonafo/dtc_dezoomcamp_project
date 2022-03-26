import os
import logging

from datetime import datetime

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator
import pyarrow.csv as pv
import pyarrow.parquet as pq

import zipfile  #to unzip files

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")



dataset_file = "{{ execution_date.strftime(\'%Y%m\') }}" + "-citibike-tripdata.csv"
dataset_url = f"https://s3.amazonaws.com/tripdata/{dataset_file}"
path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
parquet_file = dataset_file.replace('.csv', '.parquet')
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'citibike_project')

URL_PREFIX = 'https://s3.amazonaws.com/tripdata'
extension = '-citibike-tripdata.csv.zip'

URL_TEMPLATE = URL_PREFIX + '/{{ execution_date.strftime(\'%Y%m\') }}' + extension 



def format_to_parquet(src_file):
    if not src_file.endswith('.zip'):
        logging.error("Can only accept source files in zip format, for the moment")
        return
    #first extract all csv files

    with zipfile.ZipFile(src_file,"r") as zip_ref:
        zip_ref.extractall()

    csv_name = src_file.replace('.zip','')  #new csv name

    table = pv.read_csv(csv_name)  #read file with pandas
    dest_file = csv_name.replace('.csv', '.parquet')
    pq.write_table(table, dest_file)


# NOTE: takes 20 mins, at an upload speed of 800kbps. Faster if your internet has a better upload speed
def upload_to_gcs(bucket, object_name, local_file):

    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)


default_args = {
    "owner": "airflow",
    #"start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}


# NOTE: DAG declaration - using a Context Manager (an implicit way)
def donwload_parquetize_upload_dag(
    dag,
    url_template,
    local_csv_path_template,
    local_parquet_path_template,
    local_zip_file_template,
    gcs_path_template
):
    with dag:
        download_dataset_task = BashOperator(
            task_id="download_dataset_task",
            bash_command=f"curl -sSL {url_template} > {local_zip_file_template}"
        )

        format_to_parquet_task = PythonOperator(
            task_id="format_to_parquet_task",
            python_callable=format_to_parquet,
            op_kwargs={
                "src_file": local_zip_file_template,
                "dest file": local_parquet_path_template
            },
        )

        local_to_gcs_task = PythonOperator(
            task_id="local_to_gcs_task",
            python_callable=upload_to_gcs,
            op_kwargs={
                "bucket": BUCKET,
                "object_name": f"new_raw/{parquet_file}",
                "local_file": f"{path_to_local_home}/{parquet_file}",
            },
        )

        rm_task = BashOperator(
            task_id="rm_task",
            bash_command=f"rm {local_csv_path_template} {local_parquet_path_template}"
        )


        download_dataset_task >> format_to_parquet_task >> local_to_gcs_task >> rm_task


#https://s3.amazonaws.com/tripdata/201804-citibike-tripdata.csv.zip


url_prefix = 'https://s3.amazonaws.com/tripdata'
url_suffix = '-citibike-tripdata'

url_template = url_prefix + '/{{ execution_date.strftime(\'%Y%m\') }}' + url_suffix + '.csv.zip'
csv_file_template = AIRFLOW_HOME + '/{{ execution_date.strftime(\'%Y%m\') }}' + url_suffix + '.csv'
zip_file_template = AIRFLOW_HOME + '/{{ execution_date.strftime(\'%Y%m\') }}' + url_suffix + '.csv.zip'
parquet_file_template = AIRFLOW_HOME + '/{{ execution_date.strftime(\'%Y%m\') }}' + url_suffix + '.parquet'
gcs_path_template = "raw/{{ execution_date.strftime(\'%Y\') }}" + url_suffix + "/_{{ execution_date.strftime(\'%m\') }}.parquet"


dtc_project_dag = DAG(
    dag_id="dtc_project_ingest",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2018, 1, 1),
    end_date=datetime(2021, 2, 1),
    default_args=default_args,
    catchup=True,
    max_active_runs=3,
    tags=['dtc-de-project'],
)

donwload_parquetize_upload_dag(
    dag=dtc_project_dag,
    url_template=url_template,
    local_csv_path_template=csv_file_template,
    local_parquet_path_template=parquet_file_template,
    local_zip_file_template = zip_file_template,
    gcs_path_template=gcs_path_template
)
