import os
from datetime import datetime, timedelta

import airflow
import pendulum
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator

default_args = {
    'owner': 'wmpeng',
    'depends_on_past': False,
    'start_date': datetime(2019, 4, 21),
    'retries': 1,
    'retry_delay': timedelta(minutes=10)
}

dag = DAG('searchengine',
          default_args=default_args,
          schedule_interval=timedelta(days=1),
          max_active_runs=1)


def print_fn(ds, **kwargs):
    now = pendulum.now()
    execution_date = kwargs["execution_date"]
    # If the excution is manually triggered,
    # kwargs["next_execution_date"] is equal to kwargs["execution_date"]
    next_trigger = kwargs["next_execution_date"] + dag.schedule_interval
    print("now", now)
    print("execution_date", execution_date)
    print("next_trigger", next_trigger)
    if now < next_trigger:
        print("[*] Not skip.")
        print(f"[*] Begin task {execution_date}.")
    else:
        print("[*] Skip.")


def spider_fn(ds, **kwargs):
    now = pendulum.now()
    next_trigger = kwargs["next_execution_date"] + dag.schedule_interval
    print("now", now)
    print("next_trigger", next_trigger)
    if now < next_trigger:
        print("[*] Not skip.")
        os.system(
            "cd /root/repostories/NKUSearchEngine/spider && "
            "activate base && "
            "python spider.py new_batch 1000000")
        print("[*] Task Spider finished.")
    else:
        print("[*] Skip.")


def build_fn(ds, **kwargs):
    now = pendulum.now()
    next_trigger = kwargs["next_execution_date"] + dag.schedule_interval
    print("now", now)
    print("next_trigger", next_trigger)
    if now < next_trigger:
        print("[*] Not skip.")
        os.system(
            "cd /root/repostories/NKUSearchEngine && "
            "git checkout product && "
            "git pull")
        os.system(
            "cd /root/repostories/NKUSearchEngine/search-engine/src/main/bin && "
            "bash package.sh")
        print("[*] Task Build finished.")
    else:
        print("[*] Skip.")


def index_fn(ds, **kwargs):
    now = pendulum.now()
    next_trigger = kwargs["next_execution_date"] + dag.schedule_interval
    print("now", now)
    print("next_trigger", next_trigger)
    if now < next_trigger:
        print("[*] Not skip.")
        os.system(
            "cd /root/repostories/NKUSearchEngine/search-engine/target && "
            "java -jar search-engine-0.1-jar-with-dependencies.jar prod index"
        )
        print("[*] Task Index finished.")
    else:
        print("[*] Skip.")


task_print = PythonOperator(
    task_id='print',
    provide_context=True,
    python_callable=print_fn,
    dag=dag
)

task_spider = PythonOperator(
    task_id='spider',
    provide_context=True,
    python_callable=spider_fn,
    dag=dag
)

task_build = PythonOperator(
    task_id='build',
    provide_context=True,
    python_callable=build_fn,
    dag=dag
)

task_index = PythonOperator(
    task_id='index',
    provide_context=True,
    python_callable=index_fn,
    dag=dag
)

task_spider.set_upstream(task_print)
task_build.set_upstream(task_print)
task_index.set_upstream(task_build)
task_index.set_upstream(task_spider)
