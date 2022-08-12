from rest_framework.views import exception_handler as drf_exception_handler
from ratelimit.exceptions import Ratelimited
from rest_framework import status


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if isinstance(exc, Ratelimited):
        response.data['detail'] = 'Too many requests, please try again later.'
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
    return response