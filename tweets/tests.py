from datetime import timedelta
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import TweetPhoto
from tweets.services import TweetService
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis_client import RedisClient
from utils.time_helpers import utc_now


class TweetTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.marcus = self.create_user('marcus')
        self.tweet = self.create_tweet(self.marcus, 'Please sign striker!')

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.marcus, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.marcus, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        fiona = self.create_user('fiona')
        self.create_like(fiona, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_create_photo(self):
        photo = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.marcus,
        )
        self.assertEqual(photo.user, self.marcus)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)
        self.assertEqual(self.tweet.tweetphoto_set.count(), 1)


class TestServiceTweets(TestCase):

    def setUp(self):
        self.clear_cache()
        self.marcus = self.create_user('marcus')

    def test_get_user_tweets(self):
        tweet_ids = []
        for i in range(3):
            tweet = self.create_tweet(self.marcus, 'tweet {}'.format(i))
            tweet_ids.append(tweet.id)
        tweet_ids = tweet_ids[::-1]

        RedisClient.clear()
        conn = RedisClient.get_connection()

        # cache miss
        tweets = TweetService.get_cached_tweets(user_id=self.marcus.id)
        self.assertEqual([t.id for t in tweets], tweet_ids)

        # cache hit
        tweets = TweetService.get_cached_tweets(user_id=self.marcus.id)
        self.assertEqual([t.id for t in tweets], tweet_ids)

        # cached updated
        new_tweet = self.create_tweet(self.marcus, 'new tweet')
        tweets = TweetService.get_cached_tweets(user_id=self.marcus.id)
        tweet_ids.insert(0, new_tweet.id)
        self.assertEqual([t.id for t in tweets], tweet_ids)

    def test_create_new_tweet_before_get_cached_tweets(self):
        tweet1 = self.create_tweet(self.marcus, 'tweet1')
        RedisClient.clear()
        conn = RedisClient.get_connection()

        key = USER_TWEETS_PATTERN.format(user_id=self.marcus.id)
        self.assertEqual(conn.exists(key), False)
        tweet2 = self.create_tweet(self.marcus, 'tweet2')
        self.assertEqual(conn.exists(key), True)

        tweets = TweetService.get_cached_tweets(self.marcus.id)
        self.assertEqual([t.id for t in tweets], [tweet2.id, tweet1.id])