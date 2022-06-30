class TweetPhotoStatus:

    PENDING = 0
    APPROVED = 1
    REJECTED = 2


TWEET_PHOTO_STATUS_CHOICES = (
    (TweetPhotoStatus.PENDING, 'pending'),
    (TweetPhotoStatus.APPROVED, 'approved'),
    (TweetPhotoStatus.REJECTED, 'rejected'),
)

TWEET_PHOTOS_UPLOAD_LIMIT = 9