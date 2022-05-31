from testing.testcases import TestCase


class CommentModelTests(TestCase):

    def setUp(self):
        self.marcus = self.create_user('marcus')
        self.tweet = self.create_tweet(self.marcus)
        self.comment = self.create_comment(self.marcus, self.tweet)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        self.create_like(self.marcus, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        self.create_like(self.marcus, self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        fiona = self.create_user('fiona')
        self.create_like(fiona, self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)