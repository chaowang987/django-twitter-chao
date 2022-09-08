from django.conf import settings
from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase
from utils.paginations import EndlessPagination

NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        super(NewsFeedApiTests, self).setUp()
        self.marcus, self.marcus_client = self.create_user_and_client('marcus')
        self.fiona, self.fiona_client = self.create_user_and_client('fiona')

    def test_list(self):
        #has to login
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)

        # can't use post
        response = self.marcus_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)

        # nothing is showing when I am not following anyone
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        # I can see my own post
        self.marcus_client.post(POST_TWEETS_URL, {'content': 'Hello World!'})
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 1)

        # I can see others' posts whom I follow
        self.marcus_client.post(FOLLOW_URL.format(self.fiona.id))
        response = self.fiona_client.post(POST_TWEETS_URL,{
            'content': 'Hello Twitter!',
        })
        posted_tweet_id = response.data['id']
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['tweet']['id'], posted_tweet_id)

    def test_pagination(self):
        page_size = EndlessPagination.page_size
        followed_user = self.create_user('followed')
        newsfeeds = []
        for i in range(page_size * 2):
            tweet = self.create_tweet(followed_user)
            newsfeed = self.create_newsfeed(user=self.marcus, tweet=tweet)
            newsfeeds.append(newsfeed)

        newsfeeds = newsfeeds[::-1]

        # pull the first page
        response = self.marcus_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.data['has_next_page'], True)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['created_at'], newsfeeds[0].created_at)
        self.assertEqual(response.data['results'][1]['created_at'], newsfeeds[1].created_at)
        self.assertEqual(response.data['results'][page_size - 1]['created_at'], newsfeeds[page_size - 1].created_at)

        # pull the second page
        response = self.marcus_client.get(
            NEWSFEEDS_URL,
            {'created_at__lt': newsfeeds[page_size - 1].created_at},
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['results'][0]['created_at'], newsfeeds[page_size].created_at)
        self.assertEqual(response.data['results'][1]['created_at'], newsfeeds[page_size + 1].created_at)
        self.assertEqual(response.data['results'][page_size - 1]['created_at'], newsfeeds[2 * page_size - 1].created_at)

        # pull the latest newsfeeds
        response = self.marcus_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at}
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 0)
        # create new tweet and fanout to newsfeed
        new_tweet = self.create_tweet(followed_user)
        new_newsfeed = self.create_newsfeed(self.marcus, new_tweet)
        response = self.marcus_client.get(
            NEWSFEEDS_URL,
            {'created_at__gt': newsfeeds[0].created_at}
        )
        self.assertEqual(response.data['has_next_page'], False)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['created_at'], new_newsfeed.created_at)

    def test_user_cache(self):
        profile = self.fiona.profile
        profile.nickname = 'dapangzi'
        profile.save()
        self.assertEqual(self.fiona.username, 'fiona')
        self.create_newsfeed(self.fiona, self.create_tweet(self.marcus))
        self.create_newsfeed(self.fiona, self.create_tweet(self.fiona))

        response = self.fiona_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'fiona')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'dapangzi')
        self.assertEqual(results[1]['tweet']['user']['username'], 'marcus')

        self.fiona.username = 'fionaw'
        self.fiona.save()
        profile.nickname = 'xiaopangzi'
        profile.save()
        response = self.fiona_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'fionaw')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'xiaopangzi')
        self.assertEqual(results[1]['tweet']['user']['username'], 'marcus')

    def test_tweet_cache(self):
        tweet = self.create_tweet(self.marcus, 'content1')
        self.create_newsfeed(self.fiona, tweet)
        response = self.fiona_client.get(NEWSFEEDS_URL)
        result = response.data['results']
        self.assertEqual(result[0]['tweet']['user']['username'], 'marcus')
        self.assertEqual(result[0]['tweet']['content'], 'content1')

        # change the username
        self.marcus.username = 'marcusw'
        self.marcus.save()
        response = self.fiona_client.get(NEWSFEEDS_URL)
        result = response.data['results']
        self.assertEqual(result[0]['tweet']['user']['username'], 'marcusw')

        # change the content
        tweet.content = 'content2'
        tweet.save()
        response = self.fiona_client.get(NEWSFEEDS_URL)
        result = response.data['results']
        self.assertEqual(result[0]['tweet']['content'], 'content2')

    def _paginate_to_get_newsfeeds(self, client):
        response = client.get(NEWSFEEDS_URL)
        results = response.data['results']
        while response.data['has_next_page']:
            created_at__lt = response.data['results'][-1]['created_at']
            response = client.get(NEWSFEEDS_URL, {'created_at__lt': created_at__lt})
            results.extend(response.data['results'])
        return results

    def test_redis_list_limit(self):
        list_limit = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = 20
        users = [self.create_user('user{}'.format(i)) for i in range(5)]
        newsfeeds = []
        for i in range(list_limit + page_size):
            tweet = self.create_tweet(user=users[i % 5], content='feed{}'.format(i))
            feed = self.create_newsfeed(self.marcus, tweet)
            newsfeeds.append(feed)
        newsfeeds = newsfeeds[::-1]

        # only cached list_limit objects
        cached_newsfeeds = NewsFeedService.get_cached_newsfeeds(self.marcus.id)
        self.assertEqual(len(cached_newsfeeds), list_limit)
        self.assertEqual(NewsFeedService.count(self.marcus.id), list_limit + page_size)

        results = self._paginate_to_get_newsfeeds(self.marcus_client)
        self.assertEqual(len(results), list_limit + page_size)
        for i in range(list_limit + page_size):
            self.assertEqual(newsfeeds[i].created_at, results[i]['created_at'])

        # a followed user created a new tweet
        self.create_friendship(self.marcus, self.fiona)
        new_tweet = self.create_tweet(self.fiona, 'a new tweet')
        NewsFeedService.fanout_to_followers(new_tweet)

        def _test_newsfeeds_after_new_tweet_created():
            results = self._paginate_to_get_newsfeeds(self.marcus_client)
            self.assertEqual(len(results), list_limit + page_size + 1)
            self.assertEqual(results[0]['tweet']['id'], new_tweet.id)
            for i in range(list_limit + page_size):
                self.assertEqual(newsfeeds[i].created_at, results[i + 1]['created_at'])

        _test_newsfeeds_after_new_tweet_created()

        # cached expired
        self.clear_cache()
        _test_newsfeeds_after_new_tweet_created()