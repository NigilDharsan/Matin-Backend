from ninja import Router
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Role,Branch,Dealer,ProductSupply
from .schemas import RoleSchema,BranchSchema,DealerSchema,ProductSupplySchema
from .auth import JWTAuth

router=Router()

@router.post('/login')
def login(request, username:str, password:str):
    user=authenticate(username=username,password=password)
    if not user:
        return {'error':'Invalid credentials'}
    refresh=RefreshToken.for_user(user)
    return {'access':str(refresh.access_token),'refresh':str(refresh)}

@router.get('/roles',response=list[RoleSchema],auth=JWTAuth())
def list_roles(request):
    return list(Role.objects.all())

@router.post('/roles',response=RoleSchema,auth=JWTAuth())
def add_role(request,data:RoleSchema):
    obj=Role.objects.create(**data.dict())
    return obj

@router.get('/branches',response=list[BranchSchema],auth=JWTAuth())
def list_branches(request):
    return list(Branch.objects.all())

@router.post('/branches',response=BranchSchema,auth=JWTAuth())
def add_branch(request,data:BranchSchema):
    obj=Branch.objects.create(**data.dict())
    return obj

@router.get('/dealers',response=list[DealerSchema],auth=JWTAuth())
def list_dealers(request):
    return list(Dealer.objects.all())

@router.post('/dealers',response=DealerSchema,auth=JWTAuth())
def add_dealer(request,data:DealerSchema):
    obj=Dealer.objects.create(**data.dict())
    return obj

@router.get('/supplies',response=list[ProductSupplySchema],auth=JWTAuth())
def list_supplies(request):
    return list(ProductSupply.objects.all())

@router.post('/supplies',response=ProductSupplySchema,auth=JWTAuth())
def add_supply(request,data:ProductSupplySchema):
    obj=ProductSupply.objects.create(**data.dict())
    return obj

@router.get('/dashboard',auth=JWTAuth())
def dashboard_counts(request):
    return {'vehicle_count':ProductSupply.objects.count(),'dealer_count':Dealer.objects.count(),'branch_count':Branch.objects.count()}
