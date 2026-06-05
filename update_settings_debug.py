import re

with open("views/05_settings.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """            st.success(t("sync_success", found=results.get("found", 0), inserted=results.get("inserted", 0)))
            if results.get('inserted', 0) > 0:
                st.balloons()"""

new_code = """            st.success(t("sync_success", found=results.get("found", 0), inserted=results.get("inserted", 0)))
            if results.get('inserted', 0) > 0:
                st.balloons()
            elif results.get('found', 0) > 0 and results.get('debug_text'):
                with st.expander("🔍 找不到交易？查看系統萃取出的文字 (點擊展開)"):
                    st.markdown("請將下方這段文字複製貼上給 AI 助理，讓他幫您調整解析邏輯！")
                    st.code(results.get('debug_text'))"""

if target in content:
    content = content.replace(target, new_code)
    with open("views/05_settings.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated 05_settings.py to show debug text")
else:
    print("Target not found in 05_settings.py")
