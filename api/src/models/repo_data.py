from src.models.shared import db


class RepoData(db.Model):
    __tablename__ = 'github_first_contributors'

    repo_name = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Date(), primary_key=True)
    number_of_new_contributors = db.Column(db.String())

    def __init__(self, repo_name, month, number_of_new_contributors):
        self.repo_name = repo_name
        self.month = month
        self.number_of_new_contributors = number_of_new_contributors
