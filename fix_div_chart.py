import re

with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """        # --- MUJI Style Bar Chart ---
        df_div_chart = all_divs[all_divs["ex_date"] != ""].copy()
        df_div_chart["ex_date"] = pd.to_datetime(df_div_chart["ex_date"], errors="coerce")
        df_div_chart = df_div_chart.dropna(subset=["ex_date"])
        df_div_chart["month"] = df_div_chart["ex_date"].dt.strftime("%Y-%m")"""

new_code = """        # --- Cyberpunk Style Bar Chart (CASH ONLY) ---
        df_div_chart = all_divs[all_divs["ex_date"] != ""].copy()
        df_div_chart["ex_date"] = pd.to_datetime(df_div_chart["ex_date"], errors="coerce")
        df_div_chart = df_div_chart.dropna(subset=["ex_date"])
        
        # 依照使用者要求：只看現金配息 (CASH ONLY)
        df_div_chart = df_div_chart[df_div_chart["type"] == "CASH"]
        
        df_div_chart["month"] = df_div_chart["ex_date"].dt.strftime("%Y-%m")"""

if target in content:
    content = content.replace(target, new_code)
    with open("views/03_dividends.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Dividends bar chart filtered to CASH ONLY")
else:
    print("Cannot find target string")
