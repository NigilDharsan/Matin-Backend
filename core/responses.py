from typing import Generic, TypeVar, Optional, List, Any
from ninja import Schema
from datetime import datetime

T = TypeVar("T")

class ErrorSchema(Schema):
    message: str
    code: str
    details: Optional[dict] = None

class PaginationSchema(Schema):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    page_size: int
    current_page: int
    total_pages: int

class BaseResponseSchema(Schema, Generic[T]):
    success: bool
    message: Optional[str] = None
    error: Optional[ErrorSchema] = None
    data: Optional[T] = None
    timestamp: datetime = None

    @staticmethod
    def success_response(data: Any = None, message: str = "Success") -> dict:
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now()
        }

    @staticmethod
    def error_response(message: str, code: str = "ERROR", details: dict = None) -> dict:
        return {
            "success": False,
            "error": {
                "message": message,
                "code": code,
                "details": details
            },
            "timestamp": datetime.now()
        }

class PaginatedResponseSchema(BaseResponseSchema, Generic[T]):
    pagination: Optional[PaginationSchema] = None

    @staticmethod
    def success_response(data: Any = None, message: str = "Success", pagination: PaginationSchema = None) -> dict:
        response = BaseResponseSchema.success_response(data, message)
        response["pagination"] = pagination
        return response