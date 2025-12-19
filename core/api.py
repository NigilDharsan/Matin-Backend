from tokenize import TokenError
from ninja import Router
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from ninja.errors import HttpError

from .models import Role, Branch, Dealer, ProductSupply
from .schemas import (
    LoginRequest,
    RefreshRequest,
    SignupSchema,
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserInfo,
    RoleSchema,
    RoleResponseSchema,
    BranchSchema,
    BranchResponseSchema,
    DealerInSchema,
    DealerSchema,
    ProductSupplySchema,
    ProductSupplyResponseSchema,
    DetailsResponse,
)
from .responses import BaseResponseSchema, PaginatedResponseSchema
from .utils import paginate_queryset
from .auth import get_auth_class
from .serializers import ModelSerializer
from .services.email_service import EmailService

# Initialize serializer and email service
serializer = ModelSerializer()
email_service = EmailService()

# Routers
auth_router = Router()
auth_class = get_auth_class()
router = Router(auth=auth_class()) if auth_class else Router()

User = get_user_model()


# ============================================================================
# Authentication Endpoints
# ============================================================================

@auth_router.post('/login', response={200: dict, 400: dict})
def login(request, data: LoginRequest):
    """Authenticate user and return JWT tokens"""
    user = authenticate(username=data.username, password=data.password)
    
    if not user:
        return 400, {
            'status': False,
            'message': 'Invalid credentials',
        }
    
    refresh = RefreshToken.for_user(user)
    token_data = {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
        }
    }

    return 200, {
        'status': True,
        'message': 'Login successful',
        'data': token_data
    }


@auth_router.post("/refresh", response={200: BaseResponseSchema, 401: dict, 404: dict, 500: dict})
def refresh_token(request, data: RefreshRequest):
    """Refresh access token using refresh token"""
    try:
        old_refresh = RefreshToken(data.refresh)
        user_id = old_refresh.get("user_id")

        if not user_id:
            return 401, {
                "status": False,
                "message": "Invalid token: user_id missing"
            }

        user = User.objects.get(id=user_id)
        new_refresh = RefreshToken.for_user(user)

        return 200, BaseResponseSchema.success_response(
            data={
                "access": str(new_refresh.access_token),
                "refresh": str(new_refresh)
            },
            message="Tokens refreshed successfully"
        )

    except User.DoesNotExist:
        return 404, {"status": False, "message": "User not found"}
    except TokenError as e:
        return 401, {"status": False, "message": "Invalid or expired refresh token"}
    except Exception as e:
        return 500, {"status": False, "message": f"Unexpected error: {str(e)}"}


@auth_router.post('/signup', response={201: BaseResponseSchema[TokenResponse], 400: dict})
def signup(request, data: SignupSchema):
    """Register a new user"""
    username = data.username or data.email.split('@')[0]
    
    if User.objects.filter(username=username).exists():
        raise HttpError(400, "Username already exists")
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email already exists")

    try:
        user = User.objects.create_user(
            username=username,
            email=data.email,
            password=data.password,
            first_name=data.first_name or "",
            last_name=data.last_name or "",
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
    except Exception as e:
        raise HttpError(400, str(e))


@auth_router.post('/forgot-password', response={200: BaseResponseSchema, 404: dict})
def forgot_password(request, data: ForgotPasswordRequest):
    """Send OTP to user's email for password reset"""
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return 404, {"status": False, "message": "User with this email does not exist"}

    # Generate and save OTP
    otp = email_service.generate_otp()
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save(update_fields=['otp', 'otp_created_at'])

    # Send OTP via email
    if email_service.send_otp_email(user.email, otp):
        return 200, BaseResponseSchema.success_response(
            message="OTP sent to your email successfully"
        )
    else:
        return 500, {"status": False, "message": "Failed to send OTP email"}


@auth_router.post('/verify-otp', response={200: BaseResponseSchema, 400: dict})
def verify_otp(request, data: VerifyOTPRequest):
    """Verify OTP for password reset"""
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return 404, {"status": False, "message": "User not found"}

    if email_service.is_otp_valid(user, data.otp):
        return 200, BaseResponseSchema.success_response(
            message="OTP verified successfully"
        )
    else:
        return 400, {"status": False, "message": "Invalid or expired OTP"}


@auth_router.post('/reset-password', response={200: BaseResponseSchema, 400: dict})
def reset_password(request, data: ResetPasswordRequest):
    """Reset user password after OTP verification"""
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return 404, {"status": False, "message": "User not found"}

    if not email_service.is_otp_valid(user, data.otp):
        return 400, {"status": False, "message": "Invalid or expired OTP"}

    # Update password and save
    user.set_password(data.new_password)
    user.save()  # ← This was missing!
    
    # Clear OTP after successful password reset
    email_service.clear_otp(user)

    return 200, BaseResponseSchema.success_response(
        message="Password reset successfully"
    )


# ============================================================================
# Details Endpoint
# ============================================================================

@router.get('/details', response=DetailsResponse)
def get_details(request):
    """Get roles, branches, and dealers based on user permissions"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    if user.is_superuser:
        roles_qs = Role.objects.all()
        branches_qs = Branch.objects.all()
        dealers_qs = Dealer.objects.all()
    elif user.is_staff:
        roles_qs = Role.objects.filter(Q(created_by=user))
        branches_qs = Branch.objects.filter(Q(created_by=user))
        dealers_qs = Dealer.objects.filter(Q(created_by=user))
    else:
        roles_qs = user.created_roles.all()
        branches_qs = user.created_branches.all()
        dealers_qs = user.created_dealers.all()

    return {
        'status': True,
        'message': 'Data retrieved successfully',
        'data': {
            "roles": [serializer.role_to_dict(r) for r in roles_qs],
            "branches": [serializer.branch_to_dict(b) for b in branches_qs],
            "dealers": [serializer.dealer_to_dict(d) for d in dealers_qs]
        }
    }


# ============================================================================
# Role Endpoints
# ============================================================================

@router.post('/roles', response=RoleResponseSchema)
def add_role(request, data: RoleSchema):
    """Create a new role"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")
    if not (user.is_staff or user.is_superuser):
        raise HttpError(403, "Forbidden")

    obj = Role.objects.create(created_by=user, **data.dict())
    return serializer.role_to_dict(obj)


# ============================================================================
# Branch Endpoints
# ============================================================================

@router.post('/branches', response=BranchResponseSchema)
def add_branch(request, data: BranchSchema):
    """Create a new branch"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")
    if not (user.is_staff or user.is_superuser):
        raise HttpError(403, "Forbidden")

    obj = Branch.objects.create(created_by=user, **data.dict())
    return serializer.branch_to_dict(obj)


# ============================================================================
# Dealer Endpoints
# ============================================================================

@router.get('/dealers', response=PaginatedResponseSchema[list[DealerSchema]])
def list_dealers(request, page: int = 1, page_size: int = 10, branch_id: int = None, search: str = None):
    """List dealers with pagination, branch filter, and search"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        dealers_qs = Dealer.objects.select_related('branch').all()
        
        # Filter by branch if provided
        if branch_id:
            dealers_qs = dealers_qs.filter(branch_id=branch_id)
        
        # Search by name, mobile_number, or company_name
        if search:
            dealers_qs = dealers_qs.filter(
                Q(name__icontains=search) |
                Q(mobile_number__icontains=search) |
                Q(company_name__icontains=search)
            )

        items, pagination = paginate_queryset(
            dealers_qs,
            page=page,
            page_size=page_size,
            url_path="/api/dealers"
        )

        return PaginatedResponseSchema.success_response(
            data=[serializer.dealer_to_dict(d) for d in items],
            pagination=pagination,
            message="Dealers retrieved successfully"
        )
    except Exception as e:
        raise HttpError(400, f"Error listing dealers: {e}")


@router.post('/dealers', response=BaseResponseSchema[list[DealerSchema]])
def add_dealer(request, data: DealerInSchema):
    """Create a new dealer with associated user account"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    payload = data.dict()
    branch_id = payload.pop('branch', None)
    
    if not branch_id:
        raise HttpError(400, "Branch ID required")

    try:
        with transaction.atomic():
            # Create dealer
            dealer = Dealer.objects.create(
                branch_id=branch_id,
                created_by=user,
                **payload
            )

            # Create user account
            username = payload.get('mobile_number')
            
            if User.objects.filter(username=username).exists():
                raise HttpError(400, "Username already exists")
            if User.objects.filter(email=payload.get('email')).exists():
                raise HttpError(400, "Email already exists")

            dealer_user = User.objects.create_user(
                username=username,
                email=payload.get('email'),
                password=payload.get('mobile_number'),
                first_name=payload.get('name', ''),
            )

            dealer.user = dealer_user
            dealer.save()

        return BaseResponseSchema.success_response(
            data=[serializer.dealer_to_dict(dealer)],
            message="Dealer created successfully"
        )
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, f"Error creating dealer: {e}")


@router.put('/dealers/{dealer_id}', response=BaseResponseSchema[DealerSchema])
def update_dealer(request, dealer_id: int, data: DealerInSchema):
    """Update an existing dealer"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        dealer = Dealer.objects.get(id=dealer_id)
        
        # Authorization check
        if not (user.is_staff or user.is_superuser):
            if dealer.created_by != user:
                raise HttpError(403, "You don't have permission to edit this dealer")

        payload = data.dict()
        branch_id = payload.pop('branch', None)
        
        # Update dealer fields
        for field, value in payload.items():
            setattr(dealer, field, value)
        
        if branch_id:
            dealer.branch_id = branch_id
        
        dealer.save()

        return BaseResponseSchema.success_response(
            data=serializer.dealer_to_dict(dealer),
            message="Dealer updated successfully"
        )
    except Dealer.DoesNotExist:
        raise HttpError(404, "Dealer not found")
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, f"Error updating dealer: {e}")


@router.delete('/dealers/{dealer_id}', response=BaseResponseSchema)
def delete_dealer(request, dealer_id: int):
    """Delete a dealer"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        dealer = Dealer.objects.get(id=dealer_id)
        
        # Authorization check
        if not (user.is_staff or user.is_superuser):
            if dealer.created_by != user:
                raise HttpError(403, "You don't have permission to delete this dealer")

        dealer_name = dealer.name
        
        # Delete associated user if exists
        if dealer.user:
            dealer.user.delete()
        
        dealer.delete()

        return BaseResponseSchema.success_response(
            message=f"Dealer '{dealer_name}' deleted successfully"
        )
    except Dealer.DoesNotExist:
        raise HttpError(404, "Dealer not found")
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, f"Error deleting dealer: {e}")


# ============================================================================
# UPDATED DEALER DETAILS ENDPOINT
# ============================================================================

@router.get('/dealers/{dealer_id}/details', response={200: dict, 401: dict, 403: dict, 404: dict})
def get_dealer_details(
    request, 
    dealer_id: int,
    page: int = 1,
    page_size: int = 10
):
    """Get detailed dealer information with purchase statistics and paginated items"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return 401, {"status": False, "message": "Unauthorized"}

    try:
        # Get dealer with branch
        dealer = Dealer.objects.select_related('branch').get(id=dealer_id)
        
        # Authorization check
        if not (user.is_staff or user.is_superuser):
            # Regular users can only view their own dealer profile
            if not hasattr(user, 'dealer_profile') or user.dealer_profile != dealer:
                return 403, {"status": False, "message": "You don't have permission to view this dealer"}

        # Get all supplies for this dealer
        supplies_qs = ProductSupply.objects.filter(dealer=dealer).select_related('dealer__branch')
        
        # Calculate product counts by aggregating
        product_counts = (
            supplies_qs
            .values('product_name')
            .annotate(total=Sum('count'))
        )
        
        vehicle_count = 0
        battery_count = 0
        charger_count = 0
        
        for p in product_counts:
            name = (p['product_name'] or '').strip().lower()
            total = p.get('total') or 0
            
            if 'vehicle' in name:
                vehicle_count += total
            elif 'battery' in name:
                battery_count += total
            elif 'charger' in name:
                charger_count += total
        
        # Get paginated purchase items
        items, pagination = paginate_queryset(
            supplies_qs.order_by('-created_at'),
            page=page,
            page_size=page_size,
            url_path=f"/api/dealers/{dealer_id}/details"
        )
        
        # Build dealer details
        dealer_info = {
            'id': dealer.id,
            'name': dealer.name,
            'mobile_number': dealer.mobile_number,
            'company_name': dealer.company_name,
            'email': dealer.email,
            'address_line1': dealer.address_line1,
            'address_line2': dealer.address_line2,
            'pincode': dealer.pincode,
            'state': dealer.state,
            'branch_id': dealer.branch.id if dealer.branch else None,
            'branch_name': dealer.branch.name if dealer.branch else None,
            'vehicle_count': vehicle_count,
            'battery_count': battery_count,
            'charger_count': charger_count,
            'total_purchases': supplies_qs.count()
        }
        
        # Build purchase items list
        purchase_items = [serializer.supply_to_dict(item) for item in items]
        
        return 200, {
            'status': True,
            'message': 'Dealer details retrieved successfully',
            'data': {
                'dealer': dealer_info,
                'purchases': purchase_items,
                'pagination': {
                    'count': pagination.count,
                    'next': pagination.next,
                    'previous': pagination.previous,
                    'page_size': pagination.page_size,
                    'current_page': pagination.current_page,
                    'total_pages': pagination.total_pages
                }
            }
        }
        
    except Dealer.DoesNotExist:
        return 404, {"status": False, "message": "Dealer not found"}
    except Exception as e:
        return 400, {"status": False, "message": f"Error fetching dealer details: {str(e)}"}


# ============================================================================
# UPDATED SUPPLIES ENDPOINTS - Replace existing ones
# ============================================================================

@router.get('/supplies', response=PaginatedResponseSchema[list[ProductSupplyResponseSchema]])
def list_supplies(
    request, 
    page: int = 1, 
    page_size: int = 10, 
    branch_id: int = None, 
    dealer_id: int = None,
    search: str = None
):
    """List product supplies with pagination, branch/dealer filter, and search"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    # Determine queryset based on user role
    if user.is_superuser:
        supplies_qs = ProductSupply.objects.select_related('dealer', 'dealer__branch').all()
    elif user.is_staff:
        supplies_qs = ProductSupply.objects.select_related('dealer', 'dealer__branch').filter(
            Q(created_by=user)
        )
    else:
        dealer = getattr(user, 'dealer_profile', None)
        if not dealer:
            supplies_qs = ProductSupply.objects.none()
        else:
            supplies_qs = ProductSupply.objects.select_related('dealer', 'dealer__branch').filter(
                dealer=dealer
            )

    # Filter by branch if provided
    if branch_id:
        supplies_qs = supplies_qs.filter(dealer__branch_id=branch_id)
    
    # Filter by dealer if provided
    if dealer_id:
        supplies_qs = supplies_qs.filter(dealer_id=dealer_id)
    
    # Search by dealer name, mobile number, company name, product name, serial number, or invoice number
    if search:
        supplies_qs = supplies_qs.filter(
            Q(dealer__name__icontains=search) |
            Q(dealer__mobile_number__icontains=search) |
            Q(dealer__company_name__icontains=search) |
            Q(product_name__icontains=search) |
            Q(serial_number__icontains=search) |
            Q(invoice_number__icontains=search)
        )

    items, pagination = paginate_queryset(
        supplies_qs,
        page=page,
        page_size=page_size,
        url_path="/api/supplies"
    )

    return PaginatedResponseSchema.success_response(
        data=[serializer.supply_to_dict(s) for s in items],
        pagination=pagination,
        message="Product supplies retrieved successfully"
    )


@router.post('/supplies', response=BaseResponseSchema[list[ProductSupplyResponseSchema]])
def add_supplies(request, data: list[ProductSupplySchema]):
    """Create one or more product supplies with branch validation"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        items = data if isinstance(data, list) else [data]
        created_items = []

        with transaction.atomic():
            for item in items:
                payload = item.dict()
                dealer_id = payload.pop('dealer', None)
                branch_id = payload.pop('branch', None)
                
                if not dealer_id:
                    raise HttpError(400, "Dealer is required for each item")
                
                if not branch_id:
                    raise HttpError(400, "Branch is required for each item")

                # Verify dealer exists and belongs to the specified branch
                try:
                    dealer = Dealer.objects.select_related('branch').get(id=dealer_id)
                    
                    # Validate branch matches dealer's branch
                    if dealer.branch_id != branch_id:
                        raise HttpError(
                            400, 
                            f"Dealer '{dealer.name}' belongs to branch '{dealer.branch.name}' "
                            f"(ID: {dealer.branch_id}), not the specified branch (ID: {branch_id})"
                        )
                    
                except Dealer.DoesNotExist:
                    raise HttpError(404, f"Dealer with ID {dealer_id} not found")

                # Authorization check
                if not (user.is_staff or user.is_superuser):
                    if dealer.user != user:
                        raise HttpError(403, f"Not allowed to add supply for dealer '{dealer.name}'")

                # Create supply
                supply = ProductSupply.objects.create(
                    dealer_id=dealer_id,
                    created_by=user,
                    **payload
                )
                created_items.append(serializer.supply_to_dict(supply))

        return BaseResponseSchema.success_response(
            data=created_items,
            message=f"{len(created_items)} product supply/supplies created successfully"
        )
    except HttpError:
        raise
    except Exception as e:
        return BaseResponseSchema.error_response(
            message=str(e),
            code="SUPPLY_CREATE_ERROR"
        )


@router.put('/supplies/{supply_id}', response=BaseResponseSchema[ProductSupplyResponseSchema])
def update_supply(request, supply_id: int, data: ProductSupplySchema):
    """Update an existing product supply with branch validation"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        supply = ProductSupply.objects.select_related('dealer', 'dealer__branch').get(id=supply_id)
        
        # Authorization check
        if not (user.is_staff or user.is_superuser):
            if supply.created_by != user:
                raise HttpError(403, "You don't have permission to edit this supply")

        payload = data.dict()
        dealer_id = payload.pop('dealer', None)
        branch_id = payload.pop('branch', None)
        
        # If dealer is being changed, validate it
        if dealer_id and dealer_id != supply.dealer_id:
            try:
                dealer = Dealer.objects.select_related('branch').get(id=dealer_id)
                
                # Validate branch matches dealer's branch
                if branch_id and dealer.branch_id != branch_id:
                    raise HttpError(
                        400, 
                        f"Dealer '{dealer.name}' belongs to branch '{dealer.branch.name}' "
                        f"(ID: {dealer.branch_id}), not the specified branch (ID: {branch_id})"
                    )
                
                supply.dealer_id = dealer_id
                
            except Dealer.DoesNotExist:
                raise HttpError(404, f"Dealer with ID {dealer_id} not found")
        
        # Update supply fields
        for field, value in payload.items():
            setattr(supply, field, value)
        
        supply.save()

        return BaseResponseSchema.success_response(
            data=serializer.supply_to_dict(supply),
            message="Product supply updated successfully"
        )
    except ProductSupply.DoesNotExist:
        raise HttpError(404, "Product supply not found")
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, f"Error updating supply: {str(e)}")


# ============================================================================
# NEW: Get supplies by dealer
# ============================================================================

@router.get('/dealers/{dealer_id}/supplies', response=PaginatedResponseSchema[list[ProductSupplyResponseSchema]])
def get_dealer_supplies(
    request, 
    dealer_id: int,
    page: int = 1,
    page_size: int = 10,
    search: str = None
):
    """Get all supplies for a specific dealer with pagination"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        # Verify dealer exists
        dealer = Dealer.objects.select_related('branch').get(id=dealer_id)
        
        # Authorization check
        if not (user.is_staff or user.is_superuser):
            if not hasattr(user, 'dealer_profile') or user.dealer_profile != dealer:
                raise HttpError(403, "You don't have permission to view this dealer's supplies")

        # Get supplies
        supplies_qs = ProductSupply.objects.filter(dealer=dealer).select_related('dealer__branch')
        
        # Search if provided
        if search:
            supplies_qs = supplies_qs.filter(
                Q(product_name__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(invoice_number__icontains=search)
            )

        items, pagination = paginate_queryset(
            supplies_qs.order_by('-created_at'),
            page=page,
            page_size=page_size,
            url_path=f"/api/dealers/{dealer_id}/supplies"
        )

        return PaginatedResponseSchema.success_response(
            data=[serializer.supply_to_dict(s) for s in items],
            pagination=pagination,
            message=f"Supplies for dealer '{dealer.name}' retrieved successfully"
        )
        
    except Dealer.DoesNotExist:
        raise HttpError(404, "Dealer not found")
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, f"Error fetching dealer supplies: {str(e)}")

@router.delete('/supplies/{supply_id}', response=BaseResponseSchema)
def delete_supply(request, supply_id: int):
    """Delete a product supply"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        supply = ProductSupply.objects.get(id=supply_id)
        
        # Authorization check
        if not (user.is_staff or user.is_superuser):
            if supply.created_by != user:
                raise HttpError(403, "You don't have permission to delete this supply")

        product_name = supply.product_name
        serial_number = supply.serial_number
        supply.delete()

        return BaseResponseSchema.success_response(
            message=f"Product supply '{product_name}' (S/N: {serial_number}) deleted successfully"
        )
    except ProductSupply.DoesNotExist:
        raise HttpError(404, "Product supply not found")
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, f"Error deleting supply: {e}")


# ============================================================================
# Dashboard Endpoint
# ============================================================================

@router.get('/dashboard')
def dashboard_counts(request):
    """Get aggregated counts for dashboard"""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        raise HttpError(401, "Unauthorized")

    try:
        response = {
            'vehicle_count': 0,
            'battery_count': 0,
            'charger_count': 0,
        }

        # Determine queryset scope
        if user.is_superuser:
            supplies_qs = ProductSupply.objects.all()
            dealer_count = Dealer.objects.count()
            branch_count = Branch.objects.count()
        elif user.is_staff:
            supplies_qs = ProductSupply.objects.filter(Q(created_by=user))
            dealer_count = Dealer.objects.filter(Q(created_by=user)).count()
            branch_count = Branch.objects.filter(Q(created_by=user)).count()
        else:
            dealer = getattr(user, 'dealer_profile', None)
            if not dealer:
                supplies_qs = ProductSupply.objects.none()
                dealer_count = 0
                branch_count = 0
            else:
                supplies_qs = ProductSupply.objects.filter(dealer=dealer)
                dealer_count = 1
                branch_count = 1

        # Aggregate product counts
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
    except Exception as e:
        return {
            'status': False,
            'message': f'Error fetching dashboard counts: {str(e)}',
        }