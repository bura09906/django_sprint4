from django.core.paginator import Paginator

from django.conf import settings


def page_object(data, page_number):
    paginator = Paginator(data, settings.POSTS_ON_PAGE)
    page_obj = paginator.get_page(page_number)
    return page_obj
