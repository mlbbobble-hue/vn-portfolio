import re

with open("views/05_settings.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """            if results.get('inserted', 0) > 0:
                st.balloons()
            elif results.get('found', 0) > 0 and results.get('debug_text'):
                with st.expander("🔍 找不到交易？查看系統萃取出的文字 (點擊展開)"):
                    st.markdown("請將下方這段文字複製貼上給 AI 助理，讓他幫您調整解析邏輯！")
                    st.code(results.get('debug_text'))"""

new_code = """            if results.get('inserted', 0) > 0:
                st.balloons()
            
            if results.get('found', 0) > 0 and results.get('debug_text'):
                with st.expander("🔍 除錯資訊：查看系統萃取出的 PDF 原始文字 (點擊展開)"):
                    st.markdown("如果解析出的股號、買賣或價格有錯，請將下方這段文字複製貼上給 AI 助理，讓他幫您精準調整解析邏輯！")
                    st.code(results.get('debug_text'))"""

if target in content:
    content = content.replace(target, new_code)
    with open("views/05_settings.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated 05_settings.py to always show debug text")
else:
    print("Target not found in 05_settings.py")
