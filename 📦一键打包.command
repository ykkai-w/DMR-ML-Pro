#!/bin/bash
# DMR-ML Pro 一键打包脚本
# 自动创建干净的分发包

cd "$(dirname "$0")"
cd ..

clear
echo "╔════════════════════════════════════════╗"
echo "║                                        ║"
echo "║    DMR-ML Pro 一键打包工具             ║"
echo "║                                        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 设置变量
PACKAGE_NAME="DMR-ML-Pro-v1.0-内测版"
TEMP_DIR="temp_package"
OUTPUT_ZIP="${PACKAGE_NAME}.zip"

echo "📦 开始打包..."
echo ""

# 1. 创建临时目录
echo "📁 [1/5] 创建打包目录..."
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR/$PACKAGE_NAME"

# 2. 复制必要文件
echo "📋 [2/5] 复制文件..."
cp -r DMR_Pro_System/* "$TEMP_DIR/$PACKAGE_NAME/"

# 3. 清理敏感和不必要的文件
echo "🧹 [3/5] 清理临时文件..."
rm -rf "$TEMP_DIR/$PACKAGE_NAME/cache_dmr_pro"
rm -rf "$TEMP_DIR/$PACKAGE_NAME/__pycache__"
rm -f "$TEMP_DIR/$PACKAGE_NAME/.DS_Store"
rm -f "$TEMP_DIR/$PACKAGE_NAME/subscribers.json"
rm -f "$TEMP_DIR/$PACKAGE_NAME/.env"

# 4. 清空config.py中的token
echo "🔒 [4/5] 清空敏感信息..."
if [ -f "$TEMP_DIR/$PACKAGE_NAME/config.py" ]; then
    sed -i '' 's/TUSHARE_TOKEN = ".*"/TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")  # 请在此处填写您的Tushare Token/' "$TEMP_DIR/$PACKAGE_NAME/config.py"
fi

# 5. 压缩
echo "🗜️  [5/5] 压缩打包..."
cd "$TEMP_DIR"
zip -r "../$OUTPUT_ZIP" "$PACKAGE_NAME" -q
cd ..

# 6. 清理临时目录
rm -rf "$TEMP_DIR"

# 完成
if [ -f "$OUTPUT_ZIP" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_ZIP" | cut -f1)
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║  ✅ 打包成功！                          ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    echo "📦 输出文件：$OUTPUT_ZIP"
    echo "📊 文件大小：$FILE_SIZE"
    echo ""
    echo "💡 接下来："
    echo "   1. 将 $OUTPUT_ZIP 发送给亲友"
    echo "   2. 提醒他们查看 📖快速开始指南.md"
    echo "   3. 提醒他们配置自己的 Tushare Token"
    echo ""
else
    echo ""
    echo "❌ 打包失败"
    echo ""
fi

read -p "按任意键退出..."
