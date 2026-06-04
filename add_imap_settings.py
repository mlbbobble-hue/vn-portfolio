import re

with open("supabase_db.py", "r", encoding="utf-8") as f:
    content = f.read()

new_functions = """
def sb_save_imap_settings(user_id: str, imap_email: str, imap_password: str, broker_name: str):
    for key, val in [("imap_email", imap_email),
                     ("imap_password", imap_password),
                     ("broker_name", broker_name)]:
        _table("notification_settings").upsert({
            "user_id": user_id, "key": key, "value": val
        }, on_conflict="user_id,key").execute()

def sb_load_imap_settings(user_id: str) -> dict:
    res = _table("notification_settings").select("key,value").eq("user_id", user_id).in_("key", ["imap_email", "imap_password", "broker_name"]).execute()
    return {r["key"]: r["value"] for r in (res.data or [])}

"""

target = """def sb_save_notification_settings(user_id: str, telegram_token: str,"""

if target in content:
    content = content.replace(target, new_functions + "\n" + target)
    with open("supabase_db.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("IMAP settings functions added to supabase_db.py")
else:
    print("Target not found in supabase_db.py")
