#!/usr/bin/env python3
"""重新加载所有Agent"""

import asyncio
from src.agents import agent_manager

async def restart_agents():
    """重新加载所有Agent"""
    print("=== 重新加载所有Agent ===")
    
    # 重新发现Agent
    print("1. 重新发现Agent...")
    agent_manager.auto_discover_agents()
    
    print(f"2. 注册的Agent类: {list(agent_manager._classes.keys())}")
    
    # 重新初始化
    print("3. 重新初始化Agent...")
    agent_manager._instances.clear()  # 清空现有实例
    agent_manager.init_all_agents()
    
    print(f"4. 初始化后的Agent实例: {list(agent_manager._instances.keys())}")
    
    # 检查FinancialReportAgent
    if 'FinancialReportAgent' in agent_manager._instances:
        agent = agent_manager._instances['FinancialReportAgent']
        print(f"\n✅ FinancialReportAgent加载成功!")
        print(f"   名称: {agent.name}")
        print(f"   描述: {agent.description}")
        print(f"   能力: {agent.capabilities}")
        print(f"   工具数量: {len(agent.get_tools())}")
    else:
        print("\n❌ FinancialReportAgent未找到")
    
    # 显示所有Agent信息
    print(f"\n=== 所有Agent列表 ({len(agent_manager._instances)}个) ===")
    for agent_id, instance in agent_manager._instances.items():
        print(f"  {agent_id}: {instance.name}")

if __name__ == "__main__":
    asyncio.run(restart_agents())