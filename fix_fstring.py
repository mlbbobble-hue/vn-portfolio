import re

with open("views/03_dividends.py", "r", encoding="utf-8") as f:
    content = f.read()

target = """                        acc_html += \"\"\"
<div class="acc-header" style="grid-template-columns: 1.5fr 1fr 1fr;">
    <div class="acc-col-left">{t("div_sym")}</div>
    <div class="acc-col-right">{t("div_acc_cash_dist")}</div>
    <div class="acc-col-right">{t("div_acc_stock_dist")}</div>
</div>
\"\"\""""

new_code = """                        acc_html += f\"\"\"
<div class="acc-header" style="grid-template-columns: 1.5fr 1fr 1fr;">
    <div class="acc-col-left">{t("div_sym")}</div>
    <div class="acc-col-right">{t("div_acc_cash_dist")}</div>
    <div class="acc-col-right">{t("div_acc_stock_dist")}</div>
</div>
\"\"\""""

if target in content:
    content = content.replace(target, new_code)
    with open("views/03_dividends.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed f-string in 03_dividends.py")
else:
    print("Target not found in 03_dividends.py")
