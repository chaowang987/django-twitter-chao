from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):

        # N query。错误的方法
        # followers = FriendshipService.get_followers()
        # for follower in followers:
        #     NewsFeed.objects.create(user=follower, tweet=tweet)
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in FriendshipService.get_followers()
        ]
        # 把自己也加入到newsfeed里，因为自己也想看到
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        NewsFeed.objects.bulk_create(newsfeeds)