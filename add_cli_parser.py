import re

with open("email_parser.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """if __name__ == "__main__":
    # For local testing
    pass"""

new_code = """if __name__ == "__main__":
    import sys
    if "--run-all-users" in sys.argv:
        print("Starting batch email sync for all users...")
        from supabase_db import _table
        # Get all users with IMAP settings
        try:
            res = _table("notification_settings").select("user_id").eq("key", "imap_email").execute()
            user_ids = list(set([r["user_id"] for r in (res.data or [])]))
            print(f"Found {len(user_ids)} users with IMAP configured.")
            
            for uid in user_ids:
                try:
                    print(f"Syncing for user {uid}...")
                    result = run_email_sync(uid)
                    print(f"User {uid}: Found {result['found']} emails, Inserted {result['inserted']} txns.")
                except Exception as e:
                    print(f"User {uid} failed: {e}")
        except Exception as e:
            print(f"Error fetching users: {e}")
    else:
        print("Run with --run-all-users to sync all accounts.")
"""

if target in content:
    content = content.replace(target, new_code)
    with open("email_parser.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated email_parser.py with CLI entry point")
else:
    print("Target not found in email_parser.py")
