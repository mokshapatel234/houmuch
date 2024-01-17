from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from hotel_app_backend.messages import *
class CustomPagination(PageNumberPagination):
    page_size_query_param = 'per_page'
    page_size = 5

    def get_paginated_response(self, data):
        return Response({
            'result': True,
            'data': data,
            'pagination': {
                'current_page': self.page.number,
                'per_page': self.get_page_size(self.request),
                'total_docs': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages
            },
            'message': DATA_RETRIEVAL_MESSAGE
        })