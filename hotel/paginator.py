from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
class CustomPagination(PageNumberPagination):
    def __init__(self, per_page=5):
        self.page_size = per_page
        super().__init__()

    def get_paginated_response(self, data, message='Data found.'):
        return Response({
            'result': True,
            'data': data,
            'pagination': {
                'current_page': self.page.number,
                'per_page': self.page_size,
                'total_docs': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages
            },
            'message': message
        })