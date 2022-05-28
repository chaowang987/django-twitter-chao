from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.marcus = self.create_user('marcus')
        self.marcus_client = APIClient()
        self.marcus_client.force_authenticate(self.marcus)

        self.fiona = self.create_user('fiona')
        self.fiona_client = APIClient()
        self.fiona_client.force_authenticate(self.fiona)

        for i in range(2):
            fiona_follower = self.create_user(f'fiona_follower{i}')
            Friendship.objects.create(
                from_user=fiona_follower,
                to_user=self.fiona,
            )

        for i in range(3):
            fiona_following = self.create_user(f'fiona_following{i}')
            Friendship.objects.create(
                from_user=self.fiona,
                to_user=fiona_following,
            )

    def test_follow(self):
        url = FOLLOW_URL.format(self.fiona.id)

        # need to login in order to follow
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # return 405 if using get
        response = self.fiona_client.get(url)
        self.assertEqual(response.status_code, 405)

        # can't follow myself
        response = self.fiona_client.post(url)
        self.assertEqual(response.status_code, 400)

        # can follow
        response = self.marcus_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual('created_at' in response.data, True)
        self.assertEqual('user' in response.data, True)
        self.assertEqual(response.data['user']['username'], self.fiona.username)
        self.assertEqual(response.data['user']['id'], self.fiona.id)

        # can't follow again
        response = self.marcus_client.post(url)
        self.assertEqual(response.status_code, 400)

        # follow each other
        count = Friendship.objects.count()
        response = self.fiona_client.post(FOLLOW_URL.format(self.marcus.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.fiona.id)

        # unfollow without login
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)

        # return 405 if using get
        response = self.fiona_client.get(url)
        self.assertEqual(response.status_code, 405)

        # can't unfollow myself
        response = self.fiona_client.post(url)
        self.assertEqual(response.status_code, 400)

        # can unfollow
        Friendship.objects.create(from_user=self.marcus, to_user=self.fiona)
        count = Friendship.objects.count()
        response = self.marcus_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)

        # unfollow when not following
        count = Friendship.objects.count()
        response = self.marcus_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.fiona.id)

        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # use get
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followings']), 3)

        # make sure it is followed by newset to oldest
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        fw0 = response.data['followings'][0]['user']['username']
        fw1 = response.data['followings'][1]['user']['username']
        fw2 = response.data['followings'][2]['user']['username']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(fw0, 'fiona_following2')
        self.assertEqual(fw1, 'fiona_following1')
        self.assertEqual(fw2, 'fiona_following0')

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.fiona.id)

        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)

        # use get
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['followers']), 2)

        # make sure it is followed by newset to oldest
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        fw0 = response.data['followers'][0]['user']['username']
        fw1 = response.data['followers'][1]['user']['username']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(fw0, 'fiona_follower1')
        self.assertEqual(fw1, 'fiona_follower0')
