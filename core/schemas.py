from ninja import Schema
from typing import Optional
from datetime import date

class BranchSchema(Schema):
    name: str
    address: Optional[str]

class RoleSchema(Schema):
    name: str

class DealerSchema(Schema):
    name: str
    mobile_number: str
    company_name: Optional[str]
    email: Optional[str]
    address_line1: str
    address_line2: Optional[str]
    pincode: Optional[str]
    state: Optional[str]
    branch: int

class ProductSupplySchema(Schema):
    dealer: int
    product_name: str
    invoice_number: str
    serial_number: str
    vehicle_model: Optional[str]
    purchase_date: Optional[date]
    remarks: Optional[str]
    count: Optional[int] = 1
