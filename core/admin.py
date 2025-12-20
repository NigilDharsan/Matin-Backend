from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AdminUser, Role, Branch, Dealer, ProductSupply


@admin.register(AdminUser)
class AdminUserAdmin(UserAdmin):
    model = AdminUser
    list_display = ("username", "email", "role", "branch", "is_staff", "is_active")
    list_filter = ("role", "branch", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("id",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Organization", {"fields": ("role", "branch")}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "created_at")
    search_fields = ("name", "address")
    ordering = ("name",)


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "mobile_number", "company_name", "branch", "created_at")
    list_filter = ("branch", "state", "created_at")
    search_fields = ("name", "mobile_number", "company_name", "email")
    ordering = ("-created_at",)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('branch', 'user', 'created_by')


@admin.register(ProductSupply)
class ProductSupplyAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "product_name", 
        "dealer", 
        "get_branch",  # Custom method to display branch
        "invoice_number", 
        "serial_number",
        "vehicle_model", 
        "vehicle_variant", 
        "battery_model", 
        "charger_model", 
        "purchase_date",
        "count"
    )
    list_filter = ("dealer__branch", "purchase_date", "product_name")  # This is correct
    search_fields = ("product_name", "invoice_number", "serial_number", "dealer__name", "dealer__company_name")
    ordering = ("-created_at",)
    autocomplete_fields = ['dealer']  # Better UX for selecting dealer
    
    def get_branch(self, obj):
        """Display branch name in list view"""
        return obj.dealer.branch.name if obj.dealer and obj.dealer.branch else "-"
    get_branch.short_description = "Branch"
    get_branch.admin_order_field = "dealer__branch__name"  # Allow sorting by branch
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('dealer', 'dealer__branch', 'created_by')


# Customize admin site headers
admin.site.site_header = "Dealer Management Admin"
admin.site.site_title = "Dealer Admin Portal"
admin.site.index_title = "Welcome to Dealer Dashboard"