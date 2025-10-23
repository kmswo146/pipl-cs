"""
User Plan & Workspace Functions
Functions for checking user plans, workspace membership, and billing information
"""

from ..database import AssistantDB
from ..function_registry import FunctionDefinition


def register_user_plan_functions(registry):
    """Register all user plan-related functions"""
    
    # Register the section
    registry.register_section(
        "user_plans", 
        "User plan checking, workspace membership, and billing information",
        "user_plans_info"  # Will load from context/user_plans_info.txt
    )
    
    # Check user plan function
    registry.register_function(FunctionDefinition(
        name="check_user_plan",
        description="Get user plan information and workspace details",
        section="user_plans",
        inputs={
            "user_email": {
                "type": "string", 
                "description": "Email of the user to check (if different from conversation user)", 
                "required": False
            },
            "workspace_id": {
                "type": "string", 
                "description": "Specific workspace ID to check", 
                "required": False
            },
            "workspace_name": {
                "type": "string", 
                "description": "Workspace name to search for (e.g., 'Yaro's workspace')", 
                "required": False
            }
        },
        outputs={
            "user_info": {
                "type": "object",
                "description": "User details including email, plan, status"
            },
            "workspace_info": {
                "type": "object",
                "description": "Workspace details including plan, limits, usage"
            },
            "plan_details": {
                "type": "object",
                "description": "Plan features, limits, and billing information"
            }
        },
        function_callable=check_user_plan,
        examples=[
            "Check current user: check_user_plan()",
            "Check specific user: check_user_plan(user_email='user@example.com')",
            "Check workspace: check_user_plan(workspace_id='ws_123')",
            "Check by workspace name: check_user_plan(workspace_name='Yaro\\'s workspace')"
        ]
    ))


# Function implementation - BASED ON YOUR WORKING CODE
def check_user_plan(user_email=None, workspace_id=None, workspace_name=None):
    """
    Check user plan and associated workspace information.
    Returns ALL workspaces the user has access to with names, plans, owners.
    If workspace_name is provided, resolves it to workspace_id first.
    """
    from bson import ObjectId
    
    db = AssistantDB()
    
    try:
        # If workspace_name is provided, resolve it to workspace_id first
        if workspace_name and not workspace_id:
            from ..workspace_resolver import resolve_workspace_and_org
            resolution = resolve_workspace_and_org(
                user_email=user_email,
                workspace_name=workspace_name
            )
            if "error" in resolution:
                return {"error": f"Could not resolve workspace '{workspace_name}': {resolution['error']}"}
            workspace_id = resolution["workspace_id"]
        
        if not user_email:
            return {"error": "No user email provided. Please specify user_email parameter."}
        
        # 1) Find user by email
        user_doc = db.execute_query("users", "find_one", {"email": user_email.lower()})
        if not user_doc:
            return {"error": f"User not found: {user_email}"}
        
        workspace_info_list = []
        user_workspaces = user_doc.get("workspaces", [])
        
        for idx, ws_info in enumerate(user_workspaces, start=1):
            ws_id_obj = ws_info.get("workspace_id")
            if not ws_id_obj:
                continue
                
            role_name = ws_info.get("role_name", "N/A")
            
            # Get workspace document
            ws_doc = db.execute_query("workspaces", "find_one", {"_id": ws_id_obj})
            if not ws_doc:
                continue
                
            workspace_name = ws_doc.get("name", f"Workspace {str(ws_id_obj)}")
            workspace_status = ws_doc.get("status", "Unknown")
            
            # Get organization and plan details
            org_id = ws_doc.get("org_id")
            plan_name = "N/A"
            owner_email = "N/A"
            internal_group = "N/A"
            
            if org_id:
                # Get organization document
                org_doc = db.execute_query("organizations", "find_one", {"_id": org_id})
                if org_doc:
                    # Get plan name
                    plan_id = org_doc.get("plan_id")
                    if plan_id:
                        plan_doc = db.execute_query("plans", "find_one", {"_id": plan_id})
                        if plan_doc:
                            plan_name = plan_doc.get("plan_name", "N/A")
                    
                    # Find workspace owner
                    owner_query = {
                        "workspaces": {
                            "$elemMatch": {
                                "org_id": org_id,
                                "role_name": "OWNER"
                            }
                        }
                    }
                    owner_doc = db.execute_query("users", "find_one", owner_query)
                    if owner_doc:
                        owner_email = owner_doc.get("email", "N/A")
                    
                    internal_group = org_doc.get("internal_group", "N/A")
            
            workspace_info_list.append({
                "workspace_id": str(ws_id_obj),
                "workspace_name": workspace_name,
                "role_name": role_name,
                "plan_name": plan_name,
                "owner_email": owner_email,
                "status": workspace_status,
                "internal_group": internal_group
            })
        
        # Count active/inactive workspaces
        active_workspaces = sum(1 for ws in workspace_info_list if ws["status"] == "ACTIVE")
        inactive_workspaces = sum(1 for ws in workspace_info_list if ws["status"] == "INACTIVE")
        
        return {
            "user_info": {
                "email": user_doc.get("email"),
                "first_name": user_doc.get("first_name"),
                "last_name": user_doc.get("last_name"),
                "role_name": user_doc.get("role_name"),
                "status": user_doc.get("status")
            },
            "workspaces": workspace_info_list,
            "workspace_summary": {
                "total_workspaces": len(workspace_info_list),
                "active_workspaces": active_workspaces,
                "inactive_workspaces": inactive_workspaces
            }
        }
        
    except Exception as e:
        import traceback
        print(f"Error in check_user_plan: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Failed to check user plan: {str(e)}"}


# Add more functions as needed
def get_workspace_members(workspace_id):
    """Get all members of a workspace"""
    # TODO: Implement based on your data structure
    pass


def check_plan_limits(workspace_id):
    """Check current usage against plan limits"""
    # TODO: Implement based on your data structure
    pass