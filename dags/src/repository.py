class Repository():
    def __init__(self, conn):
        self.conn = conn

    def bulk_insert(self, contributors_list):
        if(len(contributors_list) == 0):
            return

        ps_cursor = self.conn.cursor()
        for contributor in contributors_list:
            sql = f'''INSERT INTO github_repo_data(repo_owner,contributor,month,repo_name,total_commits) VALUES(%(repo_owner)s,%(contributor)s,%(month)s,%(repo_name)s,%(total_commits)s) ON CONFLICT (contributor,repo_owner,repo_name) 
            DO UPDATE SET 
            repo_owner = (%(repo_owner)s),
            contributor = (%(contributor)s),
            month = (%(month)s),
            repo_name = (%(repo_name)s),
            total_commits = (%(total_commits)s)
            '''
            ps_cursor.execute(sql, contributor)
        self.conn.commit()
        ps_cursor.close()
