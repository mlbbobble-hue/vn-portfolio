import re
import base64

def replace_in_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We will replace the whole <img src="data:image/... "> tag
    # with a dynamic f-string variable {logo_img_tag}
    # But wait, in app.py it's already an f-string: f"""..."""
    # So if we insert {logo_base64} it will work if we define logo_base64 before.
    
    pattern = re.compile(r'<img src="data:image/[^;]+;base64,[^"]+"([^>]*)>')
    
    def replacer(match):
        attrs = match.group(1)
        return f'<img src="data:image/png;base64,{{logo_base64}}" {attrs}>'
        
    new_content = pattern.sub(replacer, content)
    
    if new_content != content:
        # Prepend the logic to read the file
        prefix = """
import base64
try:
    with open("assets/logo.png", "rb") as _f:
        logo_base64 = base64.b64encode(_f.read()).decode()
except:
    logo_base64 = ""
"""
        # Find where to insert prefix. After imports.
        # Let's just insert it after the first import or at the top after docstring.
        if 'import streamlit as st' in new_content:
            new_content = new_content.replace('import streamlit as st', 'import streamlit as st\n' + prefix, 1)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filename}")
    else:
        print(f"No match in {filename}")

replace_in_file("app.py")
replace_in_file("auth_page.py")
