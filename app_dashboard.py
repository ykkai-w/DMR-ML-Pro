"""
DMR Pro System - Streamlit 仪表盘
=====================================
专业级量化交易系统界面

Author: DMR Pro Team
"""

# 加载环境变量（本地开发时使用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 生产环境可能没有 python-dotenv

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# 设置页面配置（必须是第一个Streamlit命令）
st.set_page_config(
    page_title="DMR-ML Pro | 智能量化交易系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 导入系统模块
from config import get_config, SystemConfig
from data_service import DataService, get_data_service
from models import DMRStrategy, MLRiskModel, DMRMLStrategy
from backtest_engine import BacktestEngine, BacktestResult
from reports import ReportGenerator, MetricsCalculator, TradeAnalyzer, SignalGenerator
from visualization import DashboardCharts, ChartTheme
from utils import get_trading_status, format_percent, format_number, get_risk_color


# ============================================================
# 自定义CSS样式
# ============================================================

def inject_custom_css():
    """注入自定义CSS样式"""
    st.markdown("""
    <style>
    /* 整体主题 - 深色 */
    .stApp {
        background: linear-gradient(135deg, #0E1117 0%, #1a1f2e 50%, #0E1117 100%);
    }
    
    /* 侧边栏样式 - 深色 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #151922 0%, #1a1f2e 100%);
        border-right: 1px solid #2d3748;
    }
    
    /* 标题样式 */
    .main-title {
        font-family: 'Inter', -apple-system, sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #C7302A 0%, #FF6B6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #CCCCCC;
        margin-bottom: 2rem;
    }
    
    /* 指标卡片 - 深色 */
    .metric-card {
        background: linear-gradient(145deg, #1e2530 0%, #252d3a 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #CCCCCC;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FAFAFA;
    }
    
    .metric-delta {
        font-size: 0.9rem;
        margin-top: 0.3rem;
    }
    
    .delta-positive { color: #FF6B6B; }  /* 红色代表赚钱（A股风格） */
    .delta-negative { color: #66BB6A; }  /* 绿色代表亏钱（A股风格） */
    
    /* 信号卡片 - 深色 */
    .signal-card {
        background: linear-gradient(145deg, #1e2530 0%, #252d3a 100%);
        border: 2px solid #C7302A;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
    }
    
    .signal-label {
        font-size: 1rem;
        color: #CCCCCC;
        margin-bottom: 1rem;
    }
    
    .signal-value {
        font-size: 3rem;
        font-weight: 800;
        color: #FF6B6B;
        text-shadow: 0 0 20px rgba(255,107,107,0.4);
    }
    
    .signal-reason {
        font-size: 0.9rem;
        color: #E0E0E0;
        margin-top: 1rem;
        padding: 0.8rem;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
    }
    
    /* 状态指示器 */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-trading {
        background: rgba(67, 160, 71, 0.2);
        color: #66BB6A;
        border: 1px solid #43A047;
    }
    
    .status-closed {
        background: rgba(155, 155, 155, 0.2);
        color: #CCCCCC;
        border: 1px solid #9B9B9B;
    }
    
    .status-risk {
        background: rgba(211, 47, 47, 0.2);
        color: #EF5350;
        border: 1px solid #D32F2F;
    }
    
    /* 分隔线 - 深色 */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #2d3748 50%, transparent 100%);
        margin: 2rem 0;
    }
    
    /* 隐藏默认样式 */
    .stMetric {
        background: transparent;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #C7302A 0%, #a02520 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #d63830 0%, #C7302A 100%);
        box-shadow: 0 4px 15px rgba(199,48,42,0.4);
    }
    
    /* 进度条 */
    .stProgress > div > div {
        background: linear-gradient(90deg, #C7302A 0%, #FF6B6B 100%);
    }
    
    /* ============================================
       一级选项卡（主导航）
       ============================================ */
    .stTabs[data-baseweb="tabs"] > div > [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs[data-baseweb="tabs"] > div > [data-baseweb="tab-list"] > [data-baseweb="tab"] {
        background: #1e2530;
        border-radius: 8px 8px 0 0;
        color: #FFFFFF !important;
        border: 1px solid #2d3748;
        border-bottom: none;
        padding: 0.8rem 1.5rem;
        font-size: 1rem;
    }
    
    .stTabs[data-baseweb="tabs"] > div > [data-baseweb="tab-list"] > [aria-selected="true"] {
        background: #252d3a;
        color: #FFFFFF !important;
        border-color: #C7302A;
    }
    
    /* ============================================
       二级选项卡（按钮组风格）
       ============================================ */
    .stTabs .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: transparent;
        border-bottom: none;
        padding: 0.5rem 0;
    }
    
    .stTabs .stTabs [data-baseweb="tab"] {
        background: rgba(30, 37, 48, 0.6);
        border-radius: 8px;
        border: 1.5px solid #3a4556;
        color: #FFFFFF !important;
        padding: 0.5rem 1.2rem;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        border-bottom: 1.5px solid #3a4556;
    }
    
    .stTabs .stTabs [data-baseweb="tab"]:hover {
        background: rgba(30, 37, 48, 0.9);
        border-color: #5A6A7A;
        color: #FFFFFF !important;
    }
    
    .stTabs .stTabs [aria-selected="true"] {
        background: rgba(199, 48, 42, 0.2);
        border: 1.5px solid #FF6B6B;
        color: #FFFFFF !important;
        font-weight: 600;
        box-shadow: 0 0 15px rgba(199, 48, 42, 0.4);
    }
    
    /* ============================================
       全局文字颜色强制白色
       ============================================ */
    
    /* Markdown文字全白 */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown h1, .stMarkdown h2, 
    .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #FFFFFF !important;
    }
    
    /* 表格文字白色 */
    .stTable, table, th, td {
        color: #FFFFFF !important;
    }
    
    /* 侧边栏文字全白 */
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* 滑块标签和数值白色 */
    .stSlider label, .stSlider span {
        color: #FFFFFF !important;
    }
    
    /* 复选框标签白色 */
    .stCheckbox label span {
        color: #FFFFFF !important;
    }
    
    /* 选择框文字白色 */
    .stSelectbox label, .stSelectbox span {
        color: #FFFFFF !important;
    }
    
    /* Metric组件文字白色 */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] {
        color: #FFFFFF !important;
    }
    
    /* Info/Warning/Error框内文字 */
    .stAlert p, .stAlert span {
        color: #FFFFFF !important;
    }
    
    /* 数据表格 */
    .stDataFrame, [data-testid="stDataFrame"] * {
        color: #FFFFFF !important;
    }
    
    /* 标题强制白色 */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    /* 链接颜色 */
    a {
        color: #64B5F6 !important;
    }
    
    /* 加粗文字 */
    strong, b {
        color: #FFFFFF !important;
    }
    
    /* Spinner文字 */
    .stSpinner > div {
        color: #FFFFFF !important;
    }
    
    /* 隐藏Spinner的随机emoji */
    .stSpinner::before,
    .stSpinner [data-testid] img,
    .stSpinner span[style*="font-size"] {
        display: none !important;
    }
    
    /* Caption/小字 */
    .stCaption, small {
        color: #CCCCCC !important;
    }
    
    /* 订阅表单输入框 - 深色主题 */
    .stTextInput > div > div > input {
        background-color: #1e2530 !important;
        color: #FFFFFF !important;
        border: 2px solid #C7302A !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FF6B6B !important;
        box-shadow: 0 0 0 2px rgba(199,48,42,0.2) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #888888 !important;
    }
    
    /* 下拉选择框 - 深色主题 */
    .stSelectbox > div > div > div {
        background-color: #1e2530 !important;
        color: #FFFFFF !important;
        border: 2px solid #C7302A !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox > div > div > div:hover {
        border-color: #FF6B6B !important;
    }
    
    /* 下拉菜单选项 */
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #1e2530 !important;
        color: #FFFFFF !important;
    }
    
    /* 下拉菜单下拉列表 */
    [data-baseweb="popover"] {
        background-color: #1e2530 !important;
    }
    
    [data-baseweb="menu"] li {
        background-color: #1e2530 !important;
        color: #FFFFFF !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background-color: #2d3748 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# 组件函数
# ============================================================

def render_header():
    """渲染页面头部"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<h1 class="main-title" style="font-size: 3.2rem;">DMR-ML Pro</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title">基于机器学习的双重动量轮动策略 | Dual Momentum Rotation with Machine Learning</p>', unsafe_allow_html=True)
    
    with col2:
        status = get_trading_status()
        status_class = "status-trading" if status['is_trading'] else "status-closed"
        st.markdown(f"""
        <div style="text-align: right; padding-top: 1rem;">
            <span class="status-indicator {status_class}">
                {'🟢' if status['is_trading'] else '⚪'} {status['status']}
            </span>
            <div style="color: #CCCCCC; font-size: 0.8rem; margin-top: 0.5rem;">
                {status['datetime_str']} {status['weekday']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = None, delta_positive: bool = True):
    """渲染指标卡片"""
    delta_html = ""
    if delta:
        delta_class = "delta-positive" if delta_positive else "delta-negative"
        # 分离delta为标签和值（用|分隔）
        if "|" in delta:
            delta_label, delta_value = delta.split("|", 1)
            delta_html = f'<div style="font-size: 0.75rem; color: #999999; margin-top: 0.5rem;">{delta_label}</div><div class="metric-delta {delta_class}" style="font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem;">{delta_value}</div>'
        else:
            delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_signal_card(signal: str, reason: str, ml_prob: float = None):
    """渲染信号卡片"""
    # 不再在卡片内显示HTML代码，改用简洁方式
    st.markdown(f"""
    <div class="signal-card">
        <div class="signal-label">📡 今日策略信号</div>
        <div class="signal-value">{signal}</div>
        <div class="signal-reason">💡 {reason}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ML风险信息改用Streamlit原生组件显示
    if ml_prob is not None:
        risk_color = get_risk_color(ml_prob)
        risk_status = "⚠️ 避险" if ml_prob > 0.40 else "✅ 正常"
        st.info(f"**ML风险概率**: {ml_prob:.1%} | **状态**: {risk_status}")


def render_divider():
    """渲染分隔线"""
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ============================================================
# 缓存数据加载
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """加载市场数据（带缓存）"""
    data_service = get_data_service()
    df300, df1000 = data_service.get_aligned_data()
    return df300, df1000


@st.cache_data(ttl=3600, show_spinner=False)
def train_ml_model(_df300: pd.DataFrame):
    """训练ML模型（带缓存）"""
    ml_model = MLRiskModel()
    ml_probs = ml_model.fit_predict(_df300, verbose=False)
    return ml_probs


@st.cache_data(ttl=3600, show_spinner=False)
def run_strategy_backtest(
    _df300: pd.DataFrame, 
    _df1000: pd.DataFrame, 
    _ml_probs: pd.Series,
    momentum_window: int,
    ma_window: int,
):
    """运行策略回测（带缓存）"""
    engine = BacktestEngine()
    
    # DMR-ML 策略
    result_ml = engine.run_backtest(
        _df300, _df1000, momentum_window, ma_window,
        ml_probs=_ml_probs, strategy_name="DMR-ML"
    )
    
    # DMR 策略（对照）
    result_base = engine.run_backtest(
        _df300, _df1000, momentum_window, ma_window,
        ml_probs=None, strategy_name="DMR"
    )
    
    # 基准
    common_idx = _df300.index.intersection(_df1000.index)
    bench = _df300['close'].loc[common_idx]
    bench = bench / bench.iloc[0]
    
    return result_ml, result_base, bench


# ============================================================
# 侧边栏
# ============================================================

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### ⚙️ 策略参数")
        
        config = get_config()
        
        momentum_window = st.slider(
            "动量窗口（默认20）",
            min_value=10, max_value=40, value=20, step=5,
            help="计算动量的时间窗口（交易日）"
        )
        
        ma_window = st.slider(
            "均线窗口（默认14）",
            min_value=5, max_value=30, value=14, step=2,
            help="计算均线的时间窗口（交易日）"
        )
        
        st.markdown("---")
        st.markdown("### ⚖️ ML风险阈值")
        
        risk_trigger = st.slider(
            "触发阈值（默认40%）",
            min_value=30, max_value=60, value=40, step=5,
            format="%d%%",
            help="风险概率超过此值时触发避险"
        )
        
        risk_release = st.slider(
            "解除阈值（默认33%）",
            min_value=20, max_value=45, value=33, step=5,
            format="%d%%",
            help="风险概率低于此值时解除避险"
        )
        
        st.markdown("---")
        st.markdown("### 🖥️ 显示设置（仅策略概览）")
        
        show_dmr_comparison = st.checkbox("显示DMR策略对比", value=True)
        show_benchmark = st.checkbox("显示沪深300基准", value=True)
        log_scale = st.checkbox("对数坐标", value=True)
        st.caption('📌 上述选项仅影响"策略概览"的净值走势图')
        
        st.markdown("---")
        
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # 关于DMR-ML说明
        with st.expander("📖 关于 DMR-ML Pro"):
            st.markdown("""
            **策略架构**  
            DMR-ML = DMR（双重动量轮动）+ ML（机器学习门禁）
            
            **✨ ML模块优势**
            - 提升年化收益约 3-5%
            - 降低最大回撤约 6%
            - 优化夏普比率
            
            ---
            
            **🗂️ 回测说明**
            - 区间：2019年1月1日 至今
            - 为什么从2019年开始？
              - 2019年是A股牛熊转换的关键年份
              - 经历了完整的牛熊周期（2019牛市→2021-2022熊市→2024-2025反弹）
              - 样本量充足（6年+）且具有代表性
            
            ---
            
            **🔐 核心技术**
            - **Purged Walk-Forward**：防止标签泄露的滚动训练
            - **双阈值迟滞机制**：触发40%/解除33%，减少信号频繁切换
            - **随机森林模型**：100棵决策树，最大深度5，防止过拟合
            
            ---
            
            **📌 参数说明**  
            默认值已为基于2019年至今历史数据网格搜索得出的回测最优值。
            """)
        
        st.markdown("---")
        
        # 📬 内测用户专属福利 - 订阅服务
        with st.expander("📬 内测用户专属福利"):
            st.markdown("""
            **🎁 永久免费订阅每日信号邮件**
            
            作为内测用户，您将享受：
            - 每日A股开盘前准时收到操作信号
            - 今日操作信号 + ML风险概率
            - 市场风格判断 + 执行建议
            """)
            
            # 邮箱输入
            email_input = st.text_input(
                "📮 您的邮箱",
                placeholder="example@email.com",
                key="subscribe_email"
            )
            
            # 推送时间选择
            push_time = st.selectbox(
                "⏰ 推送时间（A股开盘前）",
                options=["07:30", "08:00", "08:30", "09:00"],
                index=1,  # 默认08:00
                key="push_time"
            )
            
            # 订阅按钮
            if st.button("✅ 立即订阅", key="subscribe_btn", use_container_width=True):
                if email_input:
                    try:
                        from subscription_service import subscribe_email, EmailSender
                        
                        # 添加订阅
                        success, msg = subscribe_email(email_input, push_time)
                        
                        if success:
                            st.success(msg)
                            st.balloons()
                            
                            # 立即发送确认邮件
                            with st.spinner("正在发送确认邮件..."):
                                try:
                                    sender = EmailSender()
                                    email_success, email_msg = sender.send_welcome_email(email_input, push_time)
                                    if email_success:
                                        st.info("📧 确认邮件已发送，请查收！")
                                    else:
                                        st.warning(f"⚠️ 订阅成功但确认邮件发送失败，您仍将正常收到每日信号")
                                except Exception as e:
                                    st.warning(f"⚠️ 订阅成功但确认邮件发送失败: {str(e)}")
                        else:
                            st.warning(msg)
                    except Exception as e:
                        st.error(f"订阅失败: {str(e)}")
                else:
                    st.warning("请输入邮箱地址")
            
            st.caption("🛫 订阅后每日A股开盘前收到：今日操作信号 + ML风险概率 + 市场风格判断")
        
        # 👨‍💻 关于开发者
        with st.expander("👨‍💻 关于开发者"):
            st.markdown("""
            **🎓 ykai-w 团队**（目前为个人运营）
            
            **Kai** · CAU 金融学 & 数据科学 在读
            
            ---
            
            💬 *"DMR-ML Pro 目前为内测版本。后续计划开通更多的投资标的和更多的交易提示功能。希望这个工具能帮助更多投资者做出理性决策。*
            
            *欢迎反馈，多多交流，让我们一起进步！"*
            
            ---
            
            **🌍 联系方式**
            - ✉️ 个人邮箱：ykai.w@outlook.com
            - 💻 GitHub：github.com/ykkai-w
            
            ---
            
            ☕️ 有任何建议或Bug反馈，欢迎联系开发团队！
            """)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #AAAAAA; font-size: 0.75rem;">
            <p><strong>DMR-ML Pro v1.0-内测版</strong></p>
            <p>© 2026 ykai-w</p>
        </div>
        """, unsafe_allow_html=True)
        
        return {
            'momentum_window': momentum_window,
            'ma_window': ma_window,
            'risk_trigger': risk_trigger,
            'risk_release': risk_release,
            'show_dmr_comparison': show_dmr_comparison,
            'show_benchmark': show_benchmark,
            'log_scale': log_scale,
        }


# ============================================================
# 主内容区
# ============================================================

def render_overview_tab(result_ml: BacktestResult, result_base: BacktestResult, bench: pd.Series, params: dict):
    """渲染概览标签页"""
    charts = DashboardCharts()
    
    # 计算沪深300基准指标（用于对比）
    bench_return = bench.iloc[-1] / bench.iloc[0] - 1  # 累计收益
    n_years = len(bench) / 252
    bench_annual = (1 + bench_return) ** (1 / n_years) - 1  # 年化收益
    bench_cummax = bench.cummax()
    bench_dd = ((bench - bench_cummax) / bench_cummax).min()  # 最大回撤
    bench_daily_ret = bench.pct_change().dropna()
    bench_sharpe = (bench_daily_ret.mean() * 252 - 0.03) / (bench_daily_ret.std() * np.sqrt(252)) if bench_daily_ret.std() > 0 else 0
    
    # 核心指标行
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        render_metric_card(
            "累计收益",
            f"{result_ml.total_return:.1%}",
            f"vs 沪深300:|超额收益 {(result_ml.total_return - bench_return):+.1%}",
            result_ml.total_return > bench_return
        )
    
    with col2:
        render_metric_card(
            "年化收益",
            f"{result_ml.annual_return:.1%}",
            f"vs 沪深300:|超额收益 {(result_ml.annual_return - bench_annual):+.1%}",
            result_ml.annual_return > bench_annual
        )
    
    with col3:
        render_metric_card(
            "最大回撤",
            f"{result_ml.max_drawdown:.1%}",
            f"vs 沪深300:|改善 {abs(bench_dd - result_ml.max_drawdown):.1%}",
            result_ml.max_drawdown > bench_dd
        )
    
    with col4:
        render_metric_card(
            "夏普比率",
            f"{result_ml.sharpe_ratio:.2f}",
            f"vs 沪深300:|超越 {(result_ml.sharpe_ratio - bench_sharpe):+.2f}",
            result_ml.sharpe_ratio > bench_sharpe
        )
    
    with col5:
        render_metric_card(
            "胜率",
            f"{result_ml.win_rate:.1%}",
            f"交易统计:|盈亏比 {result_ml.profit_loss_ratio:.2f}",
            True
        )
    
    # 回测说明
    st.caption("回测区间：2019-01-01 至今 | 数据来源：Tushare")
    
    render_divider()
    
    # 净值曲线
    st.markdown("### 📈 净值走势")
    
    curves = {'DMR-ML': result_ml.equity_curve}
    if params['show_dmr_comparison']:
        curves['DMR'] = result_base.equity_curve
    if params['show_benchmark']:
        curves['沪深300'] = pd.Series(bench.values, index=result_ml.equity_curve.index)
    
    fig = charts.create_equity_curve(curves, log_scale=params['log_scale'])
    st.plotly_chart(fig, use_container_width=True)


def render_signal_tab(df300: pd.DataFrame, df1000: pd.DataFrame, ml_probs: pd.Series, params: dict):
    """渲染信号标签页"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 生成实时信号
        signal_gen = SignalGenerator(
            df300, df1000, ml_probs,
            params['momentum_window'],
            params['ma_window']
        )
        signal = signal_gen.generate_signal()
        
        render_signal_card(
            signal['final_signal'],
            signal['final_reason'],
            signal['ml_risk']['probability']
        )
        
        st.markdown("---")
        
        # 技术指标详情
        st.markdown("### 📐 技术指标详情")
        
        ind = signal['indicators']
        
        col_a, col_b = st.columns(2)
        
        # 动量颜色和箭头
        mom300_color = "#66BB6A" if ind['csi300']['momentum'] > 0 else "#EF5350"
        mom300_arrow = "🔺" if ind['csi300']['momentum'] > 0 else "🔻"
        mom1000_color = "#66BB6A" if ind['csi1000']['momentum'] > 0 else "#EF5350"
        mom1000_arrow = "🔺" if ind['csi1000']['momentum'] > 0 else "🔻"
        
        with col_a:
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, #1e2530, #252d3a); border-radius: 12px; padding: 1.2rem; border-left: 4px solid #64B5F6;">
                <h4 style="color: #64B5F6; margin: 0 0 1rem 0; font-size: 1.1rem;">▎沪深300</h4>
                <div style="display: grid; gap: 0.6rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">现价</span>
                        <span style="color: #FFFFFF; font-weight: 600;">{ind['csi300']['price']:,.0f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">动量</span>
                        <span style="color: {mom300_color}; font-weight: 600;">{ind['csi300']['momentum']:+.2%} {mom300_arrow}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">均线</span>
                        <span style="color: #FFFFFF; font-weight: 600;">{ind['csi300']['ma']:,.0f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">偏离度</span>
                        <span style="color: #FFFFFF; font-weight: 600;">{ind['csi300']['bias']:+.2%}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; margin-top: 0.3rem;">
                        <span style="color: #AAAAAA; font-weight: 600;">信号</span>
                        <span style="color: {'#66BB6A' if ind['csi300']['signal'] else '#EF5350'}; font-weight: 700; font-size: 1.1rem;">
                            {'✅ 多头' if ind['csi300']['signal'] else '❌ 空头'}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_b:
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, #1e2530, #252d3a); border-radius: 12px; padding: 1.2rem; border-left: 4px solid #FF6B6B;">
                <h4 style="color: #FF6B6B; margin: 0 0 1rem 0; font-size: 1.1rem;">▎中证1000</h4>
                <div style="display: grid; gap: 0.6rem;">
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">现价</span>
                        <span style="color: #FFFFFF; font-weight: 600;">{ind['csi1000']['price']:,.0f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">动量</span>
                        <span style="color: {mom1000_color}; font-weight: 600;">{ind['csi1000']['momentum']:+.2%} {mom1000_arrow}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">均线</span>
                        <span style="color: #FFFFFF; font-weight: 600;">{ind['csi1000']['ma']:,.0f}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #3a4556;">
                        <span style="color: #AAAAAA;">偏离度</span>
                        <span style="color: #FFFFFF; font-weight: 600;">{ind['csi1000']['bias']:+.2%}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.6rem 0; margin-top: 0.3rem;">
                        <span style="color: #AAAAAA; font-weight: 600;">信号</span>
                        <span style="color: {'#66BB6A' if ind['csi1000']['signal'] else '#EF5350'}; font-weight: 700; font-size: 1.1rem;">
                            {'✅ 多头' if ind['csi1000']['signal'] else '❌ 空头'}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 💡 信号解读")
        
        st.info(f"""
        **数据日期**: {signal['data_date']}
        
        **DMR策略信号**: {signal['dmr_signal']}
        
        **ML风险状态**: {'⚠️ 避险模式' if signal['ml_risk']['is_alert'] else '✅ 正常交易'}
        
        **最终信号**: {signal['final_signal']}
        
        **执行时点**: {signal['execution_time']}
        """)
        
        # 添加大间距，使ML风险概率与左侧技术指标详情标题对齐
        st.markdown('<div style="margin-top: 7rem;"></div>', unsafe_allow_html=True)
        
        # 风险概率仪表
        ml_prob = signal['ml_risk']['probability']
        st.markdown("### 🛡️ ML风险概率")
        st.caption("ML模型基于当前技术指标预测未来5日下跌风险。>40%触发避险，<33%解除避险")
        st.progress(min(ml_prob, 1.0))
        
        col_c, col_d = st.columns(2)
        with col_c:
            st.metric("当前概率", f"{ml_prob:.1%}")
        with col_d:
            st.metric("触发阈值", f"{signal['ml_risk']['trigger_threshold']:.0%}")


def render_analysis_tab(result_ml: BacktestResult, result_base: BacktestResult, bench: pd.Series, params: dict):
    """渲染分析标签页"""
    charts = DashboardCharts()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📉 回撤分析", "📆 月度收益", "💰 收益分布", "⚡ 滚动夏普"])
    
    with tab1:
        curves = {
            'DMR-ML': result_ml.equity_curve,
            'DMR': result_base.equity_curve,
            '沪深300': pd.Series(bench.values, index=result_ml.equity_curve.index),
        }
        fig = charts.create_drawdown(curves)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = charts.create_monthly_heatmap(result_ml.equity_curve)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = charts.create_return_distribution(result_ml.trades)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        curves = {
            'DMR-ML': result_ml.equity_curve,
            'DMR': result_base.equity_curve,
        }
        fig = charts.create_rolling_sharpe(curves)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("📌 说明：126个交易日约为半年，滚动计算夏普比率以观察策略稳定性变化")


def render_trades_tab(result_ml: BacktestResult, df300: pd.DataFrame, df1000: pd.DataFrame, params: dict):
    """渲染交易标签页"""
    charts = DashboardCharts()
    
    # 交易统计摘要
    analyzer = TradeAnalyzer(result_ml.trades)
    summary = analyzer.get_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总交易次数", f"{summary['total_trades']} 笔")
    with col2:
        st.metric("盈利/亏损", f"{summary['winning_trades']}/{summary['losing_trades']}")
    with col3:
        st.metric("平均持仓", f"{summary['avg_holding_days']:.1f} 天")
    with col4:
        st.metric("最佳单笔", f"{summary.get('best_trade', 0):.1%}")
    
    st.markdown("---")
    
    # 年度配置统计
    st.markdown("### 📁 年度资产配置")
    yearly_df = analyzer.get_yearly_allocation()
    if not yearly_df.empty:
        st.dataframe(yearly_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # 交易信号图
    st.markdown("### 🔄 交易信号可视化")
    
    col1, col2 = st.columns(2)
    
    with col1:
        year = st.selectbox("选择年份", [2025, 2024, 2023, 2022, 2021, 2020, 2019])
    
    with col2:
        asset = st.selectbox("选择资产", ["中证1000", "沪深300"])
    
    target_asset = '1000' if asset == "中证1000" else '300'
    df_asset = df1000 if target_asset == '1000' else df300
    
    fig = charts.create_trade_signals(
        df_asset, result_ml.trades,
        target_asset=target_asset,
        year=year,
        ma_window=params['ma_window']
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 主函数
# ============================================================

def main():
    """主函数"""
    # 注入样式
    inject_custom_css()
    
    # 渲染头部
    render_header()
    
    # 渲染侧边栏
    params = render_sidebar()
    
    # 加载数据
    with st.spinner("📡 正在加载市场数据..."):
        try:
            df300, df1000 = load_data()
        except Exception as e:
            st.error(f"数据加载失败: {e}")
            st.info("请检查网络连接或 Tushare Token 配置")
            return
    
    # 训练ML模型
    with st.spinner("🤖 正在训练ML风险模型..."):
        ml_probs = train_ml_model(df300)
    
    # 运行回测
    with st.spinner("⚡ 正在执行策略回测..."):
        result_ml, result_base, bench = run_strategy_backtest(
            df300, df1000, ml_probs,
            params['momentum_window'],
            params['ma_window']
        )
    
    # 主内容标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 策略概览",
        "🎯 今日信号",
        "🔬 深度分析",
        "📋 交易记录"
    ])
    
    with tab1:
        render_overview_tab(result_ml, result_base, bench, params)
    
    with tab2:
        render_signal_tab(df300, df1000, ml_probs, params)
    
    with tab3:
        render_analysis_tab(result_ml, result_base, bench, params)
    
    with tab4:
        render_trades_tab(result_ml, df300, df1000, params)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #AAAAAA; font-size: 0.8rem; padding: 1rem;">
        <p>⚠️ <strong>风险提示</strong>：本策略基于历史数据回测，过往业绩不代表未来表现。投资有风险，决策需谨慎。</p>
        <p>DMR-ML Pro v1.0-内测版 | 基于机器学习的双重动量轮动策略 | © 2026 ykai-w</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
