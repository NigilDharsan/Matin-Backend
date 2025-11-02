from ninja import Schema
from typing import Optional, Generic, TypeVar, List
from datetime import date

# Generic response wrapper
T = TypeVar('T')

class ApiResponse(Schema, Generic[T]):
    """Standard API response wrapper"""
    status: str
    message: str
    data: Optional[T] = None

class ErrorResponse(Schema):
    """Standard error response"""
    status: str = "failed"
    message: str
    error: Optional[str] = None
    error_code: Optional[str] = None

# Entity Schemas
class RoleSchema(Schema):
    id: Optional[int] = None
    name: str
    
    class Config:
        from_attributes = True

class BranchSchema(Schema):
    id: Optional[int] = None
    name: str
    address: Optional[str] = None
    
    class Config:
        from_attributes = True

class DealerSchema(Schema):
    id: Optional[int] = None
    name: str
    mobile_number: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    branch: int
    
    class Config:
        from_attributes = True

class ProductSupplySchema(Schema):
    id: Optional[int] = None
    dealer: int
    product_name: str
    invoice_number: str
    serial_number: str
    vehicle_model: Optional[str] = None
    purchase_date: Optional[date] = None
    remarks: Optional[str] = None
    count: Optional[int] = 1
    
    class Config:
        from_attributes = True

# Authentication Schemas
class LoginRequest(Schema):
    username: str
    password: str

class UserInfo(Schema):
    id: int
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_staff: bool
    is_active: bool
    
    class Config:
        from_attributes = True  # Enables from_orm() method

class TokenResponse(Schema):
    access: str
    refresh: str
    user: UserInfo

class DashboardData(Schema):
    vehicle_count: int
    dealer_count: int
    branch_count: int