"""
DMR Pro System - 命令行入口
==============================
支持命令行运行回测和启动Web界面

用法:
    # 启动Web界面
    python run.py web
    
    # 运行回测
    python run.py backtest
    
    # 生成今日信号
    python run.py signal

Author: DMR Pro Team
"""

import sys
import subprocess
from datetime import datetime


def run_web():
    """启动Streamlit Web界面"""
    print("=" * 60)
    print("🚀 启动 DMR-ML Pro Web 界面")
    print("-" * 60)
    print("访问地址: http://localhost:8501")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app_dashboard.py"])


def run_backtest():
    """运行策略回测"""
    from config import get_config
    from data_service import get_data_service
    from models import MLRiskModel
    from backtest_engine import BacktestEngine
    from reports import ReportGenerator
    
    print("=" * 60)
    print("📊 DMR-ML Pro 策略回测")
    print("-" * 60)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 加载数据
    print("\n>>> 加载市场数据...")
    data_service = get_data_service()
    df300, df1000 = data_service.get_aligned_data()
    print(f"数据范围: {df300.index[0].strftime('%Y-%m-%d')} 至 {df300.index[-1].strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(df300)}")
    
    # 训练ML模型
    ml_model = MLRiskModel()
    ml_probs = ml_model.fit_predict(df300)
    
    # 参数优化
    engine = BacktestEngine()
    best_params, best_result, _ = engine.optimize_parameters(df300, df1000, ml_probs)
    
    # 运行回测
    print(f"\n>>> 基于最优参数执行回测...")
    result_ml = engine.run_backtest(
        df300, df1000,
        best_params[0], best_params[1],
        ml_probs=ml_probs,
        strategy_name="DMR-ML"
    )
    
    result_base = engine.run_backtest(
        df300, df1000,
        best_params[0], best_params[1],
        ml_probs=None,
        strategy_name="DMR"
    )
    
    # 生成报告
    report = ReportGenerator(result_ml)
    report.print_summary()
    
    # 策略对比
    print("\n" + "=" * 60)
    print("策略对比")
    print("-" * 60)
    print(f"{'指标':<15} | {'DMR-ML':<15} | {'DMR':<15}")
    print("-" * 60)
    print(f"{'累计收益':<15} | {result_ml.total_return:<15.2%} | {result_base.total_return:<15.2%}")
    print(f"{'年化收益':<15} | {result_ml.annual_return:<15.2%} | {result_base.annual_return:<15.2%}")
    print(f"{'最大回撤':<15} | {result_ml.max_drawdown:<15.2%} | {result_base.max_drawdown:<15.2%}")
    print(f"{'夏普比率':<15} | {result_ml.sharpe_ratio:<15.2f} | {result_base.sharpe_ratio:<15.2f}")
    print("=" * 60)


def run_signal():
    """生成今日交易信号"""
    from config import get_config
    from data_service import get_data_service
    from models import MLRiskModel
    from reports import SignalGenerator
    
    print("=" * 60)
    print("📌 DMR-ML Pro 今日信号")
    print("=" * 60)
    
    # 加载数据
    data_service = get_data_service()
    df300, df1000 = data_service.get_aligned_data()
    
    # 训练ML模型
    print(">>> 训练ML模型...")
    ml_model = MLRiskModel()
    ml_probs = ml_model.fit_predict(df300, verbose=False)
    
    # 生成信号
    config = get_config()
    signal_gen = SignalGenerator(
        df300, df1000, ml_probs,
        config.strategy.default_momentum_window,
        config.strategy.default_ma_window
    )
    signal_gen.print_signal()


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("""
DMR Pro System - 量化交易系统
==============================

用法:
    python run.py <command>

命令:
    web       启动Web界面
    backtest  运行策略回测
    signal    生成今日信号
    help      显示帮助信息

示例:
    python run.py web
    python run.py backtest
    python run.py signal
        """)
        return
    
    command = sys.argv[1].lower()
    
    if command == "web":
        run_web()
    elif command == "backtest":
        run_backtest()
    elif command == "signal":
        run_signal()
    elif command == "help":
        main()  # 显示帮助
    else:
        print(f"未知命令: {command}")
        print("使用 'python run.py help' 查看帮助")


if __name__ == "__main__":
    main()
