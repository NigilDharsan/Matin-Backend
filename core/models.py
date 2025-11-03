from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    id = models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=100,unique=True)
    def __str__(self):return self.name

class Branch(models.Model):
    id = models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=150,unique=True)
    address=models.TextField(blank=True)
    def __str__(self):return self.name

class AdminUser(AbstractUser):
    email=models.EmailField(unique=True)
    role=models.ForeignKey(Role,on_delete=models.SET_NULL,null=True,blank=True)
    branch=models.ForeignKey(Branch,on_delete=models.SET_NULL,null=True,blank=True)
    REQUIRED_FIELDS=['email']
    def __str__(self):return self.username

class Dealer(models.Model):
    id = models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=150)
    mobile_number=models.CharField(max_length=20)
    company_name=models.CharField(max_length=150,blank=True,null=True)
    email=models.EmailField(blank=True,null=True)
    address_line1=models.CharField(max_length=255)
    address_line2=models.CharField(max_length=255,blank=True,null=True)
    pincode=models.CharField(max_length=20,blank=True,null=True)
    state=models.CharField(max_length=100,blank=True,null=True)
    branch=models.ForeignKey(Branch,on_delete=models.CASCADE,related_name='dealers')
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return f"{self.name} ({self.mobile_number})"

class ProductSupply(models.Model):
    id = models.BigAutoField(primary_key=True)
    # ensure dealer FK is not unique so multiple ProductSupply rows can reference the same Dealer
    dealer=models.ForeignKey(Dealer,on_delete=models.CASCADE,related_name='supplies', unique=False)
    product_name=models.CharField(max_length=150)
    invoice_number=models.CharField(max_length=50)
    serial_number=models.CharField(max_length=150,unique=True)
    vehicle_model=models.CharField(max_length=150,blank=True,null=True)
    purchase_date=models.DateField(blank=True,null=True)
    remarks=models.TextField(blank=True,null=True)
    count=models.PositiveIntegerField(default=1)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name
