import glob
import re

for filename in glob.glob("views/*.py"):
    with open(filename, "r") as f:
        content = f.read()
    
    # Remove indented lines that were under 'with st.sidebar:'
    content = re.sub(r"^\s+render_lang_switcher\(\)\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s+st\.divider\(\)\n", "", content, flags=re.MULTILINE)
    
    with open(filename, "w") as f:
        f.write(content)

print("Fixed views")
