class  HBaseField:
    field_type = None

    def __init__(self, reverse=False, column_family=None):
        self.reverse = reverse
        self.column_family = column_family


class IntergerField(HBaseField):
    field_type = 'int'


class TimeStampField(HBaseField):
    field_type = 'timestamp'