from django.utils import timezone
from rest_framework.test import APIClient
from comments.models import Comment
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
COMMENT_DETAIL_URL = '/api/comments/{}/'
TWEET_LIST_URL = '/api/tweets/'
TWEET_DETAIL_URL = '/api/tweets/{}/'
NEWSFEED_LIST_URL = '/api/newsfeeds/'

class CommentApiTests(TestCase):

    def setUp(self):
        super(CommentApiTests, self).setUp()
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')
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

    def test_comments_count(self):
        # test tweet detail api
        tweet = self.create_tweet(self.marcus)
        url = TWEET_DETAIL_URL.format(tweet.id)
        response = self.fiona_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments_count'], 0)

        # test tweet list api
        self.create_comment(self.marcus, tweet)
        response = self.fiona_client.get(TWEET_LIST_URL, {'user_id': self.marcus.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['comments_count'], 1)

        # test newsfeeds list api
        self.create_comment(self.fiona, tweet)
        self.create_newsfeed(self.fiona, tweet)
        response = self.fiona_client.get(NEWSFEED_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['comments_count'], 2)

    def test_comments_count_with_cache(self):
        tweet_url = '/api/tweets/{}/'.format(self.tweet.id)
        response = self.marcus_client.get(tweet_url)
        self.assertEqual(self.tweet.comments_count, 0)
        self.assertEqual(response.data['comments_count'], 0)

        data = {'tweet_id': self.tweet.id, 'content': 'a comment'}
        for i in range(2):
            _, client = self.create_user_and_client('user{}'.format(i))
            client.post(COMMENT_URL, data)
            response = client.get(tweet_url)
            self.assertEqual(response.data['comments_count'], i + 1)
            self.assertEqual(self.tweet.comments_count, i)
            self.tweet.refresh_from_db()
            self.assertEqual(self.tweet.comments_count, i + 1)

        comment_data = self.fiona_client.post(COMMENT_URL, data).data
        response = self.fiona_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # update comment shouldnt update comments count
        comment_url = '{}{}/'.format(COMMENT_URL, comment_data['id'])
        response = self.fiona_client.put(comment_url, {'content': 'updated'})
        self.assertEqual(response.status_code, 200)
        response = self.fiona_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 3)

        # delete comment will update comments count
        response = self.fiona_client.delete(comment_url)
        self.assertEqual(response.status_code, 200)
        response = self.fiona_client.get(tweet_url)
        self.assertEqual(response.data['comments_count'], 2)
        self.assertEqual(self.tweet.comments_count, 3)
        self.tweet.refresh_from_db()
        self.assertEqual(self.tweet.comments_count, 2)

