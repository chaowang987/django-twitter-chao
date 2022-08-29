from accounts.models import UserProfile
from testing.testcases import TestCase


class UserProfileTests(TestCase):

    def setUp(self):
        super(UserProfileTests, self).setUp()

    def test_profile_property(self):
        marcus = self.create_user('marcus')
        self.assertEqual(UserProfile.objects.count(), 0)
        p = marcus.profile
        self.assertEqual(isinstance(p, UserProfile), True)
        self.assertEqual(UserProfile.objects.count(), 1)