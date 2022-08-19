from django_hbase import models


class HBaseFollowing(models.HBaseModel):
    """
    row_key: from_user_id + created_at
    row_data: to_user_id
    """
    from_user_id = models.IntergerField(reverse=True)
    created_at = models.TimeStampField()
    to_user_id = models.IntergerField(column_family='cf')

    class Meta:
        table_name = 'twitter following'
        row_key = ('from_user_id', 'created_at')


class HBaseFollower(models.HBaseModel):
    """
    row_key: to_user_id + created_at
    row_data: from_user_id
    """
    to_user_id = models.IntergerField(reverse=True)
    created_at = models.TimeStampField()
    from_user_id = models.IntergerField(column_family='cf')

    class Meta:
        table_name = 'twitter_followers'
        row_key = ('to_user_id', 'created_at')
