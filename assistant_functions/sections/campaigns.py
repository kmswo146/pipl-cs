"""
Campaign Management Functions
Functions for getting campaign information, status, and diagnostics
"""

from ..database import AssistantDB
from ..function_registry import FunctionDefinition
from ..workspace_resolver import resolve_workspace_and_org
from bson import ObjectId

# Campaign status constants
CAMPAIGN_STATUSES = ["ACTIVE", "PAUSED", "ERROR", "INACTIVE", "COMPLETED"]


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
                "description": "Filter by campaign status (ACTIVE, PAUSED, ERROR, INACTIVE, COMPLETED)", 
                "required": False
            },
            "limit": {
                "type": "integer", 
                "description": "Maximum number of campaigns to return (default: 10)", 
                "required": False
            },
            "mode": {
                "type": "string", 
                "description": "Output mode: BASIC (essential info only) or FULL (complete details). Default: BASIC", 
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


def get_campaigns(user_email=None, workspace_id=None, workspace_name=None, status=None, limit=10, mode="BASIC"):
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
            "organization_id": ObjectId(resolved_org_id),
            "status": {"$ne": "DELETED"}  # Always exclude DELETED campaigns
        }
        
        # Add status filter if specified
        if status:
            campaign_query["status"] = status.upper()
        
        print(f"DEBUG: Campaign query: {campaign_query}")
        print(f"DEBUG: Resolved workspace_id: {resolved_workspace_id}")
        print(f"DEBUG: Resolved org_id: {resolved_org_id}")
        print(f"DEBUG: Mode: {mode}, Limit: {limit}")
        
        # Choose projection based on mode
        if mode.upper() == "BASIC":
            projection = {
                "_id": 1,
                "camp_name": 1,
                "status": 1,
                "workspace_id": 1,
                "organization_id": 1,
                "lead_count": 1,
                "sent_count": 1,
                "opened_count": 1,
                "replied_count": 1,
                "bounced_count": 1,
                "lead_contacted_count": {"$ifNull": ["$lead_contacted_count", 0]},
                "created_at": 1,
                "modified_at": 1,
                "daily_limit": 1,
                "open_rate": {
                    "$cond": {
                        "if": {"$eq": ["$lead_contacted_count", 0]},
                        "then": 0,
                        "else": {
                            "$round": [
                                {
                                    "$multiply": [
                                        {"$divide": ["$unique_opened_count", "$lead_contacted_count"]},
                                        100
                                    ]
                                }, 1]
                        }
                    }
                },
                "replied_rate": {
                    "$cond": {
                        "if": {"$eq": ["$lead_contacted_count", 0]},
                        "then": 0,
                        "else": {
                            "$round": [
                                {
                                    "$multiply": [
                                        {"$divide": ["$replied_count", "$lead_contacted_count"]},
                                        100
                                    ]
                                }, 1]
                        }
                    }
                }
            }
        else:
            # Full projection (your original complex one)
            projection = {
                    "_id": 1, 
                    "camp_name": 1, 
                    "parent_camp_id": 1, 
                    "events": {"$ifNull": ["$events", None]}, 
                    "first_wait_time": {"$ifNull": ["$first_wait_time", None]},
                    "organization_id": 1, 
                    "workspace_id": 1, 
                    "status": 1, 
                    "lead_count": 1, 
                    "tags": {"$ifNull": ["$tags", None]},
                    "email_accounts": 1, 
                    "ea_n_tags": {"$ifNull": ["$ea_n_tags", None]},
                    "sent_count": 1, 
                    "opened_count": 1, 
                    "unique_opened_count": 1, 
                    "replied_count": 1, 
                    "bounced_count": 1, 
                    "unsubscribed_count": 1, 
                    "linkclick_count": 1,
                    "unique_linkclick_count": 1, 
                    "linkopened_count": 1, 
                    "unique_linkopened_count": 1, 
                    "lead_contacted_count": {"$ifNull": ["$lead_contacted_count", 0]},
                    "daily_limit": 1, 
                    "interval_limit_in_min": 1, 
                    "stop_on_lead_replied": 1, 
                    "is_link_tracking": 1, 
                    "is_emailopened_tracking": 1,
                    "created_at": 1, 
                    "modified_at": 1, 
                    "created_by": 1, 
                    "modified_by": 1, 
                    "send_priority": 1, 
                    "is_unsubscribed_link": 1, 
                    "send_as_txt": 1, 
                    "last_lead_sent": 1,
                    "error_desc": {"$ifNull": ["$error_desc", ""]},
                    "camp_st_date": {"$ifNull": ["$camp_st_date", ""]},
                    "camp_end_date": {"$ifNull": ["$camp_end_date", ""]},
                    "email_sent_today": {"$ifNull": ["$email_sent_today", ""]},
                    "positive_reply_count": {"$ifNull": ["$positive_reply_count", 0]},
                    "negative_reply_count": {"$ifNull": ["$negative_reply_count", 0]},
                    "neutral_reply_count": {"$ifNull": ["$neutral_reply_count", 0]},
                    "opportunity_val": {"$ifNull": ["$opportunity_val", 0]},
                    "exclude_ooo": 1,
                    "is_acc_based_sending": 1,
                    "is_pause_on_bouncerate": {"$ifNull": ["$is_pause_on_bouncerate", 0]},
                    "bounce_rate_limit": {"$ifNull": ["$bounce_rate_limit", 5]},
                    "is_paused_at_bounced": {"$ifNull": ["$is_paused_at_bounced", 0]},
                    "last_paused_at_bounced": {"$ifNull": ["$last_paused_at_bounced", ""]},
                    "send_risky_email": {"$ifNull": ["$send_risky_email", 0]},
                    "unsub_blocklist": {"$ifNull": ["$unsub_blocklist", 0]},
                    "other_email_acc": {"$ifNull": ["$other_email_acc", 0]},
                    "err_email_acc": {"$ifNull": ["$err_email_acc", 0]},
                    "is_esp_match": {"$ifNull": ["$is_esp_match", 0]},
                    "ooo_nr_opt": {"$ifNull": ["$ooo_nr_opt", None]},
                    "ooo_nr_ai_d": {"$ifNull": ["$ooo_nr_ai_d", 7]},
                    "ooo_nr_d": {"$ifNull": ["$ooo_nr_d", 7]},
                    "error_time": 1,
                    "new_lead_contacted_today": 1,
                    "monthly_mail_reached": 1,
                    "schedule": {"$ifNull": ["$schedule", {}]},
                    "completed_lead_count": {"$ifNull": ["$completed_lead_count", 0]},
                    "custom_fields": {"$ifNull": ["$custom_fields", ""]},
                    "sequences": {"$ifNull": ["$sequences", []]},
                    "sequence_steps": {"$size": {"$ifNull": ["$sequences", []]}},
                    "sheet_tasks": {"$ifNull": ["$sheet_tasks", []]},
                    "camp_emails": {"$ifNull": ["$camp_emails", []]},
                    "template_id": {"$ifNull": ["$template_id", ""]},
                    "is_ev_processing": {"$ifNull": ["$is_ev_processing", 0]},
                    "open_rate": {
                        "$cond": {
                            "if": {"$eq": ["$lead_contacted_count", 0]},
                            "then": 0,
                            "else": {
                                "$round": [
                                    {
                                        "$multiply": [
                                            {"$divide": ["$unique_opened_count", "$lead_contacted_count"]},
                                            100
                                        ]
                                    }, 1]
                            }
                        }
                    },
                    "replied_rate": {
                        "$cond": {
                            "if": {"$eq": ["$lead_contacted_count", 0]},
                            "then": 0,
                            "else": {
                                "$round": [
                                    {
                                        "$multiply": [
                                            {"$divide": ["$replied_count", "$lead_contacted_count"]},
                                            100
                                        ]
                                    }, 1]
                            }
                        }
                    },
                    "is_replied_email_account_id": {"$ifNull": ["$is_replied_email_account_id", 0]},
                    "is_subseq_add_cc": {"$ifNull": ["$is_subseq_add_cc", 0]},
                    "subseq_add_cc": {"$ifNull": ["$subseq_add_cc", []]}
            }
        
        # MongoDB aggregation pipeline
        pipeline = [
            {"$match": campaign_query},
            {"$project": projection},
            {"$sort": {"created_at": -1}},
            {"$limit": limit}
        ]
        
        # Execute aggregation pipeline
        campaigns_cursor = db.execute_query("campaigns", "aggregate", pipeline)
        
        campaigns_list = []
        status_counts = {}
        
        print(f"DEBUG: Processing campaigns from cursor...")
        
        for campaign in campaigns_cursor:
            campaign_status = campaign.get("status", "UNKNOWN")
            status_counts[campaign_status] = status_counts.get(campaign_status, 0) + 1
            
            # Debug: Print each campaign details
            print(f"DEBUG: Campaign - ID: {campaign.get('_id')}, Name: {campaign.get('camp_name')}, Status: {campaign_status}")
            print(f"       Workspace: {campaign.get('workspace_id')}, Org: {campaign.get('organization_id')}")
            
            # Convert ObjectId to string for JSON serialization
            if "_id" in campaign:
                campaign["_id"] = str(campaign["_id"])
            if "organization_id" in campaign:
                campaign["organization_id"] = str(campaign["organization_id"])
            if "workspace_id" in campaign:
                campaign["workspace_id"] = str(campaign["workspace_id"])
            
            campaigns_list.append(campaign)
        
        print(f"DEBUG: Found {len(campaigns_list)} campaigns")
        print(f"DEBUG: Status counts: {status_counts}")
        
        # Debug: Print the actual return data structure
        result = {
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
        
        print(f"DEBUG: Returning {len(result['campaigns'])} campaigns to Katie")
        print(f"DEBUG: Campaign names: {[c.get('camp_name') for c in result['campaigns']]}")
        
        return result
        
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