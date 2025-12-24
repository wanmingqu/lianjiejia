#!/bin/bash
# MySQL环境变量设置脚本 - 用于解决SqlReporterAgent连接问题

echo "🔧 MySQL环境变量设置脚本"
echo "=================================="
echo "此脚本将设置SqlReporterAgent所需的MySQL环境变量"
echo ""

# 检查是否已有环境变量
if [ ! -z "$MYSQL_HOST" ] || [ ! -z "$MYSQL_USER" ] || [ ! -z "$MYSQL_PASSWORD" ] || [ ! -z "$MYSQL_DATABASE" ]; then
    echo "⚠️  检测到部分MySQL环境变量已设置："
    [ ! -z "$MYSQL_HOST" ] && echo "  MYSQL_HOST: $MYSQL_HOST"
    [ ! -z "$MYSQL_USER" ] && echo "  MYSQL_USER: $MYSQL_USER"
    [ ! -z "$MYSQL_PASSWORD" ] && echo "  MYSQL_PASSWORD: ${MYSQL_PASSWORD//?/*}"
    [ ! -z "$MYSQL_DATABASE" ] && echo "  MYSQL_DATABASE: $MYSQL_DATABASE"
    [ ! -z "$MYSQL_PORT" ] && echo "  MYSQL_PORT: $MYSQL_PORT"
    echo ""
    read -p "是否要重新设置所有变量？[y/N]: " RESET_ALL
    if [[ $RESET_ALL != "y" && $RESET_ALL != "Y" ]]; then
        echo "📋 使用现有环境变量，跳过设置"
        exit 0
    fi
fi

echo "📝 请输入MySQL连接信息："
echo ""

# 交互式设置
read -p "MySQL主机地址 [localhost]: " input_host
MYSQL_HOST=${input_host:-localhost}

read -p "MySQL用户名 [root]: " input_user
MYSQL_USER=${input_user:-root}

echo ""
read -s -p "MySQL密码: " input_password
MYSQL_PASSWORD=$input_password
echo ""

read -p "MySQL数据库名 [information_schema]: " input_db
MYSQL_DATABASE=${input_db:-information_schema}

read -p "MySQL端口 [3306]: " input_port
MYSQL_PORT=${input_port:-3306}

read -p "数据库描述 [开发测试数据库]: " input_desc
MYSQL_DATABASE_DESCRIPTION=${input_desc:-开发测试数据库}

echo ""
echo "🔍 设置的环境变量："
echo "  MYSQL_HOST: $MYSQL_HOST"
echo "  MYSQL_USER: $MYSQL_USER"
echo "  MYSQL_PASSWORD: ${MYSQL_PASSWORD//?/*}"
echo "  MYSQL_DATABASE: $MYSQL_DATABASE"
echo "  MYSQL_PORT: $MYSQL_PORT"
echo "  MYSQL_DATABASE_DESCRIPTION: $MYSQL_DATABASE_DESCRIPTION"
echo ""

# 测试连接
echo "🧪 测试MySQL连接..."
python3 -c "
import os
import sys
os.environ['MYSQL_HOST'] = '$MYSQL_HOST'
os.environ['MYSQL_USER'] = '$MYSQL_USER'  
os.environ['MYSQL_PASSWORD'] = '$MYSQL_PASSWORD'
os.environ['MYSQL_DATABASE'] = '$MYSQL_DATABASE'
os.environ['MYSQL_PORT'] = '$MYSQL_PORT'
os.environ['MYSQL_DATABASE_DESCRIPTION'] = '$MYSQL_DATABASE_DESCRIPTION'

try:
    from src.agents.common.toolkits.mysql.tools import get_connection_manager
    conn = get_connection_manager()
    if conn.test_connection():
        print('✅ MySQL连接测试成功！')
    else:
        print('❌ MySQL连接测试失败')
        sys.exit(1)
except Exception as e:
    print(f'❌ 连接测试异常: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 连接测试成功！正在保存环境变量..."
    
    # 选择保存方式
    echo "请选择保存方式："
    echo "1) 当前会话（临时）"
    echo "2) 永久保存到 ~/.bashrc"  
    echo "3) 保存到项目 .env 文件"
    echo ""
    read -p "请选择 [1]: " save_option
    
    case $save_option in
        2)
            echo "📁 保存到 ~/.bashrc..."
            {
                echo ""
                echo "# MySQL环境变量 - SqlReporterAgent配置"
                echo "export MYSQL_HOST=\"$MYSQL_HOST\""
                echo "export MYSQL_USER=\"$MYSQL_USER\""
                echo "export MYSQL_PASSWORD=\"$MYSQL_PASSWORD\""
                echo "export MYSQL_DATABASE=\"$MYSQL_DATABASE\""
                echo "export MYSQL_PORT=\"$MYSQL_PORT\""
                echo "export MYSQL_DATABASE_DESCRIPTION=\"$MYSQL_DATABASE_DESCRIPTION\""
                echo ""
            } >> ~/.bashrc
            echo "✅ 已保存到 ~/.bashrc，请运行: source ~/.bashrc"
            ;;
        3)
            echo "📁 保存到 .env 文件..."
            {
                echo "# MySQL环境变量 - SqlReporterAgent配置"
                echo "MYSQL_HOST=$MYSQL_HOST"
                echo "MYSQL_USER=$MYSQL_USER"
                echo "MYSQL_PASSWORD=$MYSQL_PASSWORD"
                echo "MYSQL_DATABASE=$MYSQL_DATABASE"
                echo "MYSQL_PORT=$MYSQL_PORT"
                echo "MYSQL_DATABASE_DESCRIPTION=$MYSQL_DATABASE_DESCRIPTION"
            } > .env
            echo "✅ 已保存到 .env 文件"
            ;;
        *)
            echo "🔄 仅在当前会话中设置"
            ;;
    esac
    
    # 立即导出到当前会话
    export MYSQL_HOST="$MYSQL_HOST"
    export MYSQL_USER="$MYSQL_USER"
    export MYSQL_PASSWORD="$MYSQL_PASSWORD"
    export MYSQL_DATABASE="$MYSQL_DATABASE"
    export MYSQL_PORT="$MYSQL_PORT"
    export MYSQL_DATABASE_DESCRIPTION="$MYSQL_DATABASE_DESCRIPTION"
    
    echo ""
    echo "🎉 MySQL环境变量设置完成！"
    echo "📋 SqlReporterAgent现在应该可以正常连接数据库了！"
    echo ""
    echo "💡 使用提示："
    echo "1. 重启应用程序以使用新的环境变量"
    echo "2. 如果选择了选项2，请运行: source ~/.bashrc"
    echo "3. 如果选择了选项3，确保应用程序能加载 .env 文件"
else
    echo ""
    echo "❌ 连接测试失败！请检查："
    echo "1. MySQL服务是否启动"
    echo "2. 主机地址、端口是否正确"
    echo "3. 用户名、密码是否正确"  
    echo "4. 数据库是否存在"
    echo "5. 网络连接是否正常"
fi

echo ""
echo "🔍 验证SqlReporterAgent..."
python3 -c "
import asyncio
import sys
import os

# 设置环境变量
os.environ['MYSQL_HOST'] = '$MYSQL_HOST'
os.environ['MYSQL_USER'] = '$MYSQL_USER'
os.environ['MYSQL_PASSWORD'] = '$MYSQL_PASSWORD'
os.environ['MYSQL_DATABASE'] = '$MYSQL_DATABASE'
os.environ['MYSQL_PORT'] = '$MYSQL_PORT'
os.environ['MYSQL_DATABASE_DESCRIPTION'] = '$MYSQL_DATABASE_DESCRIPTION'

async def test_agent():
    try:
        from src.agents.reporter import SqlReporterAgent
        agent = SqlReporterAgent()
        tools = await agent.get_tools()
        
        mysql_tools = [tool for tool in tools if hasattr(tool, 'name') and 
                      any(keyword in tool.name.lower() for keyword in ['mysql', 'sql'])]
        
        print(f'✅ SqlReporterAgent创建成功！')
        print(f'🛠️  总工具数量: {len(tools)}')
        print(f'📊  MySQL工具数量: {len(mysql_tools)}')
        print('🎉 SqlReporterAgent现在可以正常工作了！')
        
    except Exception as e:
        print(f'❌ SqlReporterAgent测试失败: {e}')
        sys.exit(1)

asyncio.run(test_agent())
"