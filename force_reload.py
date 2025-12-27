#!/usr/bin/env python3
"""强制重新加载FinancialReportAgent到API"""

import asyncio
from src.agents import agent_manager

async def force_reload():
    print("=== 强制重新加载FinancialReportAgent ===")
    
    # 1. 移除FinancialReportAgent
    if 'FinancialReportAgent' in agent_manager._classes:
        del agent_manager._classes['FinancialReportAgent']
        print("1. 移除旧的FinancialReportAgent类")
    
    if 'FinancialReportAgent' in agent_manager._instances:
        del agent_manager._instances['FinancialReportAgent']
        print("2. 移除旧的FinancialReportAgent实例")
    
    # 2. 重新导入
    print("3. 重新导入FinancialReportAgent...")
    from src.agents.financial_report.graph import FinancialReportAgent
    
    # 3. 重新注册
    agent_manager.register_agent(FinancialReportAgent)
    print("4. 重新注册FinancialReportAgent")
    
    # 4. 实例化
    agent_manager.init_all_agents()
    print("5. 重新实例化所有Agent")
    
    # 5. 测试API
    print("6. 测试API返回...")
    agents_info = await agent_manager.get_agents_info()
    
    financial_agents = [agent for agent in agents_info if 'FinancialReport' in agent.get('id', '')]
    if financial_agents:
        print(f"✅ FinancialReportAgent已在API中可用:")
        agent = financial_agents[0]
        print(f"   ID: {agent['id']}")
        print(f"   名称: {agent['name']}")
        print(f"   描述: {agent['description'][:50]}...")
        print(f"   能力: {len(agent.get('capabilities', []))}个")
    else:
        print("❌ FinancialReportAgent仍未在API中找到")
        print("所有Agent ID:", [a['id'] for a in agents_info])

if __name__ == "__main__":
    asyncio.run(force_reload())