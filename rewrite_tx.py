import re

with open("views/02_transactions.py", "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace from line 249 to the end of the file.
# The original code starting at `f["淨金額"] = ...`

new_code = """        f["淨金額"] = f.apply(lambda r: r["shares"]*r["price"] + (r["fee"] if r["action"]=="BUY" else -r["fee"]), axis=1)
        f = f.reset_index(drop=True)
        
        st.markdown("### ✏️ 快速編輯與刪除 (Inline Edit & Delete)")
        st.info("💡 提示：您可以直接雙擊表格內的值進行修改，或是選取最左側的核取方塊後按下鍵盤的「Delete」鍵來刪除紀錄。修改完成後請點擊下方的「💾 儲存變更」。")
        
        edit_cols = ["id", "date", "broker", "symbol", "action", "shares", "price", "fee", "note"]
        
        edited_df = st.data_editor(
            f[edit_cols],
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="tx_data_editor",
            column_config={
                "id": st.column_config.NumberColumn(t("col_id"), disabled=True),
                "date": st.column_config.DateColumn(t("date")),
                "broker": st.column_config.SelectboxColumn(t("broker"), options=BROKERS),
                "symbol": st.column_config.TextColumn(t("symbol")),
                "action": st.column_config.SelectboxColumn(t("col_action"), options=["BUY", "SELL"]),
                "shares": st.column_config.NumberColumn(t("shares")),
                "price": st.column_config.NumberColumn(t("price")),
                "fee": st.column_config.NumberColumn(t("fee")),
                "note": st.column_config.TextColumn(t("note")),
            }
        )
        
        if st.button("💾 儲存所有變更 (Save Changes)", type="primary", use_container_width=True):
            changes = st.session_state.get("tx_data_editor", {})
            has_changes = False
            
            # Process deleted
            for idx in changes.get("deleted_rows", []):
                row_id = f.loc[int(idx), "id"]
                delete_transaction(int(row_id))
                has_changes = True
                
            # Process edited
            for idx, col_changes in changes.get("edited_rows", {}).items():
                row_id = f.loc[int(idx), "id"]
                update_transaction(int(row_id), col_changes)
                has_changes = True
                
            if has_changes:
                st.success("✅ 變更已成功儲存！")
                st.rerun()
            else:
                st.info("您沒有做出任何修改。")
"""

import ast
try:
    idx = content.index('f["淨金額"] = f.apply(lambda r: r["shares"]*r["price"]')
    content = content[:idx] + new_code
    with open("views/02_transactions.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Success")
except ValueError:
    print("Target string not found!")
