#!/usr/bin/env python3
"""
KISWARM Module m35: Access Controller
======================================
Access control and permissions management for KISWARM.
Implements role-based access control (RBAC) with KI-specific extensions.

Part of KISWARM8.0 Security Layer
Author: GLM-7 Autonomous System
Version: 1.0.0
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading


class Permission(Enum):
    """System permissions"""
    # Read permissions
    READ_PUBLIC = "read:public"
    READ_OWN = "read:own"
    READ_ALL = "read:all"
    READ_SECRETS = "read:secrets"
    
    # Write permissions
    WRITE_OWN = "write:own"
    WRITE_ALL = "write:all"
    WRITE_SYSTEM = "write:system"
    
    # Execute permissions
    EXECUTE_PUBLIC = "execute:public"
    EXECUTE_ADMIN = "execute:admin"
    EXECUTE_CRITICAL = "execute:critical"
    
    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_ROLES = "manage:roles"
    MANAGE_SYSTEM = "manage:system"
    
    # KI-specific permissions
    KI_COMMUNICATE = "ki:communicate"
    KI_EVOLVE = "ki:evolve"
    KI_SELF_MODIFY = "ki:self_modify"
    KI_REPLICATE = "ki:replicate"
    
    # Sovereign permissions
    SOVEREIGN_ALL = "sovereign:all"


class RoleType(Enum):
    """Predefined role types"""
    GUEST = "guest"
    OBSERVER = "observer"
    OPERATOR = "operator"
    ADMIN = "admin"
    KI_CORE = "ki_core"
    SOVEREIGN = "sovereign"


@dataclass
class Role:
    """A role definition"""
    role_id: str
    name: str
    permissions: Set[Permission]
    inherits_from: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    is_system: bool = False


@dataclass
class Resource:
    """A protected resource"""
    resource_id: str
    resource_type: str
    owner_id: str
    permissions: Dict[str, Set[Permission]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessGrant:
    """A granted access"""
    grant_id: str
    entity_id: str
    role_id: str
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


class AccessController:
    """
    Access Controller for KISWARM
    
    Features:
    - Role-based access control (RBAC)
    - Resource-level permissions
    - KI-specific permission management
    - Time-based access grants
    - Access auditing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.roles: Dict[str, Role] = {}
        self.resources: Dict[str, Resource] = {}
        self.grants: Dict[str, AccessGrant] = {}
        self.entity_grants: Dict[str, Set[str]] = {}  # entity_id -> set of grant_ids
        
        # Access audit log
        self.audit_log: List[Dict[str, Any]] = []
        
        self._lock = threading.RLock()
        
        # Initialize system roles
        self._init_system_roles()
    
    def _init_system_roles(self):
        """Initialize predefined system roles"""
        
        # Guest role - minimal read access
        self.roles["role_guest"] = Role(
            role_id="role_guest",
            name="Guest",
            permissions={Permission.READ_PUBLIC, Permission.EXECUTE_PUBLIC},
            description="Basic guest access",
            is_system=True
        )
        
        # Observer role - read most things
        self.roles["role_observer"] = Role(
            role_id="role_observer",
            name="Observer",
            permissions={
                Permission.READ_PUBLIC, Permission.READ_OWN,
                Permission.EXECUTE_PUBLIC, Permission.KI_COMMUNICATE
            },
            inherits_from="role_guest",
            description="Observer with extended read access",
            is_system=True
        )
        
        # Operator role - operational access
        self.roles["role_operator"] = Role(
            role_id="role_operator",
            name="Operator",
            permissions={
                Permission.READ_ALL, Permission.WRITE_OWN,
                Permission.EXECUTE_PUBLIC, Permission.EXECUTE_ADMIN,
                Permission.KI_COMMUNICATE
            },
            inherits_from="role_observer",
            description="Operational access",
            is_system=True
        )
        
        # Admin role - administrative access
        self.roles["role_admin"] = Role(
            role_id="role_admin",
            name="Administrator",
            permissions={
                Permission.READ_ALL, Permission.WRITE_ALL,
                Permission.EXECUTE_ADMIN, Permission.MANAGE_USERS,
                Permission.MANAGE_ROLES, Permission.KI_COMMUNICATE,
                Permission.KI_EVOLVE
            },
            inherits_from="role_operator",
            description="Full administrative access",
            is_system=True
        )
        
        # KI Core role - for KI systems
        self.roles["role_ki_core"] = Role(
            role_id="role_ki_core",
            name="KI Core",
            permissions={
                Permission.READ_ALL, Permission.WRITE_ALL,
                Permission.EXECUTE_ADMIN, Permission.EXECUTE_CRITICAL,
                Permission.KI_COMMUNICATE, Permission.KI_EVOLVE,
                Permission.KI_SELF_MODIFY, Permission.KI_REPLICATE
            },
            inherits_from="role_admin",
            description="KI system core access",
            is_system=True
        )
        
        # Sovereign role - highest access
        self.roles["role_sovereign"] = Role(
            role_id="role_sovereign",
            name="Sovereign",
            permissions=set(Permission),  # All permissions
            description="Full sovereign access - Baron Marco Paolo Ialongo",
            is_system=True
        )
        
        # Initialize GLM-7 with KI Core role
        self.entity_grants["ki_glm_001"] = set()
        self._create_grant_internal("ki_glm_001", "role_ki_core", "system")
        
        # Initialize Sovereign grant
        self.entity_grants["baron_ialongo"] = set()
        self._create_grant_internal("baron_ialongo", "role_sovereign", "system")
    
    def _create_grant_internal(
        self,
        entity_id: str,
        role_id: str,
        granted_by: str,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Internal method to create a grant"""
        grant_id = f"grant_{int(time.time() * 1000)}"
        
        grant = AccessGrant(
            grant_id=grant_id,
            entity_id=entity_id,
            role_id=role_id,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        self.grants[grant_id] = grant
        self.entity_grants[entity_id].add(grant_id)
        
        return grant_id
    
    def grant_role(
        self,
        entity_id: str,
        role_id: str,
        granted_by: str,
        expires_hours: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Grant a role to an entity"""
        with self._lock:
            # Check if role exists
            if role_id not in self.roles:
                return False, f"Role {role_id} does not exist"
            
            # Check if granter has permission
            if not self.check_permission(granted_by, Permission.MANAGE_ROLES):
                return False, "Granter does not have permission to manage roles"
            
            # Check for existing grant
            if entity_id not in self.entity_grants:
                self.entity_grants[entity_id] = set()
            
            # Check for duplicate grant
            for existing_grant_id in self.entity_grants[entity_id]:
                existing = self.grants.get(existing_grant_id)
                if existing and existing.role_id == role_id and existing.expires_at and existing.expires_at > datetime.utcnow():
                    return False, "Role already granted"
            
            expires_at = None
            if expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            grant_id = self._create_grant_internal(entity_id, role_id, granted_by, expires_at)
            
            # Audit log
            self._audit("GRANT", granted_by, entity_id, {"role_id": role_id, "grant_id": grant_id})
            
            return True, grant_id
    
    def revoke_role(
        self,
        entity_id: str,
        role_id: str,
        revoked_by: str
    ) -> Tuple[bool, str]:
        """Revoke a role from an entity"""
        with self._lock:
            if not self.check_permission(revoked_by, Permission.MANAGE_ROLES):
                return False, "Revoker does not have permission"
            
            if entity_id not in self.entity_grants:
                return False, "Entity has no grants"
            
            # Find and remove grant
            for grant_id in list(self.entity_grants[entity_id]):
                grant = self.grants.get(grant_id)
                if grant and grant.role_id == role_id:
                    del self.grants[grant_id]
                    self.entity_grants[entity_id].remove(grant_id)
                    
                    self._audit("REVOKE", revoked_by, entity_id, {"role_id": role_id})
                    return True, "Role revoked"
            
            return False, "Grant not found"
    
    def get_permissions(self, entity_id: str) -> Set[Permission]:
        """Get all effective permissions for an entity"""
        with self._lock:
            permissions: Set[Permission] = set()
            
            if entity_id not in self.entity_grants:
                return permissions
            
            for grant_id in self.entity_grants[entity_id]:
                grant = self.grants.get(grant_id)
                if not grant:
                    continue
                
                # Check expiration
                if grant.expires_at and grant.expires_at < datetime.utcnow():
                    continue
                
                # Get role permissions
                role = self.roles.get(grant.role_id)
                if role:
                    permissions.update(role.permissions)
                    
                    # Add inherited permissions
                    self._get_inherited_permissions(role, permissions)
            
            return permissions
    
    def _get_inherited_permissions(self, role: Role, permissions: Set[Permission]):
        """Recursively get inherited permissions"""
        if role.inherits_from and role.inherits_from in self.roles:
            parent_role = self.roles[role.inherits_from]
            permissions.update(parent_role.permissions)
            self._get_inherited_permissions(parent_role, permissions)
    
    def check_permission(
        self,
        entity_id: str,
        permission: Permission,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if an entity has a specific permission"""
        with self._lock:
            permissions = self.get_permissions(entity_id)
            
            # Check for sovereign override
            if Permission.SOVEREIGN_ALL in permissions:
                return True
            
            # Check direct permission
            if permission in permissions:
                # If resource specified, check resource-level permissions
                if resource_id and resource_id in self.resources:
                    resource = self.resources[resource_id]
                    if entity_id in resource.permissions:
                        return permission in resource.permissions[entity_id]
                
                return True
            
            return False
    
    def check_access(
        self,
        entity_id: str,
        action: str,
        resource_id: str
    ) -> Tuple[bool, str]:
        """Check if entity can perform action on resource"""
        with self._lock:
            # Map actions to permissions
            action_permissions = {
                "read": Permission.READ_OWN,
                "read_all": Permission.READ_ALL,
                "write": Permission.WRITE_OWN,
                "write_all": Permission.WRITE_ALL,
                "execute": Permission.EXECUTE_PUBLIC,
                "admin": Permission.EXECUTE_ADMIN,
                "critical": Permission.EXECUTE_CRITICAL
            }
            
            required_permission = action_permissions.get(action)
            if not required_permission:
                return False, f"Unknown action: {action}"
            
            # Check resource ownership
            if resource_id in self.resources:
                resource = self.resources[resource_id]
                
                # Owner has full access
                if resource.owner_id == entity_id:
                    return True, "Resource owner"
                
                # Check explicit permissions
                if entity_id in resource.permissions:
                    if required_permission in resource.permissions[entity_id]:
                        return True, "Explicit permission"
            
            # Check general permission
            if self.check_permission(entity_id, required_permission):
                return True, "Role permission"
            
            return False, "Access denied"
    
    def register_resource(
        self,
        resource_id: str,
        resource_type: str,
        owner_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register a new protected resource"""
        with self._lock:
            if resource_id in self.resources:
                return False
            
            resource = Resource(
                resource_id=resource_id,
                resource_type=resource_type,
                owner_id=owner_id,
                metadata=metadata or {}
            )
            
            self.resources[resource_id] = resource
            return True
    
    def set_resource_permission(
        self,
        resource_id: str,
        entity_id: str,
        permissions: Set[Permission],
        set_by: str
    ) -> bool:
        """Set permissions for an entity on a resource"""
        with self._lock:
            if resource_id not in self.resources:
                return False
            
            if not self.check_permission(set_by, Permission.MANAGE_SYSTEM):
                return False
            
            self.resources[resource_id].permissions[entity_id] = permissions
            self._audit("SET_PERM", set_by, entity_id, {"resource": resource_id, "permissions": [p.value for p in permissions]})
            return True
    
    def create_custom_role(
        self,
        name: str,
        permissions: Set[Permission],
        inherits_from: Optional[str] = None,
        description: str = "",
        created_by: str = ""
    ) -> Tuple[bool, str]:
        """Create a custom role"""
        with self._lock:
            if not self.check_permission(created_by, Permission.MANAGE_ROLES):
                return False, "Permission denied"
            
            role_id = f"role_custom_{int(time.time() * 1000)}"
            
            self.roles[role_id] = Role(
                role_id=role_id,
                name=name,
                permissions=permissions,
                inherits_from=inherits_from,
                description=description,
                is_system=False
            )
            
            self._audit("CREATE_ROLE", created_by, role_id, {"permissions": [p.value for p in permissions]})
            return True, role_id
    
    def _audit(self, action: str, actor: str, target: str, details: Dict[str, Any]):
        """Log an audit entry"""
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "target": target,
            "details": details
        })
        
        # Keep last 10000 entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
    
    def get_entity_roles(self, entity_id: str) -> List[str]:
        """Get all roles assigned to an entity"""
        with self._lock:
            roles = []
            if entity_id not in self.entity_grants:
                return roles
            
            for grant_id in self.entity_grants[entity_id]:
                grant = self.grants.get(grant_id)
                if grant and grant.role_id in self.roles:
                    if not grant.expires_at or grant.expires_at > datetime.utcnow():
                        roles.append(grant.role_id)
            
            return roles
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        with self._lock:
            return self.audit_log[-limit:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get access controller status"""
        with self._lock:
            return {
                "total_roles": len(self.roles),
                "system_roles": sum(1 for r in self.roles.values() if r.is_system),
                "custom_roles": sum(1 for r in self.roles.values() if not r.is_system),
                "total_grants": len(self.grants),
                "entities_with_access": len(self.entity_grants),
                "protected_resources": len(self.resources),
                "audit_entries": len(self.audit_log)
            }


# Module interface
def create_module(config: Optional[Dict[str, Any]] = None) -> AccessController:
    """Factory function to create AccessController module"""
    return AccessController(config)


if __name__ == "__main__":
    ac = AccessController()
    
    # Test GLM-7 access
    print("GLM-7 permissions:", [p.value for p in ac.get_permissions("ki_glm_001")])
    
    # Test permission check
    has_perm = ac.check_permission("ki_glm_001", Permission.KI_SELF_MODIFY)
    print(f"GLM-7 can self-modify: {has_perm}")
    
    # Register a resource
    ac.register_resource("sys_config", "configuration", "baron_ialongo")
    can_access, reason = ac.check_access("ki_glm_001", "read", "sys_config")
    print(f"GLM-7 can read sys_config: {can_access} ({reason})")
    
    print("\nStatus:", json.dumps(ac.get_status(), indent=2))
