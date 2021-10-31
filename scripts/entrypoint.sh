#!/usr/bin/env bash

airflow db init
airflow users  create --role Admin --username admin --email admin --firstname admin --lastname admin --password admin
airflow connections add 'postgres_datawarehouse' --conn-uri $AIRFLOW__CORE__SQL_ALCHEMY_CONN
airflow webserver