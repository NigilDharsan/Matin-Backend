# from ninja import Schema
# from typing import Optional
# from datetime import date

# class BranchSchema(Schema):
#     name: str
#     address: Optional[str]

# class RoleSchema(Schema):
#     name: str

# class DealerSchema(Schema):
#     name: str
#     mobile_number: str
#     company_name: Optional[str]
#     email: Optional[str]
#     address_line1: str
#     address_line2: Optional[str]
#     pincode: Optional[str]
#     state: Optional[str]
#     branch: int

# class ProductSupplySchema(Schema):
#     dealer: int
#     product_name: str
#     invoice_number: str
#     serial_number: str
#     vehicle_model: Optional[str]
#     purchase_date: Optional[date]
#     remarks: Optional[str]
#     count: Optional[int] = 1



# class BranchResponseSchema(BranchSchema):
#     id: int

# class RoleResponseSchema(RoleSchema):
#     id: int

# class DealerResponseSchema(DealerSchema):
#     id: int

# class ProductSupplyResponseSchema(ProductSupplySchema):
#     id: int


from ninja import Schema, Field
from typing import Optional, List
from datetime import date
from pydantic import EmailStr, constr
from django.core.validators import MinLengthValidator, RegexValidator

# Base Schemas for creation/update
class BranchSchema(Schema):
    name: str = Field(..., min_length=1, max_length=150)
    address: Optional[str] = None

class RoleSchema(Schema):
    name: str = Field(..., min_length=1, max_length=100)

class UserInSchema(Schema):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)


class SignupSchema(Schema):
    username: Optional[str] = None
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # Optional: link this user to an existing Dealer record (by id)
    # dealer_id: Optional[int] = None

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
    # Optional user id to associate an AdminUser account to this Dealer
    # user: Optional[int] = None

class CustomerInSchema(Schema):
    name: str = Field(..., min_length=1, max_length=150)
    mobile_number: str = Field(..., min_length=10, max_length=20, pattern=r'^\+?[0-9]+$')
    email: EmailStr
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = None
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$')
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class ProductRegisterSchema(Schema):
    product_name: str = Field(..., min_length=1, max_length=150)
    invoice_number: str = Field(..., min_length=1, max_length=50)
    serial_number: str = Field(..., min_length=1, max_length=150)
    invoice_date: date
    warranty_start_date: date
    warranty_end_date: date
    dealer_id: int
    customer_id: int

class ProductSupplySchema(Schema):
    dealer: int = Field(..., gt=0)
    product_name: str = Field(..., min_length=1, max_length=150)
    invoice_number: str = Field(..., min_length=1, max_length=50)
    serial_number: str = Field(..., min_length=1, max_length=150)
    vehicle_model: Optional[str] = None
    purchase_date: Optional[date] = None
    remarks: Optional[str] = None
    count: int = Field(default=1, gt=0)

# Response Schemas with IDs
class BranchResponseSchema(BranchSchema):
    id: int
    created_at: Optional[date] = None

class RoleResponseSchema(RoleSchema):
    id: int

class DealerResponseSchema(Schema):
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
    # user_id: Optional[int] = None
    created_at: date
    branch_name: Optional[str] = None

class ProductSupplyResponseSchema(Schema):
    id: int
    dealer: int
    dealer_name: Optional[str] = None
    product_name: str
    invoice_number: str
    serial_number: str
    vehicle_model: Optional[str] = None
    purchase_date: Optional[date] = None
    remarks: Optional[str] = None
    count: int
    created_at: date

# List Response Schemas
class BranchListSchema(Schema):
    branches: List[BranchResponseSchema]

class RoleListSchema(Schema):
    roles: List[RoleResponseSchema]

class DealerListSchema(Schema):
    dealers: List[DealerResponseSchema]

class ProductSupplyListSchema(Schema):
    supplies: List[ProductSupplyResponseSchema]

# Composite Response Schemas
class DetailsSchema(Schema):
    roles: List[RoleResponseSchema]
    branches: List[BranchResponseSchema]
    dealers: List[DealerResponseSchema]

class DetailsResponse(Schema):
    status: bool
    message: str
    data: DetailsSchema

# Filter Schemas
class DealerFilterSchema(Schema):
    branch_id: Optional[int] = None
    search: Optional[str] = None
    state: Optional[str] = None

class ProductSupplyFilterSchema(Schema):
    dealer_id: Optional[int] = None
    product_name: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None

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

class LoginRequest(Schema):
    username: str
    password: str
