from typing import Type, TypeVar, List, Any
from django.db.models import QuerySet
from django.core.paginator import Paginator
from ninja import Schema
from .responses import PaginationSchema, BaseResponseSchema, PaginatedResponseSchema

T = TypeVar('T')

def paginate_queryset(
    queryset: QuerySet,
    page: int = 1,
    page_size: int = 10,
    url_path: str = None
) -> tuple[List[Any], PaginationSchema]:
    """Paginates a queryset and returns items and pagination info"""
    paginator = Paginator(queryset, page_size)
    
    # Ensure page is within valid range
    page = min(max(1, page), paginator.num_pages)
    
    # Get page object
    page_obj = paginator.page(page)
    
    # Calculate next/previous URLs if base URL provided
    next_page = None
    prev_page = None
    if url_path:
        if page_obj.has_next():
            next_page = f"{url_path}?page={page_obj.next_page_number()}&page_size={page_size}"
        if page_obj.has_previous():
            prev_page = f"{url_path}?page={page_obj.previous_page_number()}&page_size={page_size}"

    # Create pagination info
    pagination = PaginationSchema(
        count=paginator.count,
        next=next_page,
        previous=prev_page,
        page_size=page_size,
        current_page=page,
        total_pages=paginator.num_pages
    )

    return list(page_obj.object_list), pagination

def create_paginated_response(
    items: List[Any],
    pagination: PaginationSchema,
    message: str = "Success"
) -> dict:
    """Creates a standardized paginated response"""
    return PaginatedResponseSchema.success_response(
        data=items,
        message=message,
        pagination=pagination
    )