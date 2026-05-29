import os
import streamlit as st
from supabase import create_client

os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]

client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    res = client.table("users_approval").update({"is_admin": True, "is_approved": True}).neq("email", "dummy").execute()
    print("Update result:", res.data)
except Exception as e:
    print("Error:", e)
