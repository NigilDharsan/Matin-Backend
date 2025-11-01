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
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address")
    search_fields = ("name", "address")


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "mobile_number", "company_name", "branch")
    list_filter = ("branch",)
    search_fields = ("name", "mobile_number", "company_name")


@admin.register(ProductSupply)
class ProductSupplyAdmin(admin.ModelAdmin):
    list_display = ("id", "product_name", "invoice_number", "dealer", "purchase_date", "count")
    list_filter = ("dealer__branch",)
    search_fields = ("product_name", "invoice_number", "serial_number", "dealer__name")


admin.site.site_header = "Dealer Management Admin"
admin.site.site_title = "Dealer Admin Portal"
admin.site.index_title = "Welcome to Dealer Dashboard"
