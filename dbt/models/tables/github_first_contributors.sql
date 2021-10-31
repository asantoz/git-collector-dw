{{
  config(
    materialized='incremental',
    unique_key='month',
    incremental_strategy='insert_overwrite',
  )
}}

SELECT repo_name,month,COUNT(*) as number_of_new_contributors FROM github_repo_data 
{% if is_incremental() %}

-- this filter will only be applied on an incremental run
where month = '{{ var("execution_date") }}'

{% endif %}
GROUP BY repo_name,month 
ORDER BY month DESC