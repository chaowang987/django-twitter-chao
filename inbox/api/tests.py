from notifications.models import Notification
from testing.testcases import TestCase

COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'

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

class NotificationApiTests(TestCase):
    def setUp(self):
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')
        self.marcus_tweet = self.create_tweet(self.marcus)

    def test_unread_count(self):
        self.fiona_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.marcus_tweet.id,
        })

        # should have only 1 unread notification for tweet like
        url = '/api/notifications/unread-count/'
        response = self.marcus_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        #should have two unread notification for comment like
        comment = self.create_comment(self.marcus, self.marcus_tweet)
        self.fiona_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.marcus_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 2)

        # the other user should have no permission to get the notification information
        response =self.fiona_client.get(url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_all_as_read(self):
        self.fiona_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.marcus_tweet.id,
        })
        comment = self.create_comment(self.marcus, self.marcus_tweet)
        self.fiona_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': self.marcus_tweet.id,
        })
        # have two unread notifications
        unread_url = '/api/notifications/unread-count/'
        response = self.marcus_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'

        # cant use get
        response = self.marcus_client.get(mark_url)
        self.assertEqual(response.status_code, 405)

        # cant mark by the other users
        response = self.fiona_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 0)

        # use post and return 200 and 2 marked count
        response = self.marcus_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)

        # unread should be cleared now
        response = self.marcus_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.fiona_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.marcus_tweet.id,
        })
        comment = self.create_comment(self.marcus, self.marcus_tweet)
        self.fiona_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': self.marcus_tweet.id,
        })

        # cant get notification without login
        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)

        # the other user cant get notification information
        response = self.fiona_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        # marcus should be able to see 2 notifications.
        response = self.marcus_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

        # mark the first one as read
        notification = self.marcus.notifications.first()
        notification.unread = False
        notification.save()
        response = self.marcus_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.marcus_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.marcus_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)