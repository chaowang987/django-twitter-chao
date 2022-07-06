from testing.testcases import TestCase

LIKE_BASE_API ='/api/likes/'
LIKE_CANCEL_API = '/api/likes/cancel/'
COMMENT_LIST_API = '/api/comments/'
TWEET_LIST_API = '/api/tweets/'
TWEET_DETAIL_API = '/api/tweets/{}/'
NEWSFEED_LIST_API = '/api/newsfeeds/'


class LikeApiTests(TestCase):

    def setUp(self):
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')

    def test_tweet_like(self):
        tweet = self.create_tweet(self.marcus)
        data = {
            'content_type': 'tweet',
            'object_id': tweet.id,
        }
        # has to log on
        response = self.anonymous_client.post(LIKE_BASE_API, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.marcus_client.get(LIKE_BASE_API, data)
        self.assertEqual(response.status_code, 405)

        # wrong content_type
        response = self.marcus_client.post(LIKE_BASE_API, {
            'content_type': 'twitter',
            'object_id': tweet.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object_id
        response = self.marcus_client.post(LIKE_BASE_API, {
            'content_type': 'tweet',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # post success
        response = self.marcus_client.post(LIKE_BASE_API, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(tweet.like_set.count(), 1)

        # duplicate likes
        response = self.marcus_client.post(LIKE_BASE_API, data)
        self.assertEqual(tweet.like_set.count(), 1)
        response = self.fiona_client.post(LIKE_BASE_API, data)
        self.assertEqual(tweet.like_set.count(), 2)

    def test_comment_likes(self):
        tweet = self.create_tweet(self.marcus)
        comment = self.create_comment(self.fiona, tweet)
        data = {'content_type': 'comment', 'object_id': comment.id}

        # anonymous is not allowed
        response = self.anonymous_client.post(LIKE_BASE_API, data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.marcus_client.get(LIKE_BASE_API, data)
        self.assertEqual(response.status_code, 405)

        # wrong content_type
        response = self.marcus_client.post(LIKE_BASE_API, {
            'content_type': 'comet',
            'object_id': comment.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['errors'], True)

        # wrong object_id
        response = self.marcus_client.post(LIKE_BASE_API, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['errors'], True)

        # post success
        response = self.marcus_client.post(LIKE_BASE_API, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)

        # duplicate likes
        response = self.marcus_client.post(LIKE_BASE_API, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(comment.like_set.count(), 1)
        self.fiona_client.post(LIKE_BASE_API, data)
        self.assertEqual(comment.like_set.count(), 2)

    def test_cancel(self):
        tweet = self.create_tweet(self.marcus)
        comment = self.create_comment(self.fiona, tweet)
        like_comment_data = {'content_type': 'comment', 'object_id': comment.id}
        like_tweet_data = {'content_type': 'tweet', 'object_id': tweet.id}
        self.marcus_client.post(LIKE_BASE_API, like_comment_data)
        self.fiona_client.post(LIKE_BASE_API, like_tweet_data)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # need to login
        response = self.anonymous_client.post(LIKE_CANCEL_API, like_comment_data)
        self.assertEqual(response.status_code, 403)

        # get is not allowed
        response = self.marcus_client.get(LIKE_CANCEL_API, like_comment_data)
        self.assertEqual(response.status_code, 405)

        # wrong content_type
        response = self.marcus_client.post(LIKE_CANCEL_API, {
            'content_type': 'wrong',
            'object_id': 1,
        })
        self.assertEqual(response.status_code, 400)

        # wrong object_id
        response = self.marcus_client.post(LIKE_CANCEL_API, {
            'content_type': 'comment',
            'object_id': -11,
        })
        self.assertEqual(response.status_code, 400)

        # fiona does not like comment
        response = self.fiona_client.post(LIKE_CANCEL_API, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 1)

        # successfully canceled comment like
        response = self.marcus_client.post(LIKE_CANCEL_API, like_comment_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # marcus does not like the tweet
        response = self.marcus_client.post(LIKE_CANCEL_API, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(tweet.like_set.count(), 1)
        self.assertEqual(comment.like_set.count(), 0)

        # successfully canceled tweet like
        response = self.fiona_client.post(LIKE_CANCEL_API, like_tweet_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(tweet.like_set.count(), 0)
        self.assertEqual(comment.like_set.count(), 0)

    def test_likes_in_comments_api(self):
        tweet = self.create_tweet(self.marcus)
        comment = self.create_comment(self.marcus, tweet)

        # test it without login
        response = self.anonymous_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)

        # test comments list api with login
        response = self.fiona_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], False)
        self.assertEqual(response.data['comments'][0]['likes_count'], 0)
        self.create_like(self.fiona, comment)
        response = self.fiona_client.get(COMMENT_LIST_API, {'tweet_id': tweet.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 1)

        # test tweet detail api
        self.create_like(self.marcus, comment)
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.fiona_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['comments'][0]['has_liked'], True)
        self.assertEqual(response.data['comments'][0]['likes_count'], 2)

    def test_likes_in_tweets_api(self):
        tweet = self.create_tweet(self.marcus)

        # test tweet detail api
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.fiona_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], False)
        self.assertEqual(response.data['likes_count'], 0)
        self.create_like(self.fiona, tweet)
        response = self.fiona_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_liked'], True)
        self.assertEqual(response.data['likes_count'], 1)

        # test newsfeeds list api
        self.create_like(self.marcus, tweet)
        self.create_newsfeed(self.fiona, tweet)
        response = self.fiona_client.get(NEWSFEED_LIST_API)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['tweet']['has_liked'], True)
        self.assertEqual(response.data['results'][0]['tweet']['likes_count'], 2)

        # test likes details
        url = TWEET_DETAIL_API.format(tweet.id)
        response = self.fiona_client.get(url)
        self.assertEqual(len(response.data['likes']), 2)
        self.assertEqual(response.data['likes'][0]['user']['id'], self.marcus.id)
        self.assertEqual(response.data['likes'][1]['user']['id'], self.fiona.id)

