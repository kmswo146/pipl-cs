"""
Campaign Management Functions
Functions for getting campaign information, status, and diagnostics
"""

from ..database import AssistantDB
from ..function_registry import FunctionDefinition
from ..workspace_resolver import resolve_workspace_and_org
from bson import ObjectId


def register_campaign_functions(registry):
    """Register all campaign-related functions"""
    
    # Register the section
    registry.register_section(
        "campaigns", 
        "Campaign management and diagnostics - view campaign status, settings, and performance",
        "campaigns_info"  # Will load from context/campaigns_info.txt if exists
    )
    
    # Get campaigns function
    registry.register_function(FunctionDefinition(
        name="get_campaigns",
        description="Get list of campaigns for a user or specific workspace",
        section="campaigns",
        inputs={
            "user_email": {
                "type": "string", 
                "description": "Email of the user (defaults to conversation user if not specified)", 
                "required": False
            },
            "workspace_id": {
                "type": "string", 
                "description": "Specific workspace ID to get campaigns for", 
                "required": False
            },
            "workspace_name": {
                "type": "string", 
                "description": "Workspace name to search for (e.g., 'Yaro's workspace')", 
                "required": False
            },
            "status": {
                "type": "string", 
                "description": "Filter by campaign status (ACTIVE, PAUSED, COMPLETED, etc.)", 
                "required": False
            },
            "limit": {
                "type": "integer", 
                "description": "Maximum number of campaigns to return (default: 20)", 
                "required": False
            }
        },
        outputs={
            "campaigns": {
                "type": "array",
                "description": "List of campaigns with ID, name, status, dates, and basic metrics"
            },
            "workspace_info": {
                "type": "object",
                "description": "Information about the workspace the campaigns belong to"
            },
            "summary": {
                "type": "object",
                "description": "Summary statistics about the campaigns"
            }
        },
        function_callable=get_campaigns,
        examples=[
            "Get user's campaigns: get_campaigns(user_email='user@example.com')",
            "Get campaigns for specific workspace: get_campaigns(workspace_name='Yaro\\'s workspace')",
            "Get active campaigns only: get_campaigns(user_email='user@example.com', status='ACTIVE')"
        ]
    ))


def get_campaigns(user_email=None, workspace_id=None, workspace_name=None, status=None, limit=20):
    """
    Get campaigns for a user or workspace
    
    Args:
        user_email: User email (if not specified, uses conversation context)
        workspace_id: Explicit workspace ID
        workspace_name: Workspace name to search for (AI should extract this from query)
        status: Filter by campaign status
        limit: Maximum campaigns to return
    
    Returns:
        dict: Campaign list with workspace info and summary
    """
    
    db = AssistantDB()
    
    try:
        # Resolve workspace and organization IDs
        resolution = resolve_workspace_and_org(
            user_email=user_email,
            workspace_id=workspace_id, 
            workspace_name=workspace_name
        )
        
        if "error" in resolution:
            return {"error": resolution["error"]}
        
        resolved_workspace_id = resolution["workspace_id"]
        resolved_org_id = resolution["organization_id"]
        workspace_name_resolved = resolution["workspace_name"]
        
        # Build campaign query
        campaign_query = {
            "workspace_id": ObjectId(resolved_workspace_id),
            "organization_id": ObjectId(resolved_org_id)
        }
        
        # Add status filter if specified
        if status:
            campaign_query["status"] = status.upper()
        
        # Get campaigns
        campaigns_cursor = db.execute_query(
            "campaigns", 
            "find", 
            campaign_query,
            limit=limit,
            sort=[("created_at", -1)]  # Most recent first
        )
        
        campaigns_list = []
        status_counts = {}
        
        for campaign in campaigns_cursor:
            campaign_status = campaign.get("status", "UNKNOWN")
            status_counts[campaign_status] = status_counts.get(campaign_status, 0) + 1
            
            # Get basic campaign info
            campaign_info = {
                "campaign_id": str(campaign.get("_id")),
                "name": campaign.get("name", "Unnamed Campaign"),
                "status": campaign_status,
                "created_at": campaign.get("created_at"),
                "updated_at": campaign.get("updated_at"),
                "campaign_type": campaign.get("campaign_type", "Unknown"),
                "total_contacts": campaign.get("total_contacts", 0),
                "emails_sent": campaign.get("emails_sent", 0),
                "emails_opened": campaign.get("emails_opened", 0),
                "emails_clicked": campaign.get("emails_clicked", 0),
                "bounce_rate": campaign.get("bounce_rate", 0),
                "reply_rate": campaign.get("reply_rate", 0)
            }
            
            campaigns_list.append(campaign_info)
        
        return {
            "campaigns": campaigns_list,
            "workspace_info": {
                "workspace_id": resolved_workspace_id,
                "workspace_name": workspace_name_resolved,
                "organization_id": resolved_org_id
            },
            "summary": {
                "total_campaigns": len(campaigns_list),
                "status_breakdown": status_counts,
                "filter_applied": {"status": status} if status else None
            }
        }
        
    except Exception as e:
        import traceback
        print(f"Error in get_campaigns: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Failed to get campaigns: {str(e)}"}


# Additional campaign functions can be added here
def get_campaign_details(campaign_id, user_email=None):
    """Get detailed information about a specific campaign"""
    # TODO: Implement detailed campaign view
    pass


def get_campaign_performance(campaign_id, user_email=None):
    """Get performance metrics for a specific campaign"""
    # TODO: Implement campaign performance analysis
    pass