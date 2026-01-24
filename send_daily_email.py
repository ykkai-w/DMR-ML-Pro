#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMR-ML Pro 每日邮件发送脚本
============================
每日定时执行，向所有订阅者发送今日操作信号

使用方法：
1. 本地执行：python send_daily_email.py
2. GitHub Actions：见 .github/workflows/daily_signal.yml
3. 本地crontab：0 8 * * 1-5 cd /path/to/DMR_Pro_System && python send_daily_email.py

Author: ykai-w
Version: 1.0-内测版
"""

import os
import sys
from datetime import datetime

# 加载环境变量（本地开发时使用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 生产环境可能没有 python-dotenv

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from data_service import get_data_service
from models import DMRStrategy, MLRiskModel, DMRMLStrategy
from reports import SignalGenerator
from subscription_service import SubscriptionManager, EmailSender, get_subscriber_count


def generate_today_signal() -> dict:
    """生成今日信号"""
    print("📡 正在生成今日信号...")
    
    config = get_config()
    data_service = get_data_service()
    
    # 获取数据
    csi300 = data_service.get_csi300()
    csi1000 = data_service.get_csi1000()
    
    if csi300 is None or csi1000 is None or csi300.empty or csi1000.empty:
        raise Exception("获取数据失败")
    
    # 初始化并运行DMR-ML策略
    strategy = DMRMLStrategy(
        momentum_window=config.strategy.default_momentum_window,
        ma_window=config.strategy.default_ma_window
    )
    
    # 训练并预测
    strategy.train(csi300, csi1000)
    ml_probs = strategy.predict(csi300, csi1000)
    
    # 生成今日信号
    signal_gen = SignalGenerator(
        csi300, csi1000, ml_probs,
        config.strategy.default_momentum_window,
        config.strategy.default_ma_window
    )
    signal = signal_gen.generate_signal()
    
    return signal


def send_emails_to_subscribers(signal: dict) -> dict:
    """向所有订阅者发送邮件"""
    
    # 构建邮件数据
    signal_data = {
        'date': signal['data_date'],
        'signal': signal['final_signal'],
        'ml_risk': signal['ml_risk']['probability'],
        'reason': signal['final_reason'],
    }
    
    # 获取订阅者
    manager = SubscriptionManager()
    subscribers = manager.get_active_subscribers()
    
    if not subscribers:
        print("📭 暂无订阅者")
        return {'success': 0, 'failed': 0, 'errors': []}
    
    print(f"📬 准备向 {len(subscribers)} 位订阅者发送邮件...")
    
    # 发送邮件
    sender = EmailSender()
    results = sender.send_batch_emails(subscribers, signal_data)
    
    return results


def main():
    """主函数"""
    print("=" * 50)
    print("🚀 DMR-ML Pro 每日信号邮件服务")
    print(f"📅 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查是否是交易日（周一到周五）
    # 🧪 测试模式：临时注释非交易日判断
    # today = datetime.now()
    # if today.weekday() >= 5:  # 周六=5, 周日=6
    #     print("⏸️ 今日为非交易日，跳过发送")
    #     return
    
    try:
        # 1. 生成今日信号
        signal = generate_today_signal()
        print(f"✅ 今日信号：{signal['final_signal']}")
        print(f"   ML风险概率：{signal['ml_risk']['probability']:.1%}")
        print(f"   信号原因：{signal['reason']}")
        
        # 2. 检查订阅者数量
        count = get_subscriber_count()
        if count == 0:
            print("📭 暂无订阅者，跳过发送")
            return
        
        # 3. 发送邮件
        results = send_emails_to_subscribers(signal)
        
        # 4. 输出结果
        print("-" * 50)
        print(f"📊 发送结果：")
        print(f"   ✅ 成功：{results['success']} 封")
        print(f"   ❌ 失败：{results['failed']} 封")
        
        if results['errors']:
            print("   错误详情：")
            for err in results['errors']:
                print(f"      - {err}")
        
        print("=" * 50)
        print("🎉 每日信号邮件发送完成！")
        
    except Exception as e:
        print(f"❌ 发送失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
