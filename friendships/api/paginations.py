from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FriendshipPagination(PageNumberPagination):
    # default page size if it is not specified
    page_size = 20
    # default page_size_query_param is None which means it does not allow user to customize page size
    #  in url /api/xxx/?size=10
    page_size_query_param = 'size'
    # max page size
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'total_results': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page_number': self.page.number,
            'has_next_page': self.page.has_next(),
            'results': data,
        })
