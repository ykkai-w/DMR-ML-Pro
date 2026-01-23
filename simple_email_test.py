#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级简单的邮件测试脚本
只测试SMTP连接和发送
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# QQ邮箱配置
SENDER_EMAIL = "2103318492@qq.com"
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465

def send_test_email(password, to_email):
    """发送测试邮件"""
    try:
        print(f"\n📡 开始测试...")
        print(f"   发件人: {SENDER_EMAIL}")
        print(f"   收件人: {to_email}")
        print(f"   SMTP服务器: {SMTP_SERVER}:{SMTP_PORT}")
        
        # 创建简单邮件
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "DMR-ML Pro 测试邮件"
        
        body = """
        <h1>🎉 测试成功！</h1>
        <p>如果您收到这封邮件，说明邮件发送功能正常！</p>
        <p>DMR-ML Pro 邮件服务已就绪。</p>
        """
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # 连接并发送
        print("\n🔌 正在连接SMTP服务器...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        
        print("🔐 正在登录...")
        server.login(SENDER_EMAIL, password)
        
        print("📬 正在发送邮件...")
        server.send_message(msg)
        
        print("✅ 关闭连接...")
        server.quit()
        
        print("\n" + "="*50)
        print("🎉 邮件发送成功！")
        print("请检查邮箱（包括垃圾邮件文件夹）")
        print("="*50)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ 认证失败：{e}")
        print("💡 请检查：")
        print("   1. 授权码是否正确（16位字符）")
        print("   2. QQ邮箱SMTP服务是否已开启")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ 连接失败：{e}")
        print("💡 请检查网络连接")
        return False
    except Exception as e:
        print(f"\n❌ 发送失败：{e}")
        print(f"   错误类型：{type(e).__name__}")
        return False

def main():
    print("="*60)
    print("    DMR-ML Pro 超级简单邮件测试")
    print("="*60)
    
    # 输入信息
    to_email = input("\n📮 收件人邮箱: ").strip()
    if not to_email:
        to_email = SENDER_EMAIL
        print(f"   使用默认邮箱: {to_email}")
    
    password = input("\n🔑 QQ邮箱授权码（16位）: ").strip()
    if not password:
        print("❌ 授权码不能为空！")
        return
    
    if len(password) != 16:
        print(f"⚠️  警告：授权码通常是16位，您输入了{len(password)}位")
        confirm = input("   是否继续？(y/n): ")
        if confirm.lower() != 'y':
            return
    
    # 发送测试邮件
    send_test_email(password, to_email)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️ 测试已取消")
