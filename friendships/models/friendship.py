from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_delete
from friendships.listeners import friendship_changed
from utils.memcached_helper import MemcachedHelper


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='following_friendship_set',
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='follower_friendship_set',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (
            # 获取我关注的所有人，按照时间顺序排序
            ('from_user_id', 'created_at'),
            # 获取关注我的所有人，按照时间顺序排序
            ('to_user_id', 'created_at'),
        )
        unique_together = (('from_user_id', 'to_user_id'),)
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.from_user_id} followed {self.to_user_id}'

    @property
    def cached_from_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.from_user_id)

    @property
    def cached_to_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.to_user_id)


pre_delete.connect(friendship_changed, sender=Friendship)
post_save.connect(friendship_changed, sender=Friendship)
