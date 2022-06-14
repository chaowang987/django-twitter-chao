from notifications.models import Notification
from inbox.services import NotificationService
from testing.testcases import TestCase

class NotificationServiceTests(TestCase):

    def setUp(self):
        self.marcus = self.create_user('marcus')
        self.fiona = self.create_user('fiona')
        self.marcus_tweet = self.create_tweet(self.marcus)

    def test_send_comment_notification(self):
        # do not send notification if user comments own tweet
        comment = self.create_comment(self.marcus, self.marcus_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # send notification if user != comment user
        comment = self.create_comment(self.fiona, self.marcus_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # do not send notification if user like own tweet
        like = self.create_like(self.marcus, self.marcus_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # send notification if user != comment user
        like = self.create_like(self.fiona, self.marcus_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)

        # fiona comment on marcus tweet and marcus liked fiona's comment
        comment = self.create_comment(self.fiona, self.marcus_tweet)
        like = self.create_like(self.marcus, comment)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 2)