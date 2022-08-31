from testing.testcases import TestCase
from friendships.services import FriendshipService
from django_hbase.models import EmptyColumnError, BadRowKeyError
from friendships.models import HBaseFollower, HBaseFollowing

import time


class FriendshipServiceTests(TestCase):

    def setUp(self):
        super(FriendshipServiceTests, self).setUp()
        self.marcus = self.create_user('marcus')
        self.fiona = self.create_user('fiona')

    def test_get_followings(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        for to_user in [user1, user2, self.fiona]:
            self.create_friendship(from_user=self.marcus, to_user=to_user)

        user_id_set = FriendshipService.get_following_user_id_set(self.marcus.id)
        self.assertEqual(user_id_set, {user1.id, user2.id, self.fiona.id})

        FriendshipService.unfollow(self.marcus.id, self.fiona.id)
        user_id_set = FriendshipService.get_following_user_id_set(self.marcus.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id})


class HBaseTests(TestCase):

    @property
    def ts_now(self):
        return int(time.time() * 1000000)

    def test_save_and_get(self):
        timestamp = self.ts_now
        following = HBaseFollowing(from_user_id=123, to_user_id=34, created_at=timestamp)
        following.save()

        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.from_user_id, 123)
        self.assertEqual(instance.to_user_id, 34)
        self.assertEqual(instance.created_at, timestamp)

        following.to_user_id = 456
        following.save()

        instance = HBaseFollowing.get(from_user_id=123, created_at=timestamp)
        self.assertEqual(instance.to_user_id, 456)

        # object does not exist, return None
        instance = HBaseFollowing.get(from_user_id=123, created_at=self.ts_now)
        self.assertEqual(instance, None)

    def test_create_and_get(self):
        # missing column data, can not store in hbase
        try:
            HBaseFollower.create(to_user_id=1, created_at=self.ts_now)
            exception_raised = False
        except EmptyColumnError:
            exception_raised = True
        self.assertEqual(exception_raised, True)

        # invalid row_key
        try:
            HBaseFollower.create(from_user_id=1, to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in the row key.')
        self.assertEqual(exception_raised, True)

        ts = self.ts_now
        HBaseFollower.create(from_user_id=1, to_user_id=2, created_at=ts)
        instance = HBaseFollower.get(to_user_id=2, created_at=ts)
        self.assertEqual(instance.from_user_id, 1)
        self.assertEqual(instance.to_user_id, 2)
        self.assertEqual(instance.created_at, ts)

        # can not get if row key missing
        try:
            HBaseFollower.get(to_user_id=2)
            exception_raised = False
        except BadRowKeyError as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at is missing in the row key.')
        self.assertEqual(exception_raised, True)

    def test_filter(self):
        for i in range(2, 5):
            HBaseFollowing.create(from_user_id=1, to_user_id=i, created_at=self.ts_now)

        followings = HBaseFollowing.filter(prefix=(1, None))
        self.assertEqual(len(followings), 3)
        self.assertEqual(followings[0].from_user_id, 1)
        self.assertEqual(followings[0].to_user_id, 2)
        self.assertEqual(followings[1].from_user_id, 1)
        self.assertEqual(followings[1].to_user_id, 3)
        self.assertEqual(followings[2].from_user_id, 1)
        self.assertEqual(followings[2].to_user_id, 4)

        # test limit
        filtered = HBaseFollowing.filter(prefix=(1, None), limit=1)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].from_user_id, 1)
        self.assertEqual(filtered[0].to_user_id, 2)

        filtered = HBaseFollowing.filter(prefix=(1, None), limit=2)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].to_user_id, 2)
        self.assertEqual(filtered[1].to_user_id, 3)

        filtered = HBaseFollowing.filter(prefix=(1, None, None), limit=4)
        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered[0].to_user_id, 2)
        self.assertEqual(filtered[1].to_user_id, 3)
        self.assertEqual(filtered[2].to_user_id, 4)
        
        filtered = HBaseFollowing.filter(start=(1, filtered[1].created_at), limit=2)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].to_user_id, 3)
        self.assertEqual(filtered[1].to_user_id, 4)

        # test reverse
        reversed = HBaseFollowing.filter(prefix=(1, None), limit=2, reverse=True)
        self.assertEqual(len(reversed), 2)
        self.assertEqual(reversed[0].to_user_id, 4)
        self.assertEqual(reversed[1].to_user_id, 3)

        reversed = HBaseFollowing.filter(start=(1, reversed[1].created_at), limit=2, reverse=True)
        self.assertEqual(len(reversed), 2)
        self.assertEqual(reversed[0].to_user_id, 3)
        self.assertEqual(reversed[1].to_user_id, 2)