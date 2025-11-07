from ninja import Router
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Role,Branch,Dealer,ProductSupply
from django.db.models import Sum
from .schemas import (
    BranchResponseSchema,
    DealerResponseSchema,
    DetailsResponse,
    DetailsSchema,
    LoginRequest,
    ProductSupplyResponseSchema,
    RoleResponseSchema,
    RoleSchema,
    BranchSchema,
    DealerInSchema,
    ProductSupplySchema,
    TokenResponse,
    UserInfo,
)
from .responses import BaseResponseSchema, PaginatedResponseSchema
from .utils import paginate_queryset, create_paginated_response
from .auth import get_auth_class

# Create an unprotected router for login
auth_router = Router()

# Main router - uses dynamic auth based on settings
auth_class = get_auth_class()
if auth_class:
    router = Router(auth=auth_class())
else:
    router = Router()  # No authentication when API_AUTHENTICATION_ENABLED is False


def _role_to_dict(role: Role) -> dict:
    return {
        'id': role.id,
        'name': role.name,
    }


def _branch_to_dict(branch: Branch) -> dict:
    return {
        'id': branch.id,
        'name': branch.name,
        'address': branch.address,
    }


def _dealer_to_dict(dealer: Dealer) -> dict:
    return {
        'id': dealer.id,
        'name': dealer.name,
        'mobile_number': dealer.mobile_number,
        'company_name': dealer.company_name,
        'email': dealer.email,
        'address_line1': dealer.address_line1,
        'address_line2': dealer.address_line2,
        'pincode': dealer.pincode,
        'state': dealer.state,
        'branch': dealer.branch_id,
        'created_at': dealer.created_at.date() if dealer.created_at else None,
        'branch_name': dealer.branch.name if dealer.branch else None,
    }


def _supply_to_dict(s: ProductSupply) -> dict:
    return {
        'id': s.id,
        'dealer': s.dealer_id,
        'dealer_name': s.dealer.name if s.dealer else None,
        'product_name': s.product_name,
        'invoice_number': s.invoice_number,
        'serial_number': s.serial_number,
        'vehicle_model': s.vehicle_model,
        'purchase_date': s.purchase_date,
        'remarks': s.remarks,
        'count': s.count,
        'created_at': s.created_at.date() if s.created_at else None
    }

@auth_router.post('/login')
def login(request,data:LoginRequest=None):

    if data:
        username = data.username
        password = data.password

    user=authenticate(username=username,password=password)
    if not user:
        return {
            'status': False,
            'message': 'Invalid credentials',
        }
    refresh=RefreshToken.for_user(user)
    token_data = TokenResponse(
        access=str(refresh.access_token),
        refresh=str(refresh),
        user=UserInfo.from_orm(user)
    )

    return 200, {
            'status': True,
            'message': 'Login successful',
            'data': token_data.dict()
        }

@router.get('/details',response=DetailsResponse)
def list_roles(request):
    response = {
        "roles": [_role_to_dict(r) for r in Role.objects.all()],
        "branches": [_branch_to_dict(b) for b in Branch.objects.all()],
        "dealers": [_dealer_to_dict(d) for d in Dealer.objects.all()]
    }
             
    return {
            'status': True,
            'message': 'Datas retrieved successfully',
            'data': response
        }


@router.post('/roles',response=RoleResponseSchema)
def add_role(request,data:RoleSchema):
    obj=Role.objects.create(**data.dict())
    return _role_to_dict(obj)

@router.post('/branches',response=BranchResponseSchema)
def add_branch(request,data:BranchSchema):
    obj=Branch.objects.create(**data.dict())
    return _branch_to_dict(obj)

@router.post('/dealers',response=DealerResponseSchema)
def add_dealer(request,data:DealerInSchema):
    payload = data.dict()
    # accept branch as an int id in the schema; use branch_id to create
    branch_id = payload.pop('branch', None)
    if branch_id is not None:
        obj = Dealer.objects.create(branch_id=branch_id, **payload)
    else:
        obj = Dealer.objects.create(**payload)
    return _dealer_to_dict(obj)

@router.get('/supplies', response=PaginatedResponseSchema[list[ProductSupplyResponseSchema]])
def list_supplies(request, page: int = 1, page_size: int = 10):
    supplies = ProductSupply.objects.all()
    items, pagination = paginate_queryset(
        supplies, 
        page=page, 
        page_size=page_size,
        url_path="/api/supplies"
    )
    return PaginatedResponseSchema.success_response(
        data=[_supply_to_dict(s) for s in items],
        pagination=pagination,
        message="Product supplies retrieved successfully"
    )

@router.post('/supplies', response=BaseResponseSchema[ProductSupplyResponseSchema])
def add_supply(request, data: ProductSupplySchema):
    try:
        payload = data.dict()
        # accept dealer as an int id in the schema; use dealer_id to create
        dealer_id = payload.pop('dealer', None)
        if dealer_id is not None:
            obj = ProductSupply.objects.create(dealer_id=dealer_id, **payload)
        else:
            obj = ProductSupply.objects.create(**payload)
        return BaseResponseSchema.success_response(
            data=_supply_to_dict(obj),
            message="Product supply created successfully"
        )
    except Exception as e:
        return BaseResponseSchema.error_response(
            message=str(e),
            code="SUPPLY_CREATE_ERROR"
        )

@router.get('/dashboard')
def dashboard_counts(request):
    # aggregate vehicle counts per product_name by summing the `count` field
    try:
        product_counts = (
            ProductSupply.objects
            .values('product_name')
            .annotate(total=Sum('count'))
            .order_by('-total')
        )
        print("DEBUG PRODUCT COUNTS:", list(product_counts))  # 👈 Add this line
        response = {
                'vehicle_count': 0,
                'battery_count': 0,
                'charger_count': 0,
            }
        
        for p in product_counts:
            name = p['product_name'].strip().lower()
            total = p['total'] or 0
            key = f"{name}_count"  
            if key in response:
                response[key] = total  

        response.update(
            {
            'dealer_count': Dealer.objects.count(),
            'branch_count': Branch.objects.count()
            }
        )
        return {
                'status': True,
                'message': 'Dashboard counts fetched successfully',
                'data': response
        }
    except Exception as e:
        # handle error gracefully
        return {
            'status': False,
            'message': f'Error fetching dashboard counts: {str(e)}',
        }