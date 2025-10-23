"""
Playbook Definitions
Predefined step-by-step guides for common troubleshooting scenarios
"""

# Campaign diagnosis playbook
CAMPAIGN_DIAGNOSIS_PLAYBOOK = {
    "name": "Campaign Not Sending Diagnosis",
    "description": "Step-by-step guide to diagnose why campaigns are not sending emails",
    "steps": [
        "Check campaign status and configuration",
        "Verify email accounts are active and healthy", 
        "Check if campaign has sufficient email accounts",
        "Verify campaign scheduling and timing settings",
        "Check for rate limiting or delivery issues",
        "Examine recent error logs and bounce rates",
        "Identify specific bottleneck or failure point"
    ]
}

# User plan diagnosis playbook  
USER_PLAN_DIAGNOSIS_PLAYBOOK = {
    "name": "User Plan and Access Issues",
    "description": "Diagnose user plan, workspace, and access problems",
    "steps": [
        "Get user account information and current plan",
        "Check workspace membership and permissions",
        "Verify plan limits and current usage",
        "Check billing and subscription status",
        "Identify specific access limitation or issue"
    ]
}

# Email account health playbook
EMAIL_HEALTH_PLAYBOOK = {
    "name": "Email Account Health Check",
    "description": "Comprehensive health check for email accounts",
    "steps": [
        "Get all email accounts for user/workspace",
        "Check account status and last activity",
        "Review recent error logs and authentication issues",
        "Check sending limits and current usage",
        "Verify SMTP/IMAP connection health",
        "Identify accounts needing attention"
    ]
}

# Available playbooks registry
AVAILABLE_PLAYBOOKS = {
    "campaign_diagnosis": CAMPAIGN_DIAGNOSIS_PLAYBOOK,
    "user_plan_diagnosis": USER_PLAN_DIAGNOSIS_PLAYBOOK,
    "email_health": EMAIL_HEALTH_PLAYBOOK
}

def get_playbook(playbook_name):
    """Get a playbook by name"""
    return AVAILABLE_PLAYBOOKS.get(playbook_name)

def list_playbooks():
    """List all available playbooks"""
    return {name: playbook["description"] for name, playbook in AVAILABLE_PLAYBOOKS.items()}