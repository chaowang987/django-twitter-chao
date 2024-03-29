from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet, TweetPhoto
from django.core.files.uploadedfile import SimpleUploadedFile
from utils.paginations import EndlessPagination
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer


TWEET_LIST_API = '/api/tweets/'
TWEET_CREATE_API = '/api/tweets/'
TWEET_RETRIEVE_API = '/api/tweets/{}/'


class TweetApiTests(TestCase):

    def setUp(self):
        super(TweetApiTests, self).setUp()
        self.user1 = self.create_user('user1')
        self.tweets1 = [
            self.create_tweet(self.user1)
            for _ in range(3)
        ]

        self.user1_client = APIClient()
        self.user1_client.force_authenticate(self.user1)

        self.user2 = self.create_user('user2')
        self.tweets2 = [
            self.create_tweet(self.user2)
            for _ in range(2)
        ]

    def test_list_api(self):
        # check api include any user_id
        response = self.anonymous_client.get(TWEET_LIST_API)
        self.assertEqual(response.status_code, 400)

        # should return 200 code if request is successful
        response = self.anonymous_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        response = self.anonymous_client.get(TWEET_LIST_API, {
            'user_id': self.user2.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # should return the newest to oldest created
        self.assertEqual(response.data['results'][0]['id'], self.tweets2[1].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweets2[0].id)

    def test_create_api(self):
        # has to login
        response = self.anonymous_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 403)

        # can't be empty
        response = self.user1_client.post(TWEET_CREATE_API)
        self.assertEqual(response.status_code, 400)

        # can't be too short(less than 6 chars)
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': '1'
        })
        self.assertEqual(response.status_code, 400)

        # can't be too long
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': '1' * 141
        })
        self.assertEqual(response.status_code, 400)

        # create tweets normally
        tweets_count = Tweet.objects.count()
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'Hello World, this is my first tweet!'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(Tweet.objects.count(), tweets_count + 1)

    def test_create_with_files(self):
        # upload with no files
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # upload with empty file list
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # upload a single file
        file = SimpleUploadedFile(
            name='selfie.jpg',
            content=str.encode('a fake image'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [file],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        # upload multiple files
        file1 = SimpleUploadedFile(
            name='selfie1.jpg',
            content=str.encode('selfie 1'),
            content_type='image/jpeg',
        )
        file2 = SimpleUploadedFile(
            name='selfie2.jpg',
            content=str.encode('selfie 2'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'a selfie',
            'files': [file1, file2],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 3)

        # we can get photo url from retrieve api
        retrieve_url = TWEET_RETRIEVE_API.format(response.data['id'])
        response = self.user1_client.get(retrieve_url)
        self.assertEqual(len(response.data['photo_urls']), 2)
        self.assertEqual('selfie1' in response.data['photo_urls'][0], True)
        self.assertEqual('selfie2' in response.data['photo_urls'][1], True)

        # upload file more than 9 files
        files = [
            SimpleUploadedFile(
                name=f'selfie{i}.jpg',
                content=str.encode('selfie {i}'),
                content_type='image/jpeg',
            )
            for i in range(10)
        ]
        response = self.user1_client.post(TWEET_CREATE_API, {
            'content': 'failed due to number of photos exceeded limit',
            'files': files,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TweetPhoto.objects.count(), 3)

    def test_retrieve(self):
        # invalid tweet id provided
        url = TWEET_RETRIEVE_API.format(-1)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 404)

        # test if we can get a tweet and comments under it
        tweet = self.create_tweet(self.user1)
        url = TWEET_RETRIEVE_API.format(tweet.id)
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 0)
        self.create_comment(self.user2, tweet, '1')
        self.create_comment(self.user1, tweet, '2')
        self.create_comment(self.user1, self.create_tweet(self.user2), '3')
        response = self.anonymous_client.get(url)
        self.assertEqual(len(response.data['comments']), 2)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        for i in range(page_size * 2 - len(self.tweets1)):
            self.tweets1.append(self.create_tweet(self.user1, 'tweet_{}'.format(i)))

        tweets = self.tweets1[::-1]

        # pull the first page
        response = self.anonymous_client.get(TWEET_LIST_API, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[page_size - 1].id)

        # pull the second page
        response = self.anonymous_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__lt': tweets[page_size - 1].created_at,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], tweets[page_size].id)
        self.assertEqual(response.data['results'][1]['id'], tweets[page_size + 1].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], tweets[2 * page_size - 1].id)

        # pull the latest tweet
        response = self.anonymous_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__gt': tweets[0].created_at,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)

        new_tweet = self.create_tweet(self.user1, 'a new tweet comes in')
        response = self.anonymous_client.get(TWEET_LIST_API, {
            'user_id': self.user1.id,
            'created_at__gt': tweets[0].created_at,
        })
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_tweet.id)

    def test_cache_tweet_in_redis(self):
        marcus = self.create_user('marcus')
        tweet = self.create_tweet(marcus)
        conn = RedisClient.get_connection()
        serialized_data = DjangoModelSerializer.serialize(tweet)
        conn.set(f'tweet:{tweet.id}', serialized_data)
        data = conn.get('tweet:not_exists')
        self.assertEqual(data, None)

        data = conn.get(f'tweet:{tweet.id}')
        cached_tweet = DjangoModelSerializer.deserialize(data)
        self.assertEqual(tweet, cached_tweet)