from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from dateutil import parser
from django.conf import settings
from utils.time_constants import MAX_TIMESTAMP


class EndlessPagination(BasePagination):
    
    page_size = 20

    def __init__(self):
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

    def paginate_ordered_list(self, reverse_ordered_list, request):
        # greater than basically means getting the updated info
        if 'created_at__gt' in request.query_params:
            try:
                created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            except ValueError:
                created_at__gt = int(request.query_params['created_at__gt'])
            objects = []
            for obj in reverse_ordered_list:
                if obj.created_at > created_at__gt:
                    objects.append(obj)
                else:
                    break
            self.has_next_page = False
            return objects

        # less than means getting older info
        index = 0
        if 'created_at__lt' in request.query_params:
            try:
                created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            except ValueError:
                created_at__lt = int(request.query_params['created_at__lt'])
            for index, obj in enumerate(reverse_ordered_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                reverse_ordered_list = []
        self.has_next_page = len(reverse_ordered_list) > index + self.page_size
        return reverse_ordered_list[index: index + self.page_size]

    def paginate_queryset(self, queryset, request, view=None):
        # if cache hit, it will return an ordered list instead of a queryset.
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            queryset = queryset.filter(created_at__gt=created_at__gt)
            self.has_next_page = False
            return queryset.order_by('-created_at')

        if 'created_at__lt' in request.query_params:
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)

        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[: self.page_size]

    def paginate_cached_list(self, cached_list, request):
        paginated_list = self.paginate_ordered_list(cached_list, request)

        if 'created_at__gt' in request.query_params:
            return paginated_list
        if self.has_next_page:
            return paginated_list
        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list
        return None

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        })

    def paginate_hbase(self, hb_model, row_key_prefix, request):
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            start = (*row_key_prefix, created_at__gt)
            stop = (*row_key_prefix, MAX_TIMESTAMP)
            objects = hb_model.filter(start=start, stop=stop)
            if len(objects) and objects[0].created_at == int(created_at__gt):
                objects = objects[:0:-1]
            else:
                objects = objects[::-1]
            self.has_next_page = False
            return objects

        if 'created_at__lt' in request.query_params:
            created_at__lt = request.query_params['created_at__lt']
            start = (*row_key_prefix, created_at__lt)
            stop = (*row_key_prefix, None)
            objects = hb_model.filter(start=start, stop=stop, limit=self.page_size + 2, reverse=True)
            if len(objects) and objects[0].created_at == int(created_at__lt):
                objects = objects[1:]
            if len(objects) > self.page_size:
                objects = objects[:-1]
                self.has_next_page = True
            else:
                self.has_next_page = False
            return objects

        prefix = (*row_key_prefix, None)
        objects = hb_model.filter(prefix=prefix, limit=self.page_size + 1, reverse=True)
        if len(objects) > self.page_size:
            objects = objects[:-1]
            self.has_next_page = True
        else:
            self.has_next_page = False
        return objects