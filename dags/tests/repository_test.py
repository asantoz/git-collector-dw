import unittest

from mock.mock import Mock
from src.repository import Repository


class RepositoryTests(unittest.TestCase):

    def test_bulk_insert_with_empty_list_should_ignore_it(self):
        mock_poll = Mock()
        repository = Repository(mock_poll)

        repository.bulk_insert([])

        self.assertEqual(0, mock_poll.cursor().execute.call_count)
        self.assertEqual(0, mock_poll.commit.call_count)
        self.assertEqual(0, mock_poll.cursor().close.call_count)

    def test_bulk_insert_with_one_contributor_list_should_ignore_it(self):
        mock_poll = Mock()
        repository = Repository(mock_poll)

        repository.bulk_insert([{"repo_owner": "facebook", "contributor": "test",
                               "month": "2020-01-01", "repo_name": "react", "total_commits": 10}])

        self.assertEqual(1, mock_poll.cursor().execute.call_count)
        self.assertEqual(1, mock_poll.commit.call_count)
        self.assertEqual(1, mock_poll.cursor().close.call_count)


if __name__ == '__main__':
    unittest.main()
