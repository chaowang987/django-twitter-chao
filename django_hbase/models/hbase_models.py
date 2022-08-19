from .exceptions import EmptyColumnError, BadRowKeyError
from .fields import HBaseField, IntegerField, TimeStampField
from django.conf import settings
from django_hbase.client import HBaseClient


class HBaseModel:

    # HBaseModel.create(from_user_id=1, to_user_id=2, created_at=ts)
    # instance = HBaseModel(from_user_id=1, to_user_id=2, created_at=ts)
    # instance.save()
    # instance.from_user_id = 2
    # instance.save()
    class Meta:
        table_name = None
        row_key = ()

    def __init__(self, **kwargs):
        for key, field in self.get_field_hash().items():
            value = kwargs.get(key)
            setattr(self, key, value)

    @classmethod
    def get_field_hash(cls):
        field_hash = {}
        for field in cls.__dict__:
            field_obj = getattr(cls, field)
            if isinstance(field_obj, HBaseField):
                field_hash[field] = field_obj
        return field_hash

    @classmethod
    def serialize_field(cls, field, value):
        value = str(value)
        if isinstance(field, IntegerField):
            # need add 0 in front cause the sorting is lexicographical order
            value = str(value)
            while len(value) < 16:
                value = '0' + value
        return value if not field.reverse else value[::-1]

    @classmethod
    def serialize_row_key(cls, data):
        """
        key1: val1
        key2: val2
        key3: val3
        b"val1:val2:val3"
        """
        field_hash = cls.get_field_hash()
        values = []
        for key, field in field_hash.items():
            if field.column_family:
                continue
            value = data.get(key)
            if value is None:
                raise BadRowKeyError(f'{key} is missing in the row key.')
            value = cls.serialize_field(field, value)
            if ':' in value:
                raise BadRowKeyError(f"{key} should not contain ':' in value: {value}.")
            values.append(value)
        return bytes(':'.join(values), encoding='utf-8')

    @classmethod
    def serialize_row_data(cls, data):
        """
        column key: column_family: key
        column value: serialized_value
        """
        row_data = {}
        field_hash = cls.get_field_hash()
        for key, field in field_hash.items():
            if not field.column_family:
                continue
            column_key = '{}:{}'.format(field.column_family, key)
            column_value = data.get(key)
            if column_value is None:
                continue
            row_data[column_key] = cls.serialize_field(field, column_value)
        return row_data

    @classmethod
    def deserialize_row_key(cls, row_key):
        """
        "val1" => {'key1': val1, 'key2': None, 'key3': None}
        "val1:val2" => {'key1': val1, 'key2': val2, 'key3': None}
        "val1:val2:val3" => {'key1': val1, 'key2': val2, 'key3': val3}
        """
        data = {}
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')
        row_key = row_key + ':'
        for key in cls.Meta.row_key:
            index = row_key.find(':')
            if index == -1:
                break
            data[key] = cls.deserialize_field(key, row_key[:index])
            row_key = row_key[index + 1:]
        return data

    @classmethod
    def deserialize_field(cls, key, value):
        field = cls.get_field_hash()[key]
        if field.reverse:
            value = value[::-1]
        if field.field_type in [IntegerField.field_type, TimeStampField.field_type]:
            return int(value)
        return value

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    def save(self):
        row_data = self.serialize_row_data(self.__dict__)
        # if row_data is empty, there will be no column_key and values, then hbase will not save anything
        # so we can raise an exception to avoid to save null data
        if len(row_data) == 0:
            raise EmptyColumnError()
        table = self.get_table()
        table.put(self.row_key, row_data)

    @classmethod
    def get_table(cls):
        conn = HBaseClient.get_connection()
        return conn.table(cls.get_table_name())

    @property
    def row_key(self):
        return self.serialize_row_key(self.__dict__)

    @classmethod
    def init_from_row(cls, row_key, row_data):
        if not row_data:
            return None
        data = cls.deserialize_row_key(row_key)
        for column_key, column_data in row_data.items():
            # remove column family
            column_key = column_key.decode('utf-8')
            key = column_key[column_key.find(':') + 1:]
            data[key] = cls.deserialize_field(key, column_data)
        return cls(**data)

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs) # no need to expand the dict
        table = cls.get_table()
        row = table.row(row_key)
        return cls.init_from_row(row_key, row)

    @classmethod
    def get_table_name(cls):
        if not cls.Meta.table_name:
            raise NotImplementedError('Missing table_name in HBaseModel meta class')
        if settings.TESTING:
            return f'test_{cls.Meta.table_name}'
        return cls.Meta.table_name

    @classmethod
    def drop_table(cls):
        if not settings.TESTING:
            raise Exception('You can not drop table outside of unit tests')
        conn = HBaseClient.get_connection()
        conn.delete_table(cls.get_table_name(), True)

    @classmethod
    def create_table(cls):
        if not settings.TESTING:
            raise Exception('You can not create table outside of unit tests')
        conn = HBaseClient.get_connection()
        tables = [table.decode('utf-8') for table in conn.tables()]
        if cls.get_table_name() in tables:
            return
        column_families = {
            field.column_family: dict()
            for key, field in cls.get_field_hash().items()
            if field.column_family is not None
        }
        conn.create_table(cls.get_table_name(), column_families)


