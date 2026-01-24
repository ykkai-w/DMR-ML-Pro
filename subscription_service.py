# -*- coding: utf-8 -*-
"""
DMR-ML Pro 订阅服务模块
======================
处理邮箱订阅、存储和邮件发送功能
支持两种存储后端：本地JSON（开发用）和 Google Sheets（生产用）

Author: ykai-w
Version: 1.0-内测版
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================
# 存储配置
# ============================================================

# 订阅数据存储路径（本地JSON模式）
SUBSCRIPTION_FILE = os.path.join(os.path.dirname(__file__), 'subscribers.json')

def _get_storage_backend():
    """
    获取存储后端配置
    优先级：Streamlit Secrets > 环境变量 > 默认(json)
    
    Returns:
        'supabase' 或 'json'
    """
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            # 检查是否配置了 Supabase
            if 'supabase' in st.secrets:
                return 'supabase'
    except:
        pass
    
    # 检查环境变量
    if os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_KEY'):
        return 'supabase'
    
    return 'json'

# 当前使用的存储后端
STORAGE_BACKEND = _get_storage_backend()

# 尝试从 Streamlit Secrets 或环境变量获取邮箱密码
def _get_email_password():
    """获取邮箱授权码，支持 Streamlit Secrets 和环境变量"""
    # 内测版：可以直接硬编码（生产环境请删除此行）
    HARDCODED_PASSWORD = "avcminvzfhmtfafi"  # 内测专用，生产环境改为 None
    
    if HARDCODED_PASSWORD:
        return HARDCODED_PASSWORD
    
    # 优先级：Streamlit Secrets > 环境变量
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'EMAIL_PASSWORD' in st.secrets:
            return st.secrets['EMAIL_PASSWORD']
    except:
        pass
    return os.environ.get('EMAIL_PASSWORD', '')

# 邮件配置（使用SMTP，兼容多种邮件服务）
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',  # QQ邮箱SMTP
    'smtp_port': 465,  # 使用SSL端口
    'sender_email': '2103318492@qq.com',  # 您的QQ邮箱
    'sender_password': _get_email_password(),  # QQ邮箱授权码
}


# ============================================================
# 数据模型
# ============================================================

@dataclass
class Subscriber:
    """订阅者数据模型"""
    email: str
    subscribe_time: str
    push_time: str = "08:00"
    is_active: bool = True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Subscriber':
        # 兼容数据库返回的多余字段（如 id / created_at）
        filtered = {
            'email': data.get('email', ''),
            'subscribe_time': data.get('subscribe_time', ''),
            'push_time': data.get('push_time', '08:00'),
            'is_active': data.get('is_active', True),
        }
        return cls(**filtered)


# ============================================================
# Supabase 存储后端
# ============================================================

class SupabaseManager:
    """Supabase 数据库管理器"""
    
    def __init__(self):
        self.client = None
        self.table_name = 'subscribers'
        self._connect()
    
    def _connect(self):
        """建立 Supabase 连接"""
        try:
            from supabase import create_client, Client
        except ImportError:
            raise ImportError("请安装 supabase: pip install supabase")
        
        # 获取配置
        url, key = self._get_credentials()
        if not url or not key:
            raise ValueError("未找到 Supabase 配置，请在 Streamlit Secrets 中配置")
        
        self.client: Client = create_client(url, key)
        
        # 确保表存在（首次运行时创建）
        try:
            self.client.table(self.table_name).select("*").limit(1).execute()
        except Exception as e:
            print(f"Supabase 表可能不存在，需要手动创建: {e}")
    
    def _get_credentials(self) -> tuple:
        """从 Streamlit Secrets 或环境变量获取 Supabase 配置"""
        url, key = None, None
        
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                url = st.secrets['supabase'].get('url')
                key = st.secrets['supabase'].get('key')
        except:
            pass
        
        # 环境变量回退
        if not url:
            url = os.environ.get('SUPABASE_URL')
        if not key:
            key = os.environ.get('SUPABASE_KEY')
        
        return url, key
    
    def load_subscribers(self) -> List[Dict]:
        """从 Supabase 加载所有订阅者"""
        try:
            response = self.client.table(self.table_name).select("*").execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"从 Supabase 加载数据失败: {e}")
            return []
    
    def save_subscriber(self, subscriber: Dict):
        """添加新订阅者到 Supabase"""
        try:
            self.client.table(self.table_name).insert(subscriber).execute()
        except Exception as e:
            print(f"保存订阅者失败: {e}")
            raise
    
    def update_subscriber(self, email: str, data: Dict):
        """更新订阅者信息"""
        try:
            self.client.table(self.table_name).update(data).eq('email', email.lower()).execute()
        except Exception as e:
            print(f"更新订阅者失败: {e}")
    
    def delete_subscriber(self, email: str) -> bool:
        """从 Supabase 删除订阅者（软删除：设置 is_active=False）"""
        try:
            self.client.table(self.table_name).update({'is_active': False}).eq('email', email.lower()).execute()
            return True
        except Exception as e:
            print(f"删除订阅者失败: {e}")
            return False
    
    def find_subscriber(self, email: str) -> Optional[Dict]:
        """查找订阅者"""
        try:
            response = self.client.table(self.table_name).select("*").eq('email', email.lower()).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            print(f"查找订阅者失败: {e}")
        return None


# ============================================================
# 订阅管理（统一接口）
# ============================================================

class SubscriptionManager:
    """
    订阅管理器 - 统一接口
    根据配置自动选择存储后端（本地JSON或Supabase）
    """
    
    def __init__(self, file_path: str = SUBSCRIPTION_FILE, force_backend: str = None):
        """
        初始化订阅管理器
        
        Args:
            file_path: 本地JSON文件路径（仅json模式使用）
            force_backend: 强制使用的后端，'json' 或 'supabase'，不指定则自动检测
        """
        self.file_path = file_path
        self.backend = force_backend or STORAGE_BACKEND
        self.supabase_manager = None
        
        if self.backend == 'supabase':
            try:
                self.supabase_manager = SupabaseManager()
            except Exception as e:
                print(f"Supabase 连接失败，回退到本地JSON: {e}")
                self.backend = 'json'
        
        if self.backend == 'json':
            self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保订阅文件存在（仅JSON模式）"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def _load_subscribers(self) -> List[Dict]:
        """加载所有订阅者"""
        if self.backend == 'supabase' and self.supabase_manager:
            return self.supabase_manager.load_subscribers()
        else:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
    
    def _save_subscribers(self, subscribers: List[Dict]):
        """保存订阅者列表（仅JSON模式使用）"""
        if self.backend == 'json':
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(subscribers, f, ensure_ascii=False, indent=2)
    
    def add_subscriber(self, email: str, push_time: str = "08:00") -> tuple[bool, str]:
        """
        添加订阅者
        
        Returns:
            (成功标志, 消息)
        """
        # 验证邮箱格式
        if not self._validate_email(email):
            return False, "邮箱格式不正确，请检查后重试"
        
        email_lower = email.lower()
        
        if self.backend == 'supabase' and self.supabase_manager:
            # Supabase 模式
            existing = self.supabase_manager.find_subscriber(email_lower)
            if existing:
                if existing.get('is_active', True):
                    return False, "该邮箱已订阅，无需重复订阅"
                else:
                    # 重新激活
                    existing['is_active'] = True
                    existing['push_time'] = push_time
                    self.supabase_manager.update_subscriber(email_lower, existing)
                    return True, "欢迎回来！已重新激活您的订阅"
            
            # 添加新订阅者
            new_subscriber = {
                'email': email_lower,
                'subscribe_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'push_time': push_time,
                'is_active': True
            }
            self.supabase_manager.save_subscriber(new_subscriber)
            return True, "🎉 订阅成功！每日信号将准时送达您的邮箱"
        
        else:
            # JSON 模式
            subscribers = self._load_subscribers()
            
            # 检查是否已订阅
            for sub in subscribers:
                if sub['email'].lower() == email_lower:
                    if sub['is_active']:
                        return False, "该邮箱已订阅，无需重复订阅"
                    else:
                        # 重新激活
                        sub['is_active'] = True
                        sub['push_time'] = push_time
                        self._save_subscribers(subscribers)
                        return True, "欢迎回来！已重新激活您的订阅"
            
            # 添加新订阅者
            new_subscriber = Subscriber(
                email=email_lower,
                subscribe_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                push_time=push_time,
                is_active=True
            )
            subscribers.append(new_subscriber.to_dict())
            self._save_subscribers(subscribers)
            
            return True, "🎉 订阅成功！每日信号将准时送达您的邮箱"
    
    def remove_subscriber(self, email: str) -> tuple[bool, str]:
        """取消订阅"""
        email_lower = email.lower()
        
        if self.backend == 'supabase' and self.supabase_manager:
            if self.supabase_manager.delete_subscriber(email_lower):
                return True, "已取消订阅"
            return False, "未找到该邮箱的订阅记录"
        else:
            subscribers = self._load_subscribers()
            
            for sub in subscribers:
                if sub['email'].lower() == email_lower:
                    sub['is_active'] = False
                    self._save_subscribers(subscribers)
                    return True, "已取消订阅"
            
            return False, "未找到该邮箱的订阅记录"
    
    def get_active_subscribers(self) -> List[Subscriber]:
        """获取所有活跃订阅者"""
        subscribers = self._load_subscribers()
        return [Subscriber.from_dict(s) for s in subscribers if s.get('is_active', True)]
    
    def get_subscriber_count(self) -> int:
        """获取订阅者数量"""
        return len(self.get_active_subscribers())
    
    def get_storage_info(self) -> str:
        """获取当前存储后端信息（用于管理后台显示）"""
        if self.backend == 'supabase':
            return "Supabase 云数据库"
        else:
            return f"本地文件 ({self.file_path})"
    
    @staticmethod
    def _validate_email(email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


# ============================================================
# 邮件发送
# ============================================================

class EmailSender:
    """邮件发送器"""
    
    def __init__(self, config: dict = None):
        self.config = config or EMAIL_CONFIG
    
    def send_signal_email(self, to_email: str, signal_data: dict) -> tuple[bool, str]:
        """
        发送每日信号邮件
        
        Args:
            to_email: 收件人邮箱
            signal_data: 信号数据，包含:
                - date: 日期
                - signal: 信号（沪深300/中证1000/空仓）
                - ml_risk: ML风险概率
                - reason: 信号原因
        """
        try:
            # 构建邮件内容
            # 🧪 测试模式：临时修改邮件标题
            subject = f"🧪【DMR-ML Pro 测试】{signal_data['date']} 临时测试邮件（请忽略信号）"
            
            html_content = self._build_email_html(signal_data)
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config['sender_email']
            msg['To'] = to_email
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 发送邮件 - QQ邮箱使用SSL
            with smtplib.SMTP_SSL(self.config['smtp_server'], 465) as server:
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            
            return True, "邮件发送成功"
            
        except Exception as e:
            return False, f"邮件发送失败: {str(e)}"
    
    def send_welcome_email(self, to_email: str, push_time: str = "08:00") -> tuple[bool, str]:
        """
        发送订阅确认邮件
        
        Args:
            to_email: 收件人邮箱
            push_time: 推送时间
        """
        try:
            # 检查密码是否配置
            if not self.config['sender_password']:
                return False, "邮件配置错误：EMAIL_PASSWORD 未设置"
            
            subject = "【DMR-ML Pro】订阅成功！感谢支持，欢迎加入🛫"
            html_content = self._build_welcome_email_html(push_time)
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config['sender_email']
            msg['To'] = to_email
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP_SSL(self.config['smtp_server'], 465, timeout=30) as server:
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            
            return True, "欢迎邮件发送成功"
            
        except smtplib.SMTPAuthenticationError:
            return False, "邮件发送失败：授权码错误或SMTP服务未开启"
        except smtplib.SMTPConnectError:
            return False, "邮件发送失败：无法连接邮件服务器（可能被网络限制）"
        except TimeoutError:
            return False, "邮件发送失败：连接超时（Streamlit Cloud可能限制了SMTP连接）"
        except Exception as e:
            return False, f"邮件发送失败: {type(e).__name__}: {str(e)}"
    
    def _build_email_html(self, signal_data: dict) -> str:
        """构建邮件HTML内容"""
        
        # 信号颜色
        signal = signal_data.get('signal', '空仓')
        if signal == '沪深300':
            signal_color = '#3498db'
            signal_desc = '大盘风格，建议配置沪深300指数'
        elif signal == '中证1000':
            signal_color = '#e74c3c'
            signal_desc = '小盘风格，建议配置中证1000指数'
        else:
            signal_color = '#95a5a6'
            signal_desc = 'ML风险预警，建议空仓观望'
        
        # ML风险状态
        ml_risk = signal_data.get('ml_risk', 0)
        risk_status = '⚠️ 避险模式' if ml_risk > 0.40 else '✅ 正常交易'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #f5f5f5;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    color: #FF6B6B;
                }}
                .header p {{
                    margin: 10px 0 0;
                    opacity: 0.8;
                    font-size: 14px;
                }}
                .signal-box {{
                    text-align: center;
                    padding: 40px 20px;
                    background: linear-gradient(135deg, #1e2530 0%, #252d3a 100%);
                }}
                .signal-label {{
                    color: #999;
                    font-size: 14px;
                    margin-bottom: 10px;
                }}
                .signal-value {{
                    font-size: 48px;
                    font-weight: 800;
                    color: {signal_color};
                    text-shadow: 0 0 20px rgba(255,107,107,0.3);
                }}
                .signal-desc {{
                    color: #ccc;
                    margin-top: 15px;
                    font-size: 14px;
                }}
                .info-section {{
                    padding: 25px 30px;
                }}
                .info-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 12px 0;
                    border-bottom: 1px solid #eee;
                }}
                .info-item:last-child {{
                    border-bottom: none;
                }}
                .info-label {{
                    color: #666;
                }}
                .info-value {{
                    font-weight: 600;
                    color: #333;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px 30px;
                    text-align: center;
                    color: #999;
                    font-size: 12px;
                }}
                .footer a {{
                    color: #FF6B6B;
                    text-decoration: none;
                }}
                .risk-badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    background: {'#fff3cd' if ml_risk > 0.40 else '#d4edda'};
                    color: {'#856404' if ml_risk > 0.40 else '#155724'};
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📡 DMR-ML Pro</h1>
                    <p>基于机器学习的双重动量轮动策略</p>
                </div>
                
                <div class="signal-box">
                    <div class="signal-label">📅 {signal_data.get('date', '')} 操作信号</div>
                    <div class="signal-value">{signal}</div>
                    <div class="signal-desc">💡 {signal_desc}</div>
                </div>
                
                <div class="info-section">
                    <div class="info-item">
                        <span class="info-label">🛡️ ML风险概率</span>
                        <span class="info-value">{ml_risk:.1%}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">📊 风险状态</span>
                        <span class="risk-badge">{risk_status}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">💡 信号原因</span>
                        <span class="info-value">{signal_data.get('reason', '-')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">⏰ 执行时点</span>
                        <span class="info-value">下一交易日开盘</span>
                    </div>
                </div>
                
                <div class="footer">
                    <p>⚠️ 风险提示：本策略基于历史数据回测，过往业绩不代表未来表现。投资有风险，决策需谨慎。</p>
                    <p>DMR-ML Pro v1.0-内测版 | © 2026 ykai-w</p>
                    <p>如需取消订阅，请回复邮件告知</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_welcome_email_html(self, push_time: str = "08:00") -> str:
        """构建订阅确认邮件HTML - 使用table布局确保兼容性"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f7fa; font-family: Arial, sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f5f7fa" style="background-color: #f5f7fa; padding: 20px 0;">
                <tr>
                    <td align="center">
                        <!-- 主容器 -->
                        <table width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            
                            <!-- 头部 -->
                            <tr>
                                <td bgcolor="#FF6B6B" style="background-color: #FF6B6B; padding: 40px 30px; text-align: center;">
                                    <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">🎉 欢迎加入 DMR-ML Pro</h1>
                                    <p style="margin: 10px 0 0; color: #ffffff; font-size: 14px;">基于机器学习的双重动量轮动策略</p>
                                </td>
                            </tr>
                            
                            <!-- 成功提示 -->
                            <tr>
                                <td bgcolor="#f8f9fa" style="background-color: #f8f9fa; padding: 40px 30px; text-align: center;">
                                    <div style="font-size: 64px; line-height: 1;">✅</div>
                                    <h2 style="margin: 20px 0 10px; color: #1a1a1a; font-size: 24px; font-weight: 600;">订阅成功！</h2>
                                    <p style="margin: 10px 0; color: #4a4a4a; font-size: 15px; line-height: 1.6;">恭喜您成为 DMR-ML Pro 的内测用户</p>
                                    <p style="margin: 10px 0; color: #4a4a4a; font-size: 15px; line-height: 1.6;">
                                        每个交易日早上 <strong style="color: #FF6B6B;">{push_time}</strong>，您将收到今日操作信号
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- 功能介绍 -->
                            <tr>
                                <td style="padding: 30px;">
                                    <h3 style="text-align: center; color: #1a1a1a; font-size: 18px; margin: 0 0 20px; font-weight: 600;">📊 您将获得</h3>
                                    
                                    <!-- 功能列表 -->
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td style="padding: 15px 0; border-bottom: 1px solid #e8e8e8;">
                                                <div style="font-weight: 600; color: #1a1a1a; font-size: 15px; margin-bottom: 5px;">📡 每日操作信号</div>
                                                <div style="color: #666666; font-size: 13px;">沪深300/中证1000/空仓，清晰明确的投资建议</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 15px 0; border-bottom: 1px solid #e8e8e8;">
                                                <div style="font-weight: 600; color: #1a1a1a; font-size: 15px; margin-bottom: 5px;">🛡️ ML风险预警</div>
                                                <div style="color: #666666; font-size: 13px;">机器学习模型实时监控市场风险，提前规避下跌</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 15px 0; border-bottom: 1px solid #e8e8e8;">
                                                <div style="font-weight: 600; color: #1a1a1a; font-size: 15px; margin-bottom: 5px;">💡 信号解读</div>
                                                <div style="color: #666666; font-size: 13px;">详细的信号原因说明，让您知其然更知其所以然</div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 15px 0;">
                                                <div style="font-weight: 600; color: #1a1a1a; font-size: 15px; margin-bottom: 5px;">📈 历史验证</div>
                                                <div style="color: #666666; font-size: 13px;">2019年1月-2026年1月累计收益207.9%，复利年化17.3%，最大回撤仅-12.7%</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- 风险提示 -->
                            <tr>
                                <td style="padding: 0 30px 20px;">
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#fff3cd" style="background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                                        <tr>
                                            <td style="padding: 15px 20px;">
                                                <strong style="color: #856404; font-size: 14px;">⚠️ 重要提示</strong><br>
                                                <span style="color: #856404; font-size: 13px;">本策略基于历史数据回测，过往业绩不代表未来表现。投资有风险，决策需谨慎。</span>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- 访问按钮 -->
                            <tr>
                                <td bgcolor="#f8f9fa" style="background-color: #f8f9fa; padding: 30px; text-align: center;">
                                    <p style="margin: 0 0 15px; color: #666666; font-size: 14px;">访问系统了解更多详情</p>
                                    <table cellpadding="0" cellspacing="0" border="0" align="center">
                                        <tr>
                                            <td bgcolor="#FF6B6B" style="border-radius: 25px;">
                                                <a href="https://dmr-ml-pro-8odufgfuzjtivdppmnwrvh.streamlit.app/"
                                                   style="display: inline-block; padding: 12px 30px; background-color: #FF6B6B; color: #ffffff; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 14px;">
                                                    立即访问系统
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- 页脚 -->
                            <tr>
                                <td bgcolor="#2c3e50" style="background-color: #2c3e50; padding: 25px 30px; text-align: center;">
                                    <p style="margin: 0 0 8px; color: #95a5a6; font-size: 12px;">如有任何问题，请回复本邮件或联系 ykai.w@outlook.com</p>
                                    <p style="margin: 0 0 8px; color: #95a5a6; font-size: 12px;">如需取消订阅，请回复邮件告知</p>
                                    <p style="margin: 0; color: #95a5a6; font-size: 12px;">DMR-ML Pro v1.0-内测版 | © 2026 ykai-w</p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        return html
    
    def send_batch_emails(self, subscribers: List[Subscriber], signal_data: dict) -> dict:
        """
        批量发送邮件
        
        Returns:
            {'success': 成功数, 'failed': 失败数, 'errors': 错误列表}
        """
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for sub in subscribers:
            success, msg = self.send_signal_email(sub.email, signal_data)
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"{sub.email}: {msg}")
        
        return results


# ============================================================
# 便捷函数
# ============================================================

def subscribe_email(email: str, push_time: str = "08:00") -> tuple[bool, str]:
    """订阅邮件服务"""
    manager = SubscriptionManager()
    return manager.add_subscriber(email, push_time)


def unsubscribe_email(email: str) -> tuple[bool, str]:
    """取消订阅"""
    manager = SubscriptionManager()
    return manager.remove_subscriber(email)


def get_subscriber_count() -> int:
    """获取订阅者数量"""
    manager = SubscriptionManager()
    return manager.get_subscriber_count()


def send_daily_signals(signal_data: dict) -> dict:
    """发送每日信号给所有订阅者"""
    manager = SubscriptionManager()
    sender = EmailSender()
    subscribers = manager.get_active_subscribers()
    return sender.send_batch_emails(subscribers, signal_data)


def load_subscribers() -> List[Subscriber]:
    """加载所有订阅者（用于管理员后台）"""
    manager = SubscriptionManager()
    return manager.get_active_subscribers()


def delete_subscriber(email: str) -> tuple[bool, str]:
    """删除订阅者（管理员功能）"""
    return unsubscribe_email(email)


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    # 测试订阅
    success, msg = subscribe_email("test@example.com")
    print(f"订阅结果: {msg}")
    
    # 查看订阅者数量
    count = get_subscriber_count()
    print(f"当前订阅者数量: {count}")
