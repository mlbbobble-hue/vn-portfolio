import re

with open("auth_page.py", "r") as f:
    content = f.read()

# 1. Make logo bigger
content = content.replace('width: 80px; height: 80px;', 'width: 250px; height: 250px;')

# 2. Remove title and tagline
content = re.sub(r'<div class="title">[^<]*</div>', '', content)
content = re.sub(r'<div class="sub">[^<]*</div>', '', content)

with open("auth_page.py", "w") as f:
    f.write(content)
print("Updated auth_page.py")
