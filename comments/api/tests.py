from django.utils import timezone
from rest_framework.test import APIClient
from comments.models import Comment
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'

class CommentApiTests(TestCase):

    def setUp(self):
        self.marcus = self.create_user('marcus')
        self.marcus_client = APIClient()
        self.marcus_client.force_authenticate(self.marcus)
        self.fiona = self.create_user('fiona')
        self.fiona_client = APIClient()
        self.fiona_client.force_authenticate(self.fiona)

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

    def test_destroy(self):
        comment = self.create_comment(self.marcus, self.tweet)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # delete without log on
        response = self.anonymous_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # delete by others
        response = self.fiona_client.delete(url)
        self.assertEqual(response.status_code, 403)

        # delete successfully
        count = Comment.objects.count()
        response = self.marcus_client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), count - 1)

    def test_update(self):
        comment = self.create_comment(self.marcus, self.tweet, 'content')
        another_tweet = self.create_tweet(self.fiona)
        url = COMMENT_DETAIL_URL.format(comment.id)

        # can't update without log on
        response = self.anonymous_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)

        # can't update by others
        response = self.fiona_client.put(url, {'content': 'new'})
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertNotEqual(comment.content, 'new')

        # can't update anything else other than content and updated_at
        before_updated_at = comment.updated_at
        before_created_at = comment.created_at
        now = timezone.now()
        response = self.marcus_client.put(url, {
            'content': 'new',
            'user_id': self.fiona.id,
            'tweet_id': another_tweet.id,
            'created_at': now,
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'new')
        self.assertEqual(comment.user, self.marcus)
        self.assertEqual(comment.tweet, self.tweet)
        self.assertEqual(comment.created_at, before_created_at)
        self.assertNotEqual(comment.created_at, now)
        self.assertNotEqual(comment.updated_at, before_updated_at)

    def test_list(self):
        # tweet_id needs to be there
        response = self.anonymous_client.get(COMMENT_URL)
        self.assertEqual(response.status_code, 400)

        # add tweet_id in the url and there is no comments initially
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)

        # sorted by created_at
        self.create_comment(self.marcus, self.tweet, '1')
        self.create_comment(self.fiona, self.tweet, '2')
        self.create_comment(self.fiona, self.create_tweet(self.fiona), '3')
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['content'], '1')
        self.assertEqual(response.data['comments'][1]['content'], '2')

        # check only filter tweet_id will work. as marcus only comment 1
        response = self.anonymous_client.get(COMMENT_URL, {
            'tweet_id': self.tweet.id,
            'user_id': self.marcus.id,
        })
        self.assertEqual(len(response.data['comments']), 2)




