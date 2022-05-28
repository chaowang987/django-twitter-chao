from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.marcus = self.create_user('marcus')
        self.marcus_client = APIClient()
        self.marcus_client.force_authenticate(self.marcus)

        self.fiona = self.create_user('fiona')
        self.fiona_client = APIClient()
        self.fiona_client.force_authenticate(self.fiona)

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
        self.assertEqual(len(response.data['newsfeeds']), 0)

        # I can see my own post
        self.marcus_client.post(POST_TWEETS_URL, {'content': 'Hello World!'})
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)

        # I can see others' posts whom I follow
        self.marcus_client.post(FOLLOW_URL.format(self.fiona.id))
        response = self.fiona_client.post(POST_TWEETS_URL,{
            'content': 'Hello Twitter!',
        })
        posted_tweet_id = response.data['id']
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)