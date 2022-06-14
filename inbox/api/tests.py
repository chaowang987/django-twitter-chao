from notifications.models import Notification

from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'

class NotificationTests(TestCase):

    def setUp(self):
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')
        self.fiona_tweet = self.create_tweet(self.fiona)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.marcus_client.post(COMMENT_URL, {
            'tweet_id': self.fiona_tweet.id,
            'content': 'aha',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.marcus_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.fiona_tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)