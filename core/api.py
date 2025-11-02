from ninja import Router
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from typing import List

from .models import Role, Branch, Dealer, ProductSupply
from .schemas import (
    RoleSchema,
    BranchSchema,
    DealerSchema,
    ProductSupplySchema,
    LoginRequest,
    TokenResponse,
    UserInfo,
    DashboardData,
    ApiResponse,
    ErrorResponse,
)
from .auth import JWTAuth
from .error_handlers import handle_error, APIException

router = Router()

# Define standard response types for all endpoints
STANDARD_RESPONSES = {
    200: ApiResponse,
    201: ApiResponse,
    400: ErrorResponse,
    401: ErrorResponse,
    404: ErrorResponse,
    500: ErrorResponse,
}

# ==================== Authentication ====================

@router.post('/login', response=STANDARD_RESPONSES)
def login(request, data: LoginRequest = None, username: str = None, password: str = None):
    """Authenticate user and return JWT tokens with user information
    
    Accepts credentials either as:
    - JSON body: {"username": "...", "password": "..."}
    - Query params: ?username=...&password=...
    """
    try:
        # Support both JSON body and query parameters
        if data:
            username = data.username
            password = data.password
        
        if not username or not password:
            return 400, {
                'status': 'failed',
                'message': 'Username and password are required',
                'error': 'Missing credentials',
                'error_code': 'MISSING_CREDENTIALS'
            }
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return 401, {
                'status': 'failed',
                'message': 'Invalid credentials',
                'error': 'Username or password is incorrect',
                'error_code': 'INVALID_CREDENTIALS'
            }
                
        refresh = RefreshToken.for_user(user)
        
        token_data = TokenResponse(
            access=str(refresh.access_token),
            refresh=str(refresh),
            user=UserInfo.from_orm(user)
        )
        
        return 200, {
            'status': 'success',
            'message': 'Login successful',
            'data': token_data.dict()
        }
    except APIException as e:
        return handle_error(e, 'login')
    except Exception as e:
        return handle_error(e, 'login')

# ==================== Roles ====================

@router.get('/roles', response=STANDARD_RESPONSES, auth=JWTAuth())
def list_roles(request):
    """Get all roles"""
    try:
        roles = [RoleSchema.from_orm(role) for role in Role.objects.all()]
        return 200, {
            'status': 'success',
            'message': f'{len(roles)} role(s) retrieved successfully',
            'data': roles
        }
    except Exception as e:
        return handle_error(e, 'list roles')

@router.get('/roles/{role_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def get_role(request, role_id: int):
    """Get a specific role by ID"""
    try:
        role = get_object_or_404(Role, id=role_id)
        return 200, {
            'status': 'success',
            'message': 'Role retrieved successfully',
            'data': RoleSchema.from_orm(role)
        }
    except Exception as e:
        return handle_error(e, 'get role')

@router.post('/roles', response=STANDARD_RESPONSES, auth=JWTAuth())
def create_role(request, data: RoleSchema):
    """Create a new role"""
    try:
        role = Role.objects.create(**data.dict(exclude={'id'}))
        return 201, {
            'status': 'success',
            'message': 'Role created successfully',
            'data': RoleSchema.from_orm(role)
        }
    except Exception as e:
        return handle_error(e, 'create role')

@router.put('/roles/{role_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def update_role(request, role_id: int, data: RoleSchema):
    """Update an existing role"""
    try:
        role = get_object_or_404(Role, id=role_id)
        for attr, value in data.dict(exclude={'id'}).items():
            setattr(role, attr, value)
        role.save()
        return 200, {
            'status': 'success',
            'message': 'Role updated successfully',
            'data': RoleSchema.from_orm(role)
        }
    except Exception as e:
        return handle_error(e, 'update role')

@router.delete('/roles/{role_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def delete_role(request, role_id: int):
    """Delete a role"""
    try:
        role = get_object_or_404(Role, id=role_id)
        role.delete()
        return 200, {
            'status': 'success',
            'message': 'Role deleted successfully',
            'data': None
        }
    except Exception as e:
        return handle_error(e, 'delete role')

# ==================== Branches ====================

@router.get('/branches', response=STANDARD_RESPONSES, auth=JWTAuth())
def list_branches(request):
    """Get all branches"""
    try:
        branches = [BranchSchema.from_orm(branch) for branch in Branch.objects.all()]
        return 200, {
            'status': 'success',
            'message': f'{len(branches)} branch(es) retrieved successfully',
            'data': branches
        }
    except Exception as e:
        return handle_error(e, 'list branches')

@router.get('/branches/{branch_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def get_branch(request, branch_id: int):
    """Get a specific branch by ID"""
    try:
        branch = get_object_or_404(Branch, id=branch_id)
        return 200, {
            'status': 'success',
            'message': 'Branch retrieved successfully',
            'data': BranchSchema.from_orm(branch)
        }
    except Exception as e:
        return handle_error(e, 'get branch')

@router.post('/branches', response=STANDARD_RESPONSES, auth=JWTAuth())
def create_branch(request, data: BranchSchema):
    """Create a new branch"""
    try:
        branch = Branch.objects.create(**data.dict(exclude={'id'}))
        return 201, {
            'status': 'success',
            'message': 'Branch created successfully',
            'data': BranchSchema.from_orm(branch)
        }
    except Exception as e:
        return handle_error(e, 'create branch')

@router.put('/branches/{branch_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def update_branch(request, branch_id: int, data: BranchSchema):
    """Update an existing branch"""
    try:
        branch = get_object_or_404(Branch, id=branch_id)
        for attr, value in data.dict(exclude={'id'}).items():
            setattr(branch, attr, value)
        branch.save()
        return 200, {
            'status': 'success',
            'message': 'Branch updated successfully',
            'data': BranchSchema.from_orm(branch)
        }
    except Exception as e:
        return handle_error(e, 'update branch')

@router.delete('/branches/{branch_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def delete_branch(request, branch_id: int):
    """Delete a branch"""
    try:
        branch = get_object_or_404(Branch, id=branch_id)
        branch.delete()
        return 200, {
            'status': 'success',
            'message': 'Branch deleted successfully',
            'data': None
        }
    except Exception as e:
        return handle_error(e, 'delete branch')

# ==================== Dealers ====================

@router.get('/dealers', response=STANDARD_RESPONSES, auth=JWTAuth())
def list_dealers(request):
    """Get all dealers"""
    try:
        dealers = [DealerSchema.from_orm(dealer) for dealer in Dealer.objects.all()]
        return 200, {
            'status': 'success',
            'message': f'{len(dealers)} dealer(s) retrieved successfully',
            'data': dealers
        }
    except Exception as e:
        return handle_error(e, 'list dealers')

@router.get('/dealers/{dealer_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def get_dealer(request, dealer_id: int):
    """Get a specific dealer by ID"""
    try:
        dealer = get_object_or_404(Dealer, id=dealer_id)
        return 200, {
            'status': 'success',
            'message': 'Dealer retrieved successfully',
            'data': DealerSchema.from_orm(dealer)
        }
    except Exception as e:
        return handle_error(e, 'get dealer')

@router.post('/dealers', response=STANDARD_RESPONSES, auth=JWTAuth())
def create_dealer(request, data: DealerSchema):
    """Create a new dealer"""
    try:
        dealer = Dealer.objects.create(**data.dict(exclude={'id'}))
        return 201, {
            'status': 'success',
            'message': 'Dealer created successfully',
            'data': DealerSchema.from_orm(dealer)
        }
    except Exception as e:
        return handle_error(e, 'create dealer')

@router.put('/dealers/{dealer_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def update_dealer(request, dealer_id: int, data: DealerSchema):
    """Update an existing dealer"""
    try:
        dealer = get_object_or_404(Dealer, id=dealer_id)
        for attr, value in data.dict(exclude={'id'}).items():
            setattr(dealer, attr, value)
        dealer.save()
        return 200, {
            'status': 'success',
            'message': 'Dealer updated successfully',
            'data': DealerSchema.from_orm(dealer)
        }
    except Exception as e:
        return handle_error(e, 'update dealer')

@router.delete('/dealers/{dealer_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def delete_dealer(request, dealer_id: int):
    """Delete a dealer"""
    try:
        dealer = get_object_or_404(Dealer, id=dealer_id)
        dealer.delete()
        return 200, {
            'status': 'success',
            'message': 'Dealer deleted successfully',
            'data': None
        }
    except Exception as e:
        return handle_error(e, 'delete dealer')

# ==================== Product Supplies ====================

@router.get('/supplies', response=STANDARD_RESPONSES, auth=JWTAuth())
def list_supplies(request):
    """Get all product supplies"""
    try:
        supplies = [ProductSupplySchema.from_orm(supply) for supply in ProductSupply.objects.all()]
        return 200, {
            'status': 'success',
            'message': f'{len(supplies)} product supply(ies) retrieved successfully',
            'data': supplies
        }
    except Exception as e:
        return handle_error(e, 'list supplies')

@router.get('/supplies/{supply_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def get_supply(request, supply_id: int):
    """Get a specific product supply by ID"""
    try:
        supply = get_object_or_404(ProductSupply, id=supply_id)
        return 200, {
            'status': 'success',
            'message': 'Product supply retrieved successfully',
            'data': ProductSupplySchema.from_orm(supply)
        }
    except Exception as e:
        return handle_error(e, 'get supply')

@router.post('/supplies', response=STANDARD_RESPONSES, auth=JWTAuth())
def create_supply(request, data: ProductSupplySchema):
    """Create a new product supply"""
    try:
        supply = ProductSupply.objects.create(**data.dict(exclude={'id'}))
        return 201, {
            'status': 'success',
            'message': 'Product supply created successfully',
            'data': ProductSupplySchema.from_orm(supply)
        }
    except Exception as e:
        return handle_error(e, 'create supply')

@router.put('/supplies/{supply_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def update_supply(request, supply_id: int, data: ProductSupplySchema):
    """Update an existing product supply"""
    try:
        supply = get_object_or_404(ProductSupply, id=supply_id)
        for attr, value in data.dict(exclude={'id'}).items():
            setattr(supply, attr, value)
        supply.save()
        return 200, {
            'status': 'success',
            'message': 'Product supply updated successfully',
            'data': ProductSupplySchema.from_orm(supply)
        }
    except Exception as e:
        return handle_error(e, 'update supply')

@router.delete('/supplies/{supply_id}', response=STANDARD_RESPONSES, auth=JWTAuth())
def delete_supply(request, supply_id: int):
    """Delete a product supply"""
    try:
        supply = get_object_or_404(ProductSupply, id=supply_id)
        supply.delete()
        return 200, {
            'status': 'success',
            'message': 'Product supply deleted successfully',
            'data': None
        }
    except Exception as e:
        return handle_error(e, 'delete supply')

# ==================== Dashboard ====================

@router.get('/dashboard', response=STANDARD_RESPONSES, auth=JWTAuth())
def dashboard_counts(request):
    """Get dashboard statistics"""
    try:
        dashboard_data = DashboardData(
            vehicle_count=ProductSupply.objects.count(),
            dealer_count=Dealer.objects.count(),
            branch_count=Branch.objects.count()
        )
        
        return 200, {
            'status': 'success',
            'message': 'Dashboard data retrieved successfully',
            'data': dashboard_data.dict()
        }
    except Exception as e:
        return handle_error(e, 'dashboard')