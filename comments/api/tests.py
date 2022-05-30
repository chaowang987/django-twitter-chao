from rest_framework.test import APIClient
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'


class CommentApiTests(TestCase):

    def setUp(self):
        self.marcus = self.create_user('marcus')
        self.marcus_client = APIClient()
        self.marcus_client.force_authenticate(self.marcus)

        self.tweet = self.create_tweet(self.marcus)

    def test_create(self):
        # 匿名不可以创建
        response = self.anonymous_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 403)

        # 啥参数都没带不行
        response = self.marcus_client.post(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # 只带 tweet_id 不行
        response = self.marcus_client.post(COMMENT_URL, {'tweet_id': self.tweet.id})
        self.assertEqual(response.status_code, 400)

        # 只带 content 不行
        response = self.marcus_client.post(COMMENT_URL, {'content': '1'})
        self.assertEqual(response.status_code, 400)

        # content 太长不行
        response = self.marcus_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1' * 141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content' in response.data['errors'], True)

        # tweet_id 和 content 都带才行
        response = self.marcus_client.post(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'content': '1',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.marcus.id)
        self.assertEqual(response.data['tweet_id'], self.tweet.id)
        self.assertEqual(response.data['content'], '1')