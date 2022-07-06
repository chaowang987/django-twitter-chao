from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.models import Friendship
from utils.paginations import FriendshipPagination

import math


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')

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
        self.assertEqual(len(response.data['results']), 3)

        # make sure it is followed by newset to oldest
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        fw0 = response.data['results'][0]['user']['username']
        fw1 = response.data['results'][1]['user']['username']
        fw2 = response.data['results'][2]['user']['username']
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
        self.assertEqual(len(response.data['results']), 2)

        # make sure it is followed by newset to oldest
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        fw0 = response.data['results'][0]['user']['username']
        fw1 = response.data['results'][1]['user']['username']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(fw0, 'fiona_follower1')
        self.assertEqual(fw1, 'fiona_follower0')

    def test_followers_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            follower = self.create_user('marcus_follower_{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.marcus)
            if follower.id % 2 == 0:
                Friendship.objects.create(from_user=self.fiona, to_user=follower)

        url = FOLLOWERS_URL.format(self.marcus.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous user always show has_followed as False
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # fiona should see has_followed as True for 1st following
        response = self.fiona_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            following = self.create_user('marcus_following_{}'.format(i))
            Friendship.objects.create(from_user=self.marcus, to_user=following)
            if following.id % 2 == 0:
                Friendship.objects.create(from_user=self.fiona, to_user=following)

        url = FOLLOWINGS_URL.format(self.marcus.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous user always show has_followed as False
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # fiona should see has_followed as True for id with even number
        response = self.fiona_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = result['user']['id'] % 2 == 0
            self.assertEqual(result['has_followed'], has_followed)

        # marcus should see has_followed as True for all of the followings
        response = self.marcus_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        # get does not require login, has_followed requires login
        response = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['total_pages'], 2)

        response = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['total_pages'], 2)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, 404)

        # the specified page size cant exceeds max page size
        response = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), max_page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['has_next_page'], True)

        # user can change default page size
        response = self.anonymous_client.get(url, {'page': 1, 'size': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['total_pages'], math.ceil(page_size * 2 / 3))