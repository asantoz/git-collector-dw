import json
from datetime import datetime

import pytest
from flask import jsonify
from src.app import app
from src.models.repo_data import RepoData
from src.models.shared import db

records = [{"repo_name": f"test{i}", "month": datetime.now(
), "number_of_new_contributors": 100} for i in range(0, 10)]


@pytest.fixture
def client():
    client = app.test_client()
    return client


def test_page_size_limit_exceeded(client):
    _load_records(records)

    response = client.get('/api/repos?page=1&page_size=1000')

    assert _json_of_response(response) == {
        'description': 'Page size should be greater than 1 and less than 100', 'error_code': '00001'}
    assert response.status_code == 400


def test_page_size_invalid(client):
    _load_records(records)

    response = client.get('/api/repos?page=1&page_size=-1')

    assert _json_of_response(response) == {
        'description': 'Page size should be greater than 1 and less than 100', 'error_code': '00001'}
    assert response.status_code == 400


def test_page_number_invalid(client):
    _load_records(records)

    response = client.get('/api/repos?page=-1')

    assert _json_of_response(response) == {
        'description': 'Page number should be greater than 1', 'error_code': '00001'}
    assert response.status_code == 400


def test_empty_db_should_return_an_empty_list(client):
    _load_records([])
    response = client.get('/api/repos')
    assert _json_of_response(response) == _expected_output_format([], 0, 1, 10)


def test_ten_records_db_should_return_an_2_pages_of_5_elements(client):
    _load_records(records)

    response_page1 = client.get('/api/repos?page=1&page_size=5')
    response_page2 = client.get('/api/repos?page=2&page_size=5')
    empty_page3 = client.get('/api/repos?page=3&page_size=5')

    assert response_page1.status_code == 200
    assert response_page2.status_code == 200
    assert empty_page3.status_code == 200
    assert _json_of_response(response_page1) == _expected_output_format(
        records[:5], 10, 1, 5)
    assert _json_of_response(response_page2) == _expected_output_format(
        records[5:], 10, 2, 5)
    assert _json_of_response(
        empty_page3) == _expected_output_format([], 10, 3, 5)


def _load_records(records):
    with app.app_context():
        db.session.query(RepoData).delete()
        for record in records:
            db.session.add(RepoData(
                record["repo_name"], record["month"], record["number_of_new_contributors"]))
        db.session.commit()


def _expected_output_format(records, total_count, page, per_page):
    results = [
        {
            "repo_name": repo["repo_name"],
            "month": repo["month"].strftime('%Y-%m-%d'),
            "number_of_new_contributors": repo["number_of_new_contributors"]
        } for repo in records]
    return {"total_records": total_count, "page": page, "page_size": per_page, "items": results}


def _json_of_response(response):
    return json.loads(response.data.decode('utf8'))
