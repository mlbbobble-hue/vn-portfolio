import sys
import os
import streamlit as st
from supabase_db import sign_up

os.environ["SUPABASE_URL"] = st.secrets["SUPABASE_URL"]
os.environ["SUPABASE_KEY"] = st.secrets["SUPABASE_KEY"]

res = sign_up("mlbbobble@gmail.com", "i4013624", "frederick chen")
print(res)
