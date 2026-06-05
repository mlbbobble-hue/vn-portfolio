import os
import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables if running locally
load_dotenv()

# Set environment variable to force supabase logic in db_router
os.environ["STREAMLIT_CLOUD"] = "true"

from email_parser import run_email_sync
from supabase_db import sb_get_all_imap_users

def run_daily_sync():
    print(f"[{datetime.datetime.now()}] Starting automated daily email sync...")
    
    users = sb_get_all_imap_users()
    if not users:
        print("No users with IMAP settings configured.")
        return
        
    print(f"Found {len(users)} users with IMAP configured.")
    
    # We want to sync today's emails
    # To be safe, we'll use a start_date of today at 00:00:00 UTC+7
    # Since run_email_sync accepts a datetime, let's create today's date
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    success_count = 0
    fail_count = 0
    
    for uid in users:
        print(f"Syncing user {uid}...")
        try:
            results = run_email_sync(uid, start_date=today)
            found = results.get("found", 0)
            inserted = results.get("inserted", 0)
            print(f"  -> User {uid}: Found {found} PDF files, inserted {inserted} transactions.")
            success_count += 1
        except Exception as e:
            print(f"  -> Error syncing user {uid}: {e}")
            traceback.print_exc()
            fail_count += 1
            
    print("-" * 40)
    print(f"Sync complete. Success: {success_count}, Failures: {fail_count}")
    
if __name__ == "__main__":
    run_daily_sync()
