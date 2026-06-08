import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import os

def send_admin_notification(new_user_email: str):
    """寄送新用戶註冊通知信給管理員"""
    try:
        # 嘗試從 secrets 讀取設定
        sender_email = st.secrets.get("SMTP_EMAIL") or os.getenv("SMTP_EMAIL")
        sender_pwd   = st.secrets.get("SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD")
        admin_email  = st.secrets.get("ADMIN_EMAIL") or os.getenv("ADMIN_EMAIL", "mlbbobble@gmail.com")
        
        if not sender_email or not sender_pwd or not admin_email:
            print("未設定 SMTP，跳過寄信通知")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = admin_email
        msg['Subject'] = f"[VN Portfolio] 新用戶等待開通審核：{new_user_email}"

        body = f"""
        您好，管理員：

        有一位新用戶剛剛登入/註冊了 VN Portfolio，目前正在等待您的開通。
        新用戶 Email：{new_user_email}

        請登入系統前往「管理員後台」為該用戶開啟權限。

        此為系統自動發送的通知信件，請勿回覆。
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 預設使用 Gmail SMTP Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_pwd)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"發送通知信失敗: {e}")
        return False
