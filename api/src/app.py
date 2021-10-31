import logging
import os

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from sqlalchemy.dialects import postgresql

from src.exceptions.custom_exceptions import APIBadParameters
from src.models.repo_data import RepoData
from src.models.shared import db
from src.utils.utils import validate_pagination

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'API_POSTGRES_CONNECTION_URL')
migrate = Migrate(app, db)
db.init_app(app)
migrate.init_app(app, db)


@app.route('/api/repos', methods=['GET'])
def get_repos():
    page = request.args.get("page")
    page_size = request.args.get("page_size")
    page, page_size = validate_pagination(page, page_size)
    pagination = RepoData.query.paginate(page, page_size, error_out=False)
    results = [
        {
            "repo_name": repo.repo_name,
            "month": repo.month.strftime('%Y-%m-%d'),
            "number_of_new_contributors": repo.number_of_new_contributors
        } for repo in pagination.items]
    return {"total_records": pagination.total, "page": page, "page_size": pagination.per_page, "items": results}


@app.errorhandler(APIBadParameters)
def handle_exception(err):
    response = {
        "error_code": "00001",
        "description": err.description,
    }
    return response, err.code


@app.errorhandler(Exception)
def handle_exception(err):
    app.logger.error(f"Unknown Exception: {str(err)}")
    response = {"error_code": "00002",
                "description": "Upsss! Something went wrong!"}
    return jsonify(response), 500


if __name__ == '__main__':
    app.run(debug=True)
