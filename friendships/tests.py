from testing.testcases import TestCase
from friendships.models import Friendship
from friendships.services import FriendshipService


class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.marcus = self.create_user('marcus')
        self.fiona = self.create_user('fiona')

    def test_get_followings(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        for to_user in [user1, user2, self.fiona]:
            Friendship.objects.create(from_user=self.marcus, to_user=to_user)
        FriendshipService.invalidate_following_cache(self.marcus.id)

        user_id_set = FriendshipService.get_following_user_id_set(self.marcus.id)
        self.assertEqual(user_id_set, set([user1.id, user2.id, self.fiona.id]))

        Friendship.objects.filter(from_user=self.marcus, to_user=self.fiona).delete()
        FriendshipService.invalidate_following_cache(self.marcus.id)
        user_id_set = FriendshipService.get_following_user_id_set(self.marcus.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id})

