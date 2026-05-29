import base64

with open("assets/logo.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode()

html_img = f'<img src="data:image/png;base64,{encoded_string}" style="width: 80px; height: 80px; border-radius: 12px;">'

with open("auth_page.py", "r") as f:
    content = f.read()

# Replace the SVG tree logo with the base64 image
svg_str = '<svg width="64" height="64" viewBox="0 0 24 24" fill="var(--financial-up, #10b981)" xmlns="http://www.w3.org/2000/svg"><path d="M17 12C18.6569 12 20 10.6569 20 9C20 7.34315 18.6569 6 17 6C16.8202 6 16.6441 6.01579 16.4727 6.04618C15.8291 3.75549 13.6895 2 11.1111 2C8.53272 2 6.39308 3.75549 5.74945 6.04618C5.57811 6.01579 5.40194 6 5.22222 6C3.44263 6 2 7.34315 2 9C2 10.6569 3.44263 12 5.22222 12C5.35209 12 5.47955 11.9922 5.60421 11.977C6.07921 13.7277 7.72895 15 9.66667 15H10.5556V20C10.5556 21.1046 11.451 22 12.5556 22H13.4444C13.9967 22 14.4444 21.5523 14.4444 21V15H15.3333C17.2711 15 18.9208 13.7277 19.3958 11.977C19.5205 11.9922 19.6479 12 19.7778 12H17Z"/></svg>'
svg_str2 = '<svg width="64" height="64" viewBox="0 0 24 24" fill="#00A352" xmlns="http://www.w3.org/2000/svg"><path d="M17 12C18.6569 12 20 10.6569 20 9C20 7.34315 18.6569 6 17 6C16.8202 6 16.6441 6.01579 16.4727 6.04618C15.8291 3.75549 13.6895 2 11.1111 2C8.53272 2 6.39308 3.75549 5.74945 6.04618C5.57811 6.01579 5.40194 6 5.22222 6C3.44263 6 2 7.34315 2 9C2 10.6569 3.44263 12 5.22222 12C5.35209 12 5.47955 11.9922 5.60421 11.977C6.07921 13.7277 7.72895 15 9.66667 15H10.5556V20C10.5556 21.1046 11.451 22 12.5556 22H13.4444C13.9967 22 14.4444 21.5523 14.4444 21V15H15.3333C17.2711 15 18.9208 13.7277 19.3958 11.977C19.5205 11.9922 19.6479 12 19.7778 12H17Z"/></svg>'

content = content.replace(svg_str, html_img)
content = content.replace(svg_str2, html_img)

with open("auth_page.py", "w") as f:
    f.write(content)
print("done")
