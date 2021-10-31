import logging
import time
from datetime import date, datetime, timedelta

from airflow.decorators import dag, task
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import DAG, Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import get_current_context

from src.exceptions import RateLimitExceedError
from src.gateway import GitGateway
from src.repository import Repository

gateway = GitGateway(Variable.get("GITHUB_ACCESS_TOKEN", default_var=None))
pghook = PostgresHook(postgres_conn_id="postgres_datawarehouse")
repository = Repository(pghook.get_conn())

repo_owner = Variable.get("GITHUB_REPO_OWNER", default_var=None)
CACHE_KEY_REPOSITORY_LIST = f"{repo_owner}_REPOS_LIST"
CACHE_KEY_TIMESTAMP_TTL = f"{repo_owner}_CACHE_TIMESTAMP_TTL"
CACHE_TTL = Variable.get("CACHE_TTL", default_var="24")


def get_all_available_repositories():
    repos_list = Variable.get(CACHE_KEY_REPOSITORY_LIST, default_var=[],
                              deserialize_json=True)
    repos_list_cache_ttl = float(Variable.get(CACHE_KEY_TIMESTAMP_TTL, default_var=str(datetime.now().timestamp()),
                                              deserialize_json=False))
    cache_ttl = timedelta(hours=int(Variable.get(CACHE_TTL, default_var="24")))
    cache_live_time = (datetime.now() - datetime.fromtimestamp(repos_list_cache_ttl)).total_seconds()

    # If repository list is loaded and cache isn't expired
    if(len(repos_list) > 0 and (cache_live_time < cache_ttl.total_seconds())):
        return repos_list

    try:
        current_page = 1
        repos_request = gateway.get_repositories(repo_owner, current_page)
        repos_list += repos_request
        while(len(repos_request) > 0):
            logging.info(
                f"Requesting page {current_page} of account {repo_owner} repositories list")
            current_page = current_page + 1
            repos_request = gateway.get_repositories(repo_owner, current_page)
            repos_list += repos_request

        # Add on cache
        Variable.set(CACHE_KEY_REPOSITORY_LIST,
                     value=repos_list, serialize_json=True)
        Variable.set(CACHE_KEY_TIMESTAMP_TTL, value=(
            datetime.now() + cache_ttl).timestamp())
        return repos_list

    except RateLimitExceedError as ex:
        logging.exception("Rate limit exceed")
        time.sleep(ex.time_to_wait)
        raise

    except Exception:
        logging.exception("Unable to prepare base repositories DAG")
        raise


@task(retries=20, retry_delay=timedelta(seconds=30), retry_exponential_backoff=True)
def get_contributors(repo):
    try:
        context = get_current_context()
        execution_date = context.get("dag_run").execution_date
        contributors_list = gateway.get_contributors_per_month(
            repo_owner, repo, execution_date)
        repository.bulk_insert(contributors_list)

    except RateLimitExceedError as ex:
        logging.exception("Rate limit exceed")
        time.sleep(ex.time_to_wait)
        raise

    except Exception:
        logging.exception(
            f"Unable to get contributors for {repo} repository")
        raise


with DAG(
    "github_etl",
    description="Extract all repositories contributors data",
    schedule_interval="0 0 1 * *",
    catchup=True,
    max_active_runs=1,
    start_date=datetime(2016, 1, 1),
        is_paused_upon_creation=False) as dag:

    repos_list = get_all_available_repositories()

    task_list = [get_contributors(repo) for repo in repos_list]
    if(len(task_list) > 0):
        task_list >> BashOperator(
            task_id='update_dbt',
            retries=10,
            retry_delay=timedelta(minutes=1),
            bash_command="cd /dbt && dbt run --profiles-dir . --vars 'execution_date: {{ execution_date.replace(day=1).strftime('%Y-%m-%d') }}'")
