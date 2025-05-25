#!/usr/bin/env python3
"""
Script to manage Intercom bot status
Usage:
  python manage_bot.py status        # Check current status
  python manage_bot.py activate      # Set bot to ACTIVE
  python manage_bot.py deactivate    # Set bot to INACTIVE
"""

import sys
import db

def show_status():
    """Show current bot status"""
    is_active = db.is_bot_active()
    status = "ACTIVE" if is_active else "INACTIVE"
    print(f"Intercom Bot Status: {status}")
    return is_active

def activate_bot():
    """Activate the bot"""
    result = db.set_bot_status("ACTIVE")
    if result:
        print("✅ Bot ACTIVATED - Auto-replies enabled")
    else:
        print("❌ Failed to activate bot")

def deactivate_bot():
    """Deactivate the bot"""
    result = db.set_bot_status("INACTIVE")
    if result:
        print("🛑 Bot DEACTIVATED - Auto-replies disabled")
    else:
        print("❌ Failed to deactivate bot")

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "activate":
        activate_bot()
        show_status()
    elif command == "deactivate":
        deactivate_bot()
        show_status()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main() 