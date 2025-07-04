"""
Tenant Validator untuk Permission dan Feature Validation
Validator untuk memvalidasi permissions dan fitur tenant
"""

import logging
from typing import Dict, List, Optional, Tuple
from src.database.models.tenant import Tenant, SubscriptionPlan

logger = logging.getLogger(__name__)

class TenantValidator:
    """Validator untuk tenant permissions dan features"""
    
    def __init__(self):
        # Mapping fitur berdasarkan plan
        self.plan_features = {
            SubscriptionPlan.BASIC: {
                'shop', 'leveling', 'reputation', 'tickets', 'live_stock', 'admin_commands'
            },
            SubscriptionPlan.PREMIUM: {
                'shop', 'leveling', 'reputation', 'tickets', 'live_stock', 'admin_commands',
                'automod', 'custom_commands', 'analytics'
            },
            SubscriptionPlan.ENTERPRISE: {
                'shop', 'leveling', 'reputation', 'tickets', 'live_stock', 'admin_commands',
                'automod', 'custom_commands', 'analytics', 'api_access', 'priority_support'
            }
        }
        
        # Mapping permissions berdasarkan plan
        self.plan_permissions = {
            SubscriptionPlan.BASIC: {
                'manage_products', 'manage_users'
            },
            SubscriptionPlan.PREMIUM: {
                'manage_products', 'manage_users', 'view_analytics'
            },
            SubscriptionPlan.ENTERPRISE: {
                'manage_products', 'manage_users', 'view_analytics', 'custom_config',
                'api_access', 'advanced_settings'
            }
        }
    
    def validate_feature_access(self, tenant: Tenant, feature: str) -> Tuple[bool, str]:
        """Validasi akses fitur berdasarkan plan tenant"""
        try:
            allowed_features = self.plan_features.get(tenant.plan, set())
            
            if feature not in allowed_features:
                return False, f"Fitur {feature} tidak tersedia untuk plan {tenant.plan.value}"
            
            return True, "Fitur valid"
            
        except Exception as e:
            logger.error(f"Error validating feature access: {e}")
            return False, f"Error validasi: {str(e)}"
    
    def validate_permission_access(self, tenant: Tenant, permission: str) -> Tuple[bool, str]:
        """Validasi akses permission berdasarkan plan tenant"""
        try:
            allowed_permissions = self.plan_permissions.get(tenant.plan, set())
            
            if permission not in allowed_permissions:
                return False, f"Permission {permission} tidak tersedia untuk plan {tenant.plan.value}"
            
            return True, "Permission valid"
            
        except Exception as e:
            logger.error(f"Error validating permission access: {e}")
            return False, f"Error validasi: {str(e)}"
    
    def validate_tenant_config(self, tenant: Tenant) -> Tuple[bool, List[str]]:
        """Validasi konfigurasi tenant secara keseluruhan"""
        errors = []
        
        try:
            # Validasi features
            for feature, enabled in tenant.features.items():
                if enabled:
                    is_valid, message = self.validate_feature_access(tenant, feature)
                    if not is_valid:
                        errors.append(f"Feature error: {message}")
            
            # Validasi permissions
            for permission, enabled in tenant.permissions.items():
                if enabled:
                    is_valid, message = self.validate_permission_access(tenant, permission)
                    if not is_valid:
                        errors.append(f"Permission error: {message}")
            
            # Validasi channel configuration
            required_channels = ['live_stock', 'purchase_log']
            for channel in required_channels:
                if channel not in tenant.channels or not tenant.channels[channel]:
                    errors.append(f"Channel {channel} belum dikonfigurasi")
            
            # Validasi bot config
            if not tenant.bot_config.get('prefix'):
                errors.append("Bot prefix belum dikonfigurasi")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating tenant config: {e}")
            return False, [f"Error validasi: {str(e)}"]
    
    def get_available_features(self, plan: SubscriptionPlan) -> List[str]:
        """Dapatkan daftar fitur yang tersedia untuk plan"""
        return list(self.plan_features.get(plan, set()))
    
    def get_available_permissions(self, plan: SubscriptionPlan) -> List[str]:
        """Dapatkan daftar permissions yang tersedia untuk plan"""
        return list(self.plan_permissions.get(plan, set()))
    
    def can_upgrade_feature(self, current_plan: SubscriptionPlan, 
                          target_plan: SubscriptionPlan, feature: str) -> bool:
        """Cek apakah fitur bisa diupgrade ke plan yang lebih tinggi"""
        current_features = self.plan_features.get(current_plan, set())
        target_features = self.plan_features.get(target_plan, set())
        
        return feature not in current_features and feature in target_features
    
    def validate_channel_id(self, channel_id: str) -> Tuple[bool, str]:
        """Validasi format channel ID Discord"""
        try:
            # Channel ID Discord harus berupa angka dan panjang 17-19 digit
            if not channel_id.isdigit():
                return False, "Channel ID harus berupa angka"
            
            if len(channel_id) < 17 or len(channel_id) > 19:
                return False, "Channel ID tidak valid (panjang harus 17-19 digit)"
            
            return True, "Channel ID valid"
            
        except Exception as e:
            return False, f"Error validasi channel ID: {str(e)}"
