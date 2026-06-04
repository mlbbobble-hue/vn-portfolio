import base64
import re

try:
    with open("assets/auth_hero_bg.png", "rb") as f:
        bg_base64 = base64.b64encode(f.read()).decode()
except:
    bg_base64 = ""

with open("auth_page.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the two occurrences of reading logo.png
content = re.sub(
    r'import base64\ntry:\n\s+with open\("assets/logo.png", "rb"\) as _f:\n\s+logo_base64 = base64\.b64encode\(_f\.read\(\)\)\.decode\(\)\nexcept:\n\s+logo_base64 = ""\n',
    '',
    content
)

# New CSS properties to inject
new_css = f"""
.stApp {{
    background: url(data:image/png;base64,{bg_base64}) left center / 50% 100% no-repeat, var(--bg-main, #0f172a);
    background-attachment: fixed;
    min-height: 100vh;
}}
.block-container {{
    max-width: 50% !important;
    width: 50% !important;
    margin-left: 50% !important;
    padding: 0 5% !important;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 100vh;
}}
@media (max-width: 768px) {{
    .stApp {{
        background: var(--bg-main, #0f172a);
    }}
    .block-container {{
        max-width: 100% !important;
        width: 100% !important;
        margin-left: 0 !important;
        padding: 40px 20px !important;
    }}
}}
.auth-container {{
    max-width: 440px;
    width: 100%;
    margin: 0 auto;
}}
.auth-card {{
    background: rgba(15, 23, 42, 0.4); 
    border-radius: 20px;
    padding: 40px 36px;
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    box-shadow: 0 30px 60px rgba(0,0,0,0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
    position: relative;
    z-index: 1;
}}
/* Glowing border */
.auth-card::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    border-radius: 20px;
    padding: 1.5px;
    background: linear-gradient(135deg, rgba(59,130,246,0.5), rgba(16,185,129,0.5));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
    z-index: -1;
}}
"""

# Replace old CSS blocks using regex
content = re.sub(r'\.stApp\s*\{[^}]*\}', '', content)
content = re.sub(r'\.auth-container\s*\{[^}]*\}', '', content)
content = re.sub(r'\.auth-card\s*\{[^}]*\}', '', content)

# Inject new CSS right after html, body...
content = content.replace(
    "html, body, [class*=\"css\"] { font-family: 'Inter', sans-serif; }",
    "html, body, [class*=\"css\"] { font-family: 'Inter', sans-serif; }\n" + new_css
)

# New Logo SVG
new_logo_svg = '''
<svg width="100" height="100" viewBox="0 0 100 100" fill="none" style="margin: 0 auto; display: block; margin-bottom: 16px;">
    <defs>
        <linearGradient id="logoGrad" x1="0" y1="100" x2="100" y2="0" gradientUnits="userSpaceOnUse">
            <stop stop-color="#3b82f6"/>
            <stop offset="1" stop-color="#10b981"/>
        </linearGradient>
    </defs>
    <path d="M50 15 L15 80 L35 80 L50 45 L65 80 L85 80 Z" fill="url(#logoGrad)" fill-opacity="0.1" stroke="url(#logoGrad)" stroke-width="4"/>
    <path d="M40 60 L60 60" stroke="url(#logoGrad)" stroke-width="6" stroke-linecap="round"/>
    <path d="M50 15 L80 15 L80 30 M80 15 L65 15" stroke="url(#logoGrad)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''

# Replace the icon div
content = re.sub(
    r'<div class="icon">.*?</div>',
    f'<div class="icon">{new_logo_svg.strip()}</div>',
    content,
    flags=re.DOTALL
)

with open("auth_page.py", "w", encoding="utf-8") as f:
    f.write(content)

print("auth_page.py updated successfully.")
