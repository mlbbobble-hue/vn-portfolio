import base64

with open("assets/logo.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode()

html_img = f'''<div style='text-align:center; padding:12px 0;'>
        <img src="data:image/png;base64,{encoded_string}" style="width: 140px; height: 140px; border-radius: 12px; margin-bottom: 8px;">
    </div>'''

with open("app.py", "r") as f:
    content = f.read()

import re
# Regex to match the sidebar logo block
content = re.sub(
    r"<div style='text-align:center; padding:12px 0;'>.*?</div>\s*</div>", 
    html_img, 
    content, 
    flags=re.DOTALL
)

with open("app.py", "w") as f:
    f.write(content)
print("Updated app.py")
