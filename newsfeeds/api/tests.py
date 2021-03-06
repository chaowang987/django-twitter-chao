from django.contrib.auth.models import User

from accounts.services import UserService
from testing.testcases import TestCase
from utils.paginations import EndlessPagination

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')

    def test_list(self):
        #has to login
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)

        # can't use post
        response = self.marcus_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)

        # nothing is showing when I am not following anyone
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        # I can see my own post
        self.marcus_client.post(POST_TWEETS_URL, {'content': 'Hello World!'})
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)

        # I can see others' posts whom I follow
        self.marcus_client.post(FOLLOW_URL.format(self.fiona.id))
        response = self.fiona_client.post(POST_TWEETS_URL,{
            'content': 'Hello Twitter!',
        })
        posted_tweet_id = response.data['id']
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(user=self.marcus, tweet=tweet)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[0].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[page_size - 1].id)

        # pull the second page
        response = self.marcus_client.get(
            NEWSFEEDS_URL,
            {'created_at__lt': newsfeeds[page_size - 1].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['id'], newsfeeds[page_size].id)
        self.assertEqual(response.data['results'][page_size - 1]['id'], newsfeeds[2 * page_size - 1].id)

        # pull the latest newsfeeds
        response = self.marcus_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at}
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)
        # create new tweet and fanout to newsfeed
        new_tweet = self.create_tweet(followed_user)
        new_newsfeed = self.create_newsfeed(self.marcus, new_tweet)
        response = self.marcus_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at}
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], new_newsfeed.id)

    def test_user_cache(self):
        profile = self.fiona.profile
        profile.nickname = 'dapangzi'
        profile.save()
        self.assertEqual(self.fiona.username, 'fiona')
        self.create_newsfeed(self.fiona, self.create_tweet(self.marcus))
        self.create_newsfeed(self.fiona, self.create_tweet(self.fiona))

        response = self.fiona_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'fiona')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'dapangzi')
        self.assertEqual(results[1]['tweet']['user']['username'], 'marcus')

        self.fiona.username = 'fionaw'
        self.fiona.save()
        profile.nickname = 'xiaopangzi'
        profile.save()
        response = self.fiona_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'fionaw')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'xiaopangzi')
        self.assertEqual(results[1]['tweet']['user']['username'], 'marcus')

    def test_tweet_cache(self):
        tweet = self.create_tweet(self.marcus, 'content1')
        self.create_newsfeed(self.fiona, tweet)
        response = self.fiona_client.get(NEWSFEEDS_URL)
        result = response.data['results']
        self.assertEqual(result[0]['tweet']['user']['username'], 'marcus')
        self.assertEqual(result[0]['tweet']['content'], 'content1')

        # change the username
        self.marcus.username = 'marcusw'
        self.marcus.save()
        response = self.fiona_client.get(NEWSFEEDS_URL)
        result = response.data['results']
        self.assertEqual(result[0]['tweet']['user']['username'], 'marcusw')

        # change the content
        tweet.content = 'content2'
        tweet.save()
        response = self.fiona_client.get(NEWSFEEDS_URL)
        result = response.data['results']
        self.assertEqual(result[0]['tweet']['content'], 'content2')