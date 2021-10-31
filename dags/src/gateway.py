
import calendar
import json
import logging
from datetime import datetime, timezone
import urllib3

from src.exceptions import HttpRequestError, RateLimitExceedError


class GitGateway():

    def __init__(self, token):
        self.token = token
        self.http = urllib3.PoolManager()

    def get_repositories(self, owner, page_number=1):
        resp = self.http.request(
            "GET", f'https://api.github.com/users/{owner}/repos?page={page_number}&page_size=50', headers=self.get_auth_header())

        self.handle_rate_limit(resp)
        if resp.status == 200:
            json_response = json.loads(resp.data)
            return [repo["name"] for repo in json_response if repo.get("name")]
        else:
            raise HttpRequestError(resp.data, resp.status)

    def get_contributors_per_month(self, owner, repo_name, month):
        if not isinstance(month, datetime):
            raise ValueError("month should be a datetime")

        resp = self.http.request(
            "GET", f'https://api.github.com/repos/{owner}/{repo_name}/stats/contributors', headers=self.get_auth_header())

        self.handle_rate_limit(resp)

        if resp.status == 200:
            json_response = json.loads(resp.data)
            first_day_month_date = month.replace(
                day=1, tzinfo=timezone.utc).date()
            first_day_month_unix_timestamp = month.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc).timestamp()
            last_day_month_unix_timestamp = month.replace(day=calendar.monthrange(
                month.year, month.month)[1], hour=23, minute=59, second=59, microsecond=0, tzinfo=timezone.utc).timestamp()

            first_contributions = []
            for contribution in json_response:

                # discard contributors without commits
                if contribution["total"] == 0:
                    break

                # Select for first contribution on a datetime ordered array
                first_contribution = next(
                    ctr for ctr in contribution["weeks"] if ctr["c"] > 0)

                # Validate if the first contribution is on the request month
                if first_day_month_unix_timestamp <= first_contribution["w"] <= last_day_month_unix_timestamp:
                    first_contributions.append({
                        'repo_owner': owner,
                        'contributor':
                        contribution["author"]["login"], 'month': str(first_day_month_date), 'repo_name': repo_name, 'total_commits': first_contribution["c"]})
            return first_contributions

        # No content
        elif resp.status == 204:
            return []

        else:
            raise HttpRequestError(resp.data, resp.status)

    def handle_rate_limit(self, response):
        remaining_requests = response.headers['X-RateLimit-Remaining']
        limit_requests = response.headers['X-RateLimit-Limit']
        reset_time = response.headers['X-RateLimit-Reset']
        logging.info(
            f"RateLimit Report - RemainingRequests: {remaining_requests} - Limit: {limit_requests} - NextResetWindow: {reset_time}")
        if(response.status == 403):
            if(int(remaining_requests) == 0):
                seconds_to_wait = (datetime.utcfromtimestamp(
                    int(reset_time)) - datetime.now()).total_seconds()
                raise RateLimitExceedError(
                    f"Github Rate exceed limit of {limit_requests} with next reset time window is in about {seconds_to_wait} seconds", seconds_to_wait)

    def get_auth_header(self):
        if self.token:
            return {"Authorization": f"token {self.token}", "user-agent": "github-crawler"}
        else:
            return {"user-agent": "github-crawler"}
