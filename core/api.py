from tokenize import TokenError
from ninja import Router
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Role,Branch,Dealer,ProductSupply
from django.db.models import Sum, Q
from .schemas import (
    BranchResponseSchema,
    DealerResponseSchema,
    DetailsResponse,
    DetailsSchema,
    LoginRequest,
    RefreshRequest,
    SignupSchema,
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
from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from django.db import transaction

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
        'user_id': dealer.user_id,
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
        'purchase_date': s.purchase_date,
        'count': s.count,
        'chase_number': s.chase_number,
        'vehicle_model': s.vehicle_model,
        'vehicle_variant': s.vehicle_variant,
        'vehicle_warranty': s.vehicle_warranty,
        'controller': s.controller,
        'motor': s.motor,
        'battery_number': s.battery_number,
        'battery_model': s.battery_model,
        'battery_variant': s.battery_variant,
        'battery_warranty': s.battery_warranty,
        'bulging_warranty': s.bulging_warranty,
        'charger_number': s.charger_number,
        'charger_model': s.charger_model,
        'charger_type': s.charger_type,
        'charger_variant': s.charger_variant,
        'charger_warranty': s.charger_warranty,
        'remarks': s.remarks,
        'created_at': s.created_at.date() if s.created_at else None,
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

@auth_router.post("/refresh")
def refresh_token(request, data: RefreshRequest):
    """
    Accepts a refresh token and returns new access & refresh tokens
    """
    try:
        old_refresh = RefreshToken(data.refresh)
        user_id = old_refresh.get("user_id")

        if not user_id:
            return 401, {
                "status": False,
                "message": "Invalid token: user_id missing"
            }

        # ✅ Fetch the user using Django’s user model
        user_model = get_user_model()
        user = user_model.objects.get(id=user_id)

        # ✅ Generate new tokens
        new_refresh = RefreshToken.for_user(user)
        new_access = str(new_refresh.access_token)

        return 200, {
            "status": True,
            "message": "Access and refresh tokens refreshed successfully",
            "data": {
                "access": new_access,
                "refresh": str(new_refresh)
            }
        }

    except get_user_model().DoesNotExist:
        return 404, {
            "status": False,
            "message": "User not found"
        }

    except TokenError as e:
        return 401, {
            "status": False,
            "message": "Invalid or expired refresh token",
            "error": str(e)
        }

    except Exception as e:
        return 500, {
            "status": False,
            "message": f"Unexpected error: {str(e)}"
        }

@auth_router.post('/signup', response={201: BaseResponseSchema[TokenResponse], 400: dict})
def signup(request, data: SignupSchema):
    """Create a new AdminUser and optionally link to a Dealer via dealer_id.
    Returns JWT tokens on success (same shape as login).
    """
    User = get_user_model()
    # basic validation
    username = data.username or data.email.split('@')[0]
    if User.objects.filter(username=username).exists():
        raise HttpError(400, "username already exists")
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "email already exists")

    try:
        user = User.objects.create_user(
            username=username,
            email=data.email,
            password=data.password,
            first_name=(data.first_name or ""),
            last_name=(data.last_name or ""),
            is_staff=True
        )

        refresh = RefreshToken.for_user(user)
        token_data = TokenResponse(
            access=str(refresh.access_token),
            refresh=str(refresh),
            user=UserInfo.from_orm(user)
        )

        return 201, BaseResponseSchema.success_response(
            data=token_data,
            message="Signup successful"
        )
    except HttpError:
        raise
    except Exception as e:
        # on unexpected errors respond with 400
        raise HttpError(400, str(e))

@router.get('/details',response=DetailsResponse)
def list_roles(request):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        raise HttpError(401, "Unauthorized")

    # Staff/superuser: return everything
    if getattr(user, 'is_superuser', False):
        roles_qs = Role.objects.all()
        branches_qs = Branch.objects.all()
        dealers_qs = Dealer.objects.all()
    elif getattr(user, 'is_staff', False):
        # Staff can see items they created and items without creator
        roles_qs = Role.objects.filter(Q(created_by=user))
        branches_qs = Branch.objects.filter(Q(created_by=user))
        dealers_qs = Dealer.objects.filter(Q(created_by=user))
    else:
        roles_qs = user.created_roles.all()
        branches_qs = user.created_branches.all()
        dealers_qs = user.created_dealers.all()
    response = {
        "roles": [_role_to_dict(r) for r in roles_qs],
        "branches": [_branch_to_dict(b) for b in branches_qs],
        "dealers": [_dealer_to_dict(d) for d in dealers_qs]
    }

    return {
        'status': True,
        'message': 'Data retrieved successfully',
        'data': response
    }


@router.post('/roles',response=RoleResponseSchema)
def add_role(request,data:RoleSchema):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        raise HttpError(401, "Unauthorized")
    if not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
        raise HttpError(403, "Forbidden")

    obj = Role.objects.create(created_by=user, **data.dict())
    return _role_to_dict(obj)

@router.post('/branches',response=BranchResponseSchema)
def add_branch(request,data:BranchSchema):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        raise HttpError(401, "Unauthorized")
    if not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
        raise HttpError(403, "Forbidden")

    obj = Branch.objects.create(created_by=user, **data.dict())
    return _branch_to_dict(obj)

@router.get('/dealers', response=DealerResponseSchema)
def list_dealers(request):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        raise HttpError(401, "Unauthorized")

    try:
        dealers_qs = Dealer.objects.all()

        return {
            'status': 'success',
            'message': 'dealer(s) retrieved successfully',
            'data': [_dealer_to_dict(s) for s in dealers_qs],
        }
    except Exception as e:
        raise HttpError(400, f"Error listing dealers: {e}")



@router.post('/dealers',response=DealerResponseSchema)
def add_dealer(request,data:DealerInSchema):
    user = getattr(request, 'user', None)
    if user is None or not getattr(user, 'is_authenticated', False):
        raise HttpError(401, "Unauthorized")
        
    payload = data.dict()
    # accept branch as an int id in the schema; use branch_id to create
    branch_id = payload.pop('branch', None)
    if branch_id is not None:
        obj = Dealer.objects.create(branch_id=branch_id, created_by=user, **payload)
        # Create user for this dealer
        User = get_user_model()
        username = payload.get('mobile_number')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            raise HttpError(400, "Username already exists")
        if User.objects.filter(email=payload.get('email')).exists():
            raise HttpError(400, "Email already exists")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=payload.get('email'),
            password=payload.get('mobile_number'),
            first_name=payload.get('name', ''),
        )
        
        # Link user to dealer
        obj.user = user
        obj.save()
    else:
        raise HttpError(400, "Branch ID required")
    return {
            'status': 'success',
            'message': 'dealer created successfully',
            'data': [_dealer_to_dict(obj)],

        }

@router.get('/supplies', response=PaginatedResponseSchema[list[ProductSupplyResponseSchema]])
def list_supplies(request, page: int = 1, page_size: int = 10):
    user = getattr(request, 'user', None)
    # If authentication is enabled, require a logged in user
    if user is None or not getattr(user, 'is_authenticated', False):
        raise HttpError(401, "Unauthorized")

    # Staff/superusers can see all supplies
    if getattr(user, 'is_superuser', False):
        supplies_qs = ProductSupply.objects.all()
    elif getattr(user, 'is_staff', False):
        # Staff can see supplies they created and ones without creator
        supplies_qs = ProductSupply.objects.filter(Q(created_by=user))
    else:
        # For dealer users, find the linked Dealer and show only its supplies
        dealer = getattr(user, 'dealer_profile', None)
        if dealer is None:
            supplies_qs = ProductSupply.objects.none()
        else:
            supplies_qs = ProductSupply.objects.filter(dealer=dealer)

    items, pagination = paginate_queryset(
        supplies_qs,
        page=page,
        page_size=page_size,
        url_path="/api/supplies"
    )
    
    return PaginatedResponseSchema.success_response(
        data=[_supply_to_dict(s) for s in items],
        pagination=pagination,
        message="Product supplies retrieved successfully"
    )

@router.post('/supplies', response=BaseResponseSchema[list[ProductSupplyResponseSchema]])
def add_supplies(request, data: list[ProductSupplySchema]):
    try:
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            raise HttpError(401, "Unauthorized")

        # normalize to a list in case a single item is passed
        items = data if isinstance(data, list) else [data]

        created_items = []

        with transaction.atomic():
            for item in items:
                payload = item.dict()
                dealer_id = payload.pop('dealer', None)
                if dealer_id is None:
                    raise HttpError(400, "dealer is required for each item")

                # Authorization: staff/superuser can create for any dealer;
                # regular dealer users only for their own dealer
                if not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
                    dealer = Dealer.objects.filter(id=dealer_id, user=user).first()
                    if dealer is None:
                        raise HttpError(403, "You are not allowed to add supply for dealer id %s" % dealer_id)

                obj = ProductSupply.objects.create(dealer_id=dealer_id, created_by=user, **payload)
                created_items.append(_supply_to_dict(obj))

        return BaseResponseSchema.success_response(
            data=created_items,
            message="Product supplies created successfully"
        )
    except HttpError:
        raise
    except Exception as e:
        return BaseResponseSchema.error_response(
            message=str(e),
            code="SUPPLY_CREATE_ERROR"
        )

@router.get('/dashboard')
def dashboard_counts(request):
    # aggregate vehicle counts per product_name by summing the `count` field
    try:
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            raise HttpError(401, "Unauthorized")

        # Base response keys
        response = {
            'vehicle_count': 0,
            'battery_count': 0,
            'charger_count': 0,
        }

        # Determine queryset scope
        if getattr(user, 'is_superuser', False):
            supplies_qs = ProductSupply.objects.all()
            dealer_count = Dealer.objects.count()
            branch_count = Branch.objects.count()
        elif getattr(user, 'is_staff', False):
            supplies_qs = ProductSupply.objects.filter(Q(created_by=user))
            dealer_count = Dealer.objects.filter(Q(created_by=user)).count()
            branch_count = Branch.objects.filter(Q(created_by=user)).count()
        else:
            dealer = getattr(user, 'dealer_profile', None)
            if dealer is None:
                supplies_qs = ProductSupply.objects.none()
                dealer_count = 0
                branch_count = 0
            else:
                supplies_qs = ProductSupply.objects.filter(dealer=dealer)
                dealer_count = 1
                branch_count = 1

        product_counts = (
            supplies_qs
            .values('product_name')
            .annotate(total=Sum('count'))
            .order_by('-total')
        )

        for p in product_counts:
            name = (p['product_name'] or '').strip().lower()
            total = p.get('total') or 0
            key = f"{name}_count"
            response[key] = total

        response.update({
            'dealer_count': dealer_count,
            'branch_count': branch_count,
        })

        return {
            'status': True,
            'message': 'Dashboard counts fetched successfully',
            'data': response
        }
    except HttpError:
        raise
    except Exception as e:
        # handle error gracefully
        return {
            'status': False,
            'message': f'Error fetching dashboard counts: {str(e)}',
        }