"""
Shared workspace and organization ID resolver
Handles workspace/organization resolution logic used across all functions
"""

from .database import AssistantDB
from bson import ObjectId
import re


def resolve_workspace_and_org(user_email=None, workspace_id=None, workspace_name=None):
    """
    Shared function to resolve workspace_id and organization_id
    
    Args:
        user_email: User's email (required if no workspace_id specified)
        workspace_id: Explicit workspace ID (if provided, use this)
        workspace_name: Workspace name to search for (AI should extract this from query)
    
    Returns:
        dict: {
            "workspace_id": str,
            "organization_id": str, 
            "workspace_name": str,
            "error": str (if any)
        }
    """
    
    db = AssistantDB()
    
    try:
        # Case 1: Explicit workspace_id provided
        if workspace_id:
            return _resolve_from_workspace_id(db, workspace_id)
        
        # Case 2: Workspace name provided (AI should determine this from query context)
        if workspace_name:
            return _resolve_from_workspace_name(db, user_email, workspace_name)
        
        # Case 3: Default to user's primary workspace
        if user_email:
            return _resolve_user_primary_workspace(db, user_email)
        
        return {"error": "No user email or workspace identifier provided"}
        
    except Exception as e:
        return {"error": f"Failed to resolve workspace: {str(e)}"}


def _resolve_from_workspace_id(db, workspace_id):
    """Resolve organization from explicit workspace ID"""
    try:
        ws_id_obj = ObjectId(workspace_id) if isinstance(workspace_id, str) else workspace_id
        
        # Get workspace document
        ws_doc = db.execute_query("workspaces", "find_one", {"_id": ws_id_obj})
        if not ws_doc:
            return {"error": f"Workspace not found: {workspace_id}"}
        
        org_id = ws_doc.get("org_id")
        if not org_id:
            return {"error": f"No organization found for workspace: {workspace_id}"}
        
        return {
            "workspace_id": str(ws_id_obj),
            "organization_id": str(org_id),
            "workspace_name": ws_doc.get("name", "Unknown")
        }
        
    except Exception as e:
        return {"error": f"Invalid workspace ID format: {workspace_id}"}


def _resolve_from_workspace_name(db, user_email, workspace_name):
    """Resolve workspace by name using AI to match against user's accessible workspaces"""
    if not user_email:
        return {"error": "User email required for workspace name lookup"}
    
    # Get user's workspaces
    user_doc = db.execute_query("users", "find_one", {"email": user_email.lower()})
    if not user_doc:
        return {"error": f"User not found: {user_email}"}
    
    user_workspaces = user_doc.get("workspaces", [])
    
    # Get all workspace names
    available_workspaces = []
    workspace_map = {}
    
    for ws_info in user_workspaces:
        ws_id_obj = ws_info.get("workspace_id")
        if not ws_id_obj:
            continue
        
        # Get workspace document
        ws_doc = db.execute_query("workspaces", "find_one", {"_id": ws_id_obj})
        if not ws_doc:
            continue
        
        ws_name = ws_doc.get("name", "")
        org_id = ws_doc.get("org_id")
        
        if ws_name and org_id:
            available_workspaces.append(ws_name)
            workspace_map[ws_name] = {
                "workspace_id": str(ws_id_obj),
                "organization_id": str(org_id),
                "workspace_name": ws_name
            }
    
    if not available_workspaces:
        return {"error": f"No valid workspaces found for user: {user_email}"}
    
    # Use AI to find the best match
    import openai_utils
    import config
    
    try:
        match_prompt = f"""User is looking for workspace: "{workspace_name}"

Available workspaces:
{chr(10).join(f"- {ws}" for ws in available_workspaces)}

Which workspace name is the best match? Return ONLY the exact workspace name from the list above, or "NONE" if no good match exists.

Best match:"""

        response_obj = openai_utils.call_openai_with_retry(
            messages=[{"role": "user", "content": match_prompt}],
            max_completion_tokens=50,
            temperature=0.1,
            model=config.NANO
        )
        
        if response_obj and response_obj.choices:
            matched_name = response_obj.choices[0].message.content.strip()
            
            if matched_name == "NONE":
                return {"error": f"No good workspace match found for '{workspace_name}' among available workspaces"}
            
            if matched_name in workspace_map:
                print(f"DEBUG: AI matched '{workspace_name}' -> '{matched_name}'")
                return workspace_map[matched_name]
            else:
                # Fallback if AI returned something not in the list
                return {"error": f"AI returned invalid workspace name: {matched_name}"}
        
    except Exception as e:
        print(f"Error using AI for workspace matching: {e}")
    
    # Fallback: no match found
    return {"error": f"Could not match workspace '{workspace_name}' to any available workspace"}


def _resolve_user_primary_workspace(db, user_email):
    """Get user's primary workspace (preference: OWNER > first active > first any)"""
    user_doc = db.execute_query("users", "find_one", {"email": user_email.lower()})
    if not user_doc:
        return {"error": f"User not found: {user_email}"}
    
    user_workspaces = user_doc.get("workspaces", [])
    if not user_workspaces:
        return {"error": f"User has no accessible workspaces: {user_email}"}
    
    owner_workspaces = []
    active_workspaces = []
    all_workspaces = []
    
    for ws_info in user_workspaces:
        ws_id_obj = ws_info.get("workspace_id")
        role_name = ws_info.get("role_name", "")
        
        if not ws_id_obj:
            continue
        
        # Get workspace document
        ws_doc = db.execute_query("workspaces", "find_one", {"_id": ws_id_obj})
        if not ws_doc:
            continue
        
        org_id = ws_doc.get("org_id")
        if not org_id:
            continue
        
        workspace_data = {
            "workspace_id": str(ws_id_obj),
            "organization_id": str(org_id),
            "workspace_name": ws_doc.get("name", "Unknown"),
            "role": role_name,
            "status": ws_doc.get("status", "Unknown")
        }
        
        all_workspaces.append(workspace_data)
        
        if role_name == "OWNER":
            owner_workspaces.append(workspace_data)
        
        if ws_doc.get("status") == "ACTIVE":
            active_workspaces.append(workspace_data)
    
    if not all_workspaces:
        return {"error": f"No valid workspaces found for user: {user_email}"}
    
    # Priority: Owner workspaces > Active workspaces > Any workspace
    if owner_workspaces:
        primary = owner_workspaces[0]
    elif active_workspaces:
        primary = active_workspaces[0]
    else:
        primary = all_workspaces[0]
    
    return {
        "workspace_id": primary["workspace_id"],
        "organization_id": primary["organization_id"],
        "workspace_name": primary["workspace_name"]
    }


