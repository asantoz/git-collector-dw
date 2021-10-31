import json
import unittest
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from mock.mock import Mock, call
from src.exceptions import HttpRequestError, RateLimitExceedError
from src.gateway import GitGateway


class GatewayTests(unittest.TestCase):

    def test_get_repositories_response_error_status_should_raise_an_exception(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 500
        gateway.http.request().data = "[]"
        gateway.http.request().headers = self.set_rate_limit()

        with self.assertRaises(HttpRequestError) as context:
            gateway.get_repositories("facebook")

        self.assertTrue(500 == context.exception.status)
        self.assertTrue("[]" == context.exception.message)

    def test_get_repositories_rate_limit_exceed_should_raise_an_exception(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 403
        gateway.http.request().data = "[]"
        gateway.http.request().headers = self.set_rate_limit(True)

        with self.assertRaises(RateLimitExceedError) as context:
            gateway.get_repositories("facebook")

        self.assertTrue(0 <= context.exception.time_to_wait <= 1)

    def test_get_repositories_sucessfull_response_with_empty_list_should_return_an_empty_array(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 200
        gateway.http.request().data = "[]"
        gateway.http.request().headers = self.set_rate_limit()

        result = gateway.get_repositories("facebook")

        self.assertEqual(0, len(result))

    def test_get_repositories_sucessfull_response_with_invalid_objects_should_be_discard(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 200
        gateway.http.request().data = "[{}]"
        gateway.http.request().headers = self.set_rate_limit()

        result = gateway.get_repositories("facebook")

        self.assertEqual(0, len(result))

    def test_get_repositories_sucessfull_response_with_2_repos(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 200
        gateway.http.request().data = '[{"name": "test1"},{"name": "test2"}]'
        gateway.http.request().headers = self.set_rate_limit()

        result = gateway.get_repositories("facebook")

        self.assertEqual(2, len(result))
        self.assertEqual(['test1', 'test2'], result)
        self.assertEqual(call('GET', 'https://api.github.com/users/facebook/repos?page=1&page_size=50', headers={
                         'Authorization': 'token 123', 'user-agent': 'github-crawler'}), gateway.http.request.call_args_list[-1])

    def test_get_contributors_per_month_error_status_should_raise_an_exception(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 500
        gateway.http.request().data = "[]"
        gateway.http.request().headers = self.set_rate_limit()

        with self.assertRaises(HttpRequestError) as context:
            gateway.get_contributors_per_month(
                "facebook", "react", datetime.now())

        self.assertTrue(500 == context.exception.status)
        self.assertTrue("[]" == context.exception.message)

    def test_get_repositories_rate_limit_exceed_should_raise_an_exception(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 403
        gateway.http.request().data = "[]"
        gateway.http.request().headers = self.set_rate_limit(True)

        with self.assertRaises(RateLimitExceedError) as context:
            gateway.get_contributors_per_month(
                "facebook", "react", datetime.now())

        self.assertTrue(0 <= context.exception.time_to_wait <= 1)

    def test_get_contributors_sucessfull_response_with_empty_list_should_return_an_empty_array(self):
        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 200
        gateway.http.request().data = "[]"
        gateway.http.request().headers = self.set_rate_limit()

        result = gateway.get_contributors_per_month(
            "facebook", "react", datetime.now())

        self.assertEqual(0, len(result))

    def test_get_contributors_sucessfull_response_with_contributor_without_commits_this_month_should_return_an_empty_array(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 200
        gateway.http.request().data = '[{"total":0},{"total":0}]'
        gateway.http.request().headers = self.set_rate_limit()

        result = gateway.get_contributors_per_month(
            "facebook", "react", datetime.now())

        self.assertEqual(0, len(result))

    def test_get_contributors_should_not_return_authors_without_commits_on_requested_month(self):
        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 200
        gateway.http.request().headers = self.set_rate_limit()

        gateway.http.request().data = json.dumps([{"total": 1, "weeks": [
            {"c": 0, "w": (datetime.now() -
                           relativedelta(months=2)).timestamp()},
            {"c": 1, "w": (datetime.now() -
                           relativedelta(months=1)).timestamp()},
            {"c": 1, "w": datetime.now().timestamp()}],
            "author": {"login": "username"}}])

        result = gateway.get_contributors_per_month(
            "facebook", "react", datetime.now())

        self.assertEqual(0, len(result))

    def test_get_contributors_should_return_authors_with_commits_on_requested_month(self):

        gateway = GitGateway("123")
        gateway.http.request = Mock()
        gateway.http.request().status = 200
        gateway.http.request().headers = self.set_rate_limit()

        gateway.http.request().data = json.dumps([{"total": 3, "weeks": [
            {"c": 0, "w": (datetime.now() -
                           relativedelta(months=1)).timestamp()},
            {"c": 1, "w": (datetime.now()).timestamp()},
            {"c": 1, "w": (datetime.now() + relativedelta(months=1)).timestamp()}],
            "author": {"login": "username"}}])
        current_month = datetime.now()

        result = gateway.get_contributors_per_month(
            "facebook", "react", datetime.now())

        self.assertEqual(1, len(result))
        self.assertEqual({'repo_owner': 'facebook', 'contributor': 'username',
                          'month': current_month.replace(day=1).strftime('%Y-%m-%d'), 'repo_name': 'react', 'total_commits': 1}, result[0])

    def set_rate_limit(self, reached=False):

        if(reached == False):
            return {'X-RateLimit-Remaining': 100, 'X-RateLimit-Limit': 500,
                    'X-RateLimit-Reset': (datetime.now() + timedelta(days=1)).timestamp()}
        else:
            return {'X-RateLimit-Remaining': 0, 'X-RateLimit-Limit': 500,
                    'X-RateLimit-Reset': (datetime.now() + timedelta(seconds=1)).timestamp()}


if __name__ == '__main__':
    unittest.main()
