from testing.testcases import TestCase

LIKE_BASE_API ='/api/likes/'
LIKE_CANCEL_API = '/api/likes/cancel/'

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

