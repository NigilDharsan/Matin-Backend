from .models import Role, Branch, Dealer, ProductSupply


class ModelSerializer:
    """Utility class for converting models to dictionaries"""

    @staticmethod
    def role_to_dict(role: Role) -> dict:
        """Convert Role model to dictionary"""
        return {
            'id': role.id,
            'name': role.name,
        }

    @staticmethod
    def branch_to_dict(branch: Branch) -> dict:
        """Convert Branch model to dictionary"""
        return {
            'id': branch.id,
            'name': branch.name,
            'address': branch.address,
        }

    @staticmethod
    def dealer_to_dict(dealer: Dealer) -> dict:
        """Convert Dealer model to dictionary"""
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

    @staticmethod
    def supply_to_dict(supply: ProductSupply) -> dict:
        """Convert ProductSupply model to dictionary"""
        return {
            'id': supply.id,
            'dealer': supply.dealer_id,
            'dealer_name': supply.dealer.name if supply.dealer else None,
            'branch_id': supply.dealer.branch_id if supply.dealer else None,
            'branch_name': supply.dealer.branch.name if supply.dealer and supply.dealer.branch else None,
            'product_name': supply.product_name,
            'invoice_number': supply.invoice_number,
            'serial_number': supply.serial_number,
            'purchase_date': supply.purchase_date,
            'count': supply.count,
            'chase_number': supply.chase_number,
            'vehicle_model': supply.vehicle_model,
            'vehicle_variant': supply.vehicle_variant,
            'vehicle_warranty': supply.vehicle_warranty,
            'controller': supply.controller,
            'motor': supply.motor,
            'battery_number': supply.battery_number,
            'battery_model': supply.battery_model,
            'battery_variant': supply.battery_variant,
            'battery_warranty': supply.battery_warranty,
            'bulging_warranty': supply.bulging_warranty,
            'charger_number': supply.charger_number,
            'charger_model': supply.charger_model,
            'charger_type': supply.charger_type,
            'charger_variant': supply.charger_variant,
            'charger_warranty': supply.charger_warranty,
            'remarks': supply.remarks,
            'created_at': supply.created_at.date() if supply.created_at else None,
        }