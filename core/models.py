from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Role(models.Model):
    """Role model for user categorization"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class Branch(models.Model):
    """Branch model for organizational structure"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_branches'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branches'
        ordering = ['name']
        verbose_name_plural = 'Branches'

    def __str__(self):
        return self.name


class AdminUser(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    email = models.EmailField(unique=True)
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'admin_users'

    def __str__(self):
        return self.username


class Dealer(models.Model):
    """Dealer model for managing dealer information"""
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=20)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='dealers'
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dealer_profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_dealers'
    )

    class Meta:
        db_table = 'dealers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['branch', '-created_at']),
            models.Index(fields=['mobile_number']),
        ]

    def __str__(self):
        return f"{self.name} ({self.mobile_number})"


class ProductSupply(models.Model):
    """Product supply model for tracking vehicle and component supplies"""
    id = models.BigAutoField(primary_key=True)
    dealer = models.ForeignKey(
        Dealer,
        on_delete=models.CASCADE,
        related_name='supplies'
    )

    # Product info
    product_name = models.CharField(max_length=150)
    invoice_number = models.CharField(max_length=50)
    serial_number = models.CharField(max_length=150, unique=True)
    purchase_date = models.DateField(blank=True, null=True)
    count = models.PositiveIntegerField(default=1)

    # Vehicle fields
    chase_number = models.CharField(max_length=100, blank=True, null=True)
    vehicle_model = models.CharField(max_length=150, blank=True, null=True)
    vehicle_variant = models.CharField(max_length=150, blank=True, null=True)
    vehicle_warranty = models.CharField(max_length=150, blank=True, null=True)

    # Controller & Motor
    controller = models.CharField(max_length=150, blank=True, null=True)
    motor = models.CharField(max_length=150, blank=True, null=True)

    # Battery details
    battery_number = models.CharField(max_length=150, blank=True, null=True)
    battery_model = models.CharField(max_length=150, blank=True, null=True)
    battery_variant = models.CharField(max_length=150, blank=True, null=True)
    battery_warranty = models.CharField(max_length=150, blank=True, null=True)
    bulging_warranty = models.CharField(max_length=150, blank=True, null=True)

    # Charger details
    charger_number = models.CharField(max_length=150, blank=True, null=True)
    charger_model = models.CharField(max_length=150, blank=True, null=True)
    charger_type = models.CharField(max_length=150, blank=True, null=True)
    charger_variant = models.CharField(max_length=150, blank=True, null=True)
    charger_warranty = models.CharField(max_length=150, blank=True, null=True)

    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_supplies'
    )

    class Meta:
        db_table = 'product_supplies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dealer', '-created_at']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['product_name']),
        ]
        verbose_name_plural = 'Product Supplies'

    def __str__(self):
        return f"{self.product_name} - {self.serial_number}"