from rest_framework import serializers
from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForTweet


class TweetSerializer(serializers.ModelSerializer):
    # "user": {
    #     "id": 6,
    #     "username": "twitter_test1"
    # }
    # 如果不写就是只有 "user": 6, 不会再展开
    user = UserSerializerForTweet()

    class Meta:
        model = Tweet
        fields = ('id', 'user', 'created_at', 'content',)


class TweetSerializerForCreate(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Tweet
        fields = ('content',)

    # 在serializer.save()的时候会执行这个，如果validated_data是一个instance，就update，
    # 否则就create
    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet