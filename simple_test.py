#!/usr/bin/env python3
"""简单测试FinancialReportAgent加载"""

print("=== 测试FinancialReportAgent加载 ===")

try:
    # 测试导入
    from src.agents.financial_report.graph import FinancialReportAgent
    print("✅ FinancialReportAgent导入成功")
    
    # 测试实例化
    agent = FinancialReportAgent()
    print(f"✅ Agent实例化成功: {agent.name}")
    print(f"   描述: {agent.description}")
    print(f"   能力: {agent.capabilities}")
    
    # 测试工具
    tools = agent.get_tools()
    print(f"✅ 工具加载成功: {len(tools)} 个工具")
    tool_names = [tool.name for tool in tools if hasattr(tool, 'name')]
    print(f"   工具列表: {tool_names}")
    
    print("\n🎉 FinancialReportAgent基础功能测试通过！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()