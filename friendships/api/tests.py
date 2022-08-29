from friendships.services import FriendshipService
from testing.testcases import TestCase
from friendships.models import Friendship
from friendships.api.paginations import FriendshipPagination
from utils.paginations import EndlessPagination

import math


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        super(FriendshipApiTests, self).setUp()
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')

        for i in range(2):
            fiona_follower = self.create_user(f'fiona_follower{i}')
            self.create_friendship(fiona_follower, self.fiona)

        for i in range(3):
            fiona_following = self.create_user(f'fiona_following{i}')
            self.create_friendship(self.fiona, fiona_following)

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
        before_count = FriendshipService.get_following_count(self.fiona.id)
        response = self.fiona_client.post(FOLLOW_URL.format(self.marcus.id))
        self.assertEqual(response.status_code, 201)
        after_count = FriendshipService.get_following_count(self.fiona.id)
        self.assertEqual(after_count, before_count + 1)

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
        self.create_friendship(self.marcus, self.fiona)
        before_count = FriendshipService.get_following_count(self.marcus.id)
        response = self.marcus_client.post(url)
        after_count = FriendshipService.get_following_count(self.marcus.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(after_count, before_count - 1)

        # unfollow when not following
        before_count = FriendshipService.get_following_count(self.marcus.id)
        response = self.marcus_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        after_count = FriendshipService.get_following_count(self.marcus.id)
        self.assertEqual(after_count, before_count)

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
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            follower = self.create_user('marcus_follower_{}'.format(i))
            friendship = self.create_friendship(from_user=follower, to_user=self.marcus)
            friendships.append(friendship)
            if follower.id % 2 == 0:
                self.create_friendship(from_user=self.fiona, to_user=follower)

        url = FOLLOWERS_URL.format(self.marcus.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous user always show has_followed as False
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # fiona should see has_followed as True for 1st following
        response = self.fiona_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            following = self.create_user('marcus_following_{}'.format(i))
            friendship = self.create_friendship(from_user=self.marcus, to_user=following)
            friendships.append(friendship)
            if following.id % 2 == 0:
                self.create_friendship(from_user=self.fiona, to_user=following)

        url = FOLLOWINGS_URL.format(self.marcus.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous user always show has_followed as False
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # fiona should see has_followed as True for id with even number
        response = self.fiona_client.get(url)
        for result in response.data['results']:
            has_followed = result['user']['id'] % 2 == 0
            self.assertEqual(result['has_followed'], has_followed)

        # marcus should see has_followed as True for all of the followings
        response = self.marcus_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

        # test pull new friendships
        last_created_at = friendships[-1].created_at
        response = self.marcus_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        new_friends = [self.create_user('big_v{}'.format(i)) for i in range(3)]
        new_friendships = []
        for friend in new_friends:
            new_friendship = self.create_friendship(from_user=self.marcus, to_user=friend)
            new_friendships.append(new_friendship)
        response = self.marcus_client.get(url, {'created_at__gt': last_created_at})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        for result, friendship in zip(response.data['results'], new_friendships[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)

    def _paginate_until_the_end(self, url, expect_pages, friendship):
        results, pages = [], 0
        response = self.anonymous_client.get(url)
        results.extend(response.data['results'])
        pages += 1
        while response.data['has_next_page']:
            self.assertEqual(response.status_code, 200)
            last_item = response.data['results'][-1]
            response = self.anonymous_client.get(url, {
                'created_at__lt': last_item['created_at'],
            })
            results.extend(response.data['results'])
            pages += 1

        self.assertEqual(len(results), len(friendship))
        self.assertEqual(pages, expect_pages)
        for result, friendship in zip(results, friendship[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)