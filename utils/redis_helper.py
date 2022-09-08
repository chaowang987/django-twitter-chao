from django_hbase.models import HBaseModel
from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer, HBaseModelSerializer
from django.conf import settings


class RedisHelper:

    @classmethod
    def load_objects(cls, key, lazy_load_objects, serializer=DjangoModelSerializer):
        conn = RedisClient.get_connection()

        # cache hit
        if conn.exists(key):
            serialized_list = conn.lrange(key, 0, -1)  # get value from start to end
            objects = []
            for serialized_data in serialized_list:
                deserialized_obj = serializer.deserialize(serialized_data)
                objects.append(deserialized_obj)
            return objects

        # cache miss
        objects = lazy_load_objects(settings.REDIS_LIST_LENGTH_LIMIT)
        cls._load_objects_to_cache(key, objects, serializer)
        return list(objects)

    @classmethod
    def push_object(cls, key, obj, lazy_load_objects):
        if isinstance(obj, HBaseModel):
            serializer = HBaseModelSerializer
        else:
            serializer = DjangoModelSerializer
        conn = RedisClient.get_connection()
        if conn.exists(key):
            serialized_data = serializer.serialize(obj)
            conn.lpush(key, serialized_data)
            conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)
            return
        objects = lazy_load_objects(settings.REDIS_LIST_LENGTH_LIMIT)
        cls._load_objects_to_cache(key, objects, serializer)

    @classmethod
    def _load_objects_to_cache(cls, key, objects, serializer):
        conn = RedisClient.get_connection()
        serialized_list = []
        # Can only cache the limit size objects
        for obj in objects:
            serialized_data = serializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def get_count_key(cls, obj, attr):
        return '{}.{}:{}'.format(obj.__class__.__name__, attr, obj.id)

    @classmethod
    def incr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if not conn.exists(key):
            conn.set(key, getattr(obj, attr))
            conn.exists(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        return conn.incr(key)

    @classmethod
    def decr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        if not conn.exists(key):
            conn.set(key, getattr(obj, attr))
            conn.exists(key, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        return conn.decr(key)

    @classmethod
    def get_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        count = conn.get(key)
        if count:
            return int(count)
        obj.refresh_from_db()
        count = getattr(obj, attr)
        conn.set(key, count)
        return count
