from django.conf import settings
from django.core.paginator import Paginator


def get_page_obj(request, posts):
    paginator = Paginator(posts, settings.PAGE_LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
