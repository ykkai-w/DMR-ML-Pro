#!/bin/bash
# DMR-ML Pro 傻瓜式启动器（macOS）
# 双击即可运行，自动处理所有依赖

cd "$(dirname "$0")"

# 清屏
clear

# 显示欢迎信息
echo "╔════════════════════════════════════════╗"
echo "║                                        ║"
echo "║       DMR-ML Pro v1.0-内测版           ║"
echo "║   智能量化交易系统                      ║"
echo "║                                        ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "🚀 正在启动，请稍候..."
echo ""

# 检查Python
echo "📍 [1/3] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "❌ 未检测到Python环境"
    echo ""
    echo "请先安装Python："
    echo "1. 访问 https://www.python.org/downloads/"
    echo "2. 下载Python 3.10版本"
    echo "3. 安装后重新运行此脚本"
    echo ""
    read -p "按任意键退出..."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "   ✅ $PYTHON_VERSION"

# 检查并安装依赖
echo ""
echo "📦 [2/3] 检查依赖包..."

# 检查streamlit是否安装
if ! python3 -c "import streamlit" &> /dev/null 2>&1; then
    echo "   📥 首次运行，正在安装依赖..."
    echo "   （大约需要1-2分钟，请耐心等待）"
    echo ""
    
    pip3 install -r requirements.txt -q
    
    if [ $? -eq 0 ]; then
        echo "   ✅ 依赖安装完成"
    else
        echo "   ❌ 依赖安装失败"
        echo "   请检查网络连接或手动执行："
        echo "   pip3 install -r requirements.txt"
        echo ""
        read -p "按任意键退出..."
        exit 1
    fi
else
    echo "   ✅ 依赖已安装"
fi

# 启动应用
echo ""
echo "🌐 [3/3] 启动Web界面..."
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  ✅ 启动成功！                          ║"
echo "║                                        ║"
echo "║  浏览器将自动打开系统界面               ║"
echo "║  网址：http://localhost:8501           ║"
echo "║                                        ║"
echo "║  ⚠️  请勿关闭此窗口                     ║"
echo "║  关闭窗口 = 停止服务                    ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "💡 如浏览器未自动打开，请手动访问："
echo "   http://localhost:8501"
echo ""
echo "════════════════════════════════════════"
echo ""

# 启动Streamlit（自动打开浏览器）
streamlit run app_dashboard.py --server.headless=false

# 如果用户关闭了
echo ""
echo "👋 服务已停止"
read -p "按任意键退出..."
