#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件功能测试脚本
快速测试订阅和邮件发送是否正常
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subscription_service import subscribe_email, EmailSender

def test_subscription():
    """测试订阅功能"""
    print("=" * 50)
    print("📧 测试订阅功能")
    print("=" * 50)
    
    # 测试邮箱
    test_email = input("请输入您的测试邮箱（用于接收测试邮件）: ").strip()
    
    if not test_email:
        print("❌ 请输入有效邮箱")
        return False
    
    # 订阅
    success, msg = subscribe_email(test_email, "08:00")
    print(f"\n{'✅' if success else '❌'} {msg}")
    
    return success and test_email

def test_email_sending(to_email):
    """测试邮件发送"""
    print("\n" + "=" * 50)
    print("📬 测试邮件发送")
    print("=" * 50)
    
    # 模拟信号数据
    test_signal = {
        'date': '2026-01-23',
        'signal': '中证1000',
        'ml_risk': 0.343,
        'reason': '小盘多头，大盘走弱'
    }
    
    print(f"\n📡 准备发送测试邮件到: {to_email}")
    print(f"   信号: {test_signal['signal']}")
    print(f"   ML风险: {test_signal['ml_risk']:.1%}")
    
    # 配置邮件密码
    email_password = input("\n请输入QQ邮箱授权码（16位）: ").strip()
    
    if not email_password:
        print("❌ 请输入QQ邮箱授权码")
        print("💡 提示：在QQ邮箱设置中获取的16位授权码")
        return False
    
    # 临时设置环境变量
    os.environ['EMAIL_PASSWORD'] = email_password
    
    # 发送邮件
    sender = EmailSender()
    success, msg = sender.send_signal_email(to_email, test_signal)
    
    print(f"\n{'✅' if success else '❌'} {msg}")
    
    if success:
        print("\n🎉 测试成功！请检查您的邮箱")
        print(f"   如果没收到，请检查垃圾邮件文件夹")
    else:
        print(f"\n❌ 发送失败：{msg}")
        print("\n💡 可能的原因：")
        print("   1. Outlook应用密码输入错误")
        print("   2. 邮箱地址不正确")
        print("   3. 网络连接问题")
    
    return success

def main():
    """主函数"""
    print("\n" + "🎯" * 20)
    print("DMR-ML Pro 邮件功能测试")
    print("🎯" * 20 + "\n")
    
    # 测试订阅
    test_email = test_subscription()
    
    if not test_email:
        return
    
    # 询问是否继续测试发送
    continue_test = input("\n是否继续测试邮件发送？(y/n): ").strip().lower()
    
    if continue_test == 'y':
        test_email_sending(test_email)
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️ 测试已取消")
    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
