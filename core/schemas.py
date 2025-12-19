from ninja import Schema, Field
from typing import Optional, List
from datetime import date
from pydantic import EmailStr, BaseModel

from core.responses import PaginationSchema


# ============================================================================
# Authentication Schemas
# ============================================================================

class LoginRequest(Schema):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh: str


class SignupSchema(Schema):
    username: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ForgotPasswordRequest(Schema):
    email: EmailStr


class VerifyOTPRequest(Schema):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(Schema):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)


class UserInfo(Schema):
    id: int
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_staff: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class TokenResponse(Schema):
    access: str
    refresh: str
    user: UserInfo


# ============================================================================
# Role Schemas
# ============================================================================

class RoleSchema(Schema):
    name: str = Field(..., min_length=1, max_length=100)


class RoleResponseSchema(RoleSchema):
    id: int


# ============================================================================
# Branch Schemas
# ============================================================================

class BranchSchema(Schema):
    name: str = Field(..., min_length=1, max_length=150)
    address: Optional[str] = None


class BranchResponseSchema(BranchSchema):
    id: int
    created_at: Optional[date] = None


# ============================================================================
# Dealer Schemas
# ============================================================================

class DealerInSchema(Schema):
    name: str = Field(..., min_length=1, max_length=100)
    mobile_number: str = Field(..., min_length=10, max_length=20, pattern=r'^\+?[0-9]+$')
    company_name: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$')
    state: Optional[str] = Field(None, max_length=100)
    branch: int = Field(..., gt=0)


class DealerSchema(Schema):
    id: int
    name: str
    mobile_number: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    branch: int
    branch_name: Optional[str] = None
    user_id: Optional[int] = None
    created_at: Optional[date] = None

    class Config:
        from_attributes = True


# ============================================================================
# UPDATED SCHEMAS - Add these to your schemas.py
# ============================================================================

class DealerDetailsSchema(Schema):
    """Dealer details with purchase statistics"""
    id: int
    name: str
    mobile_number: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    pincode: Optional[str] = None
    state: Optional[str] = None
    branch_id: int
    branch_name: str
    vehicle_count: int
    battery_count: int
    charger_count: int
    total_purchases: int


class DealerDetailsResponse(Schema):
    """Response schema for dealer details"""
    dealer: DealerDetailsSchema
    purchases: List['ProductSupplyResponseSchema']
    pagination: 'PaginationSchema'

# ============================================================================
# Product Supply Schemas
# ============================================================================

class ProductSupplySchema(Schema):
    dealer: int
    branch: int  
    product_name: str
    invoice_number: str
    serial_number: str
    purchase_date: Optional[date] = None
    count: int = 1

    # Vehicle info
    chase_number: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    vehicle_warranty: Optional[str] = None
    controller: Optional[str] = None
    motor: Optional[str] = None

    # Battery info
    battery_number: Optional[str] = None
    battery_model: Optional[str] = None
    battery_variant: Optional[str] = None
    battery_warranty: Optional[str] = None
    bulging_warranty: Optional[str] = None

    # Charger info
    charger_number: Optional[str] = None
    charger_model: Optional[str] = None
    charger_type: Optional[str] = None
    charger_variant: Optional[str] = None
    charger_warranty: Optional[str] = None

    remarks: Optional[str] = None


class ProductSupplyResponseSchema(Schema):
    id: int
    dealer: int
    dealer_name: Optional[str] = None
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    product_name: str
    invoice_number: str
    serial_number: str
    purchase_date: Optional[date] = None
    count: int
    chase_number: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_variant: Optional[str] = None
    vehicle_warranty: Optional[str] = None
    controller: Optional[str] = None
    motor: Optional[str] = None
    battery_number: Optional[str] = None
    battery_model: Optional[str] = None
    battery_variant: Optional[str] = None
    battery_warranty: Optional[str] = None
    bulging_warranty: Optional[str] = None
    charger_number: Optional[str] = None
    charger_model: Optional[str] = None
    charger_type: Optional[str] = None
    charger_variant: Optional[str] = None
    charger_warranty: Optional[str] = None
    remarks: Optional[str] = None
    created_at: Optional[date] = None


# ============================================================================
# Composite Schemas
# ============================================================================

class DetailsSchema(Schema):
    roles: List[RoleResponseSchema]
    branches: List[BranchResponseSchema]
    dealers: List[DealerSchema]


class DetailsResponse(Schema):
    status: bool
    message: str
    data: DetailsSchema