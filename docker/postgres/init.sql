CREATE TABLE IF NOT EXISTS airflow.public.github_repo_data (
    contributor VARCHAR NOT NULL,
    repo_owner VARCHAR NOT NULL,
    repo_name VARCHAR NOT NULL,
    month DATE NOT NULL,
    total_commits INTEGER NOT NULL,
    PRIMARY KEY(contributor,repo_owner,repo_name)
);

CREATE TABLE IF NOT EXISTS airflow.public.github_first_contributors (
    repo_name VARCHAR NOT NULL,
    month DATE NOT NULL,
    number_of_new_contributors INTEGER NOT NULL
);