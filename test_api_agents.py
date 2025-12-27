#!/usr/bin/env python3
"""测试API Agent列表"""

import asyncio
from src.agents import agent_manager

async def test_api_agents():
    try:
        # 模拟API调用 get_agents_info
        agents_info = await agent_manager.get_agents_info()
        
        print(f'API返回的Agent数量: {len(agents_info)}')
        print('\nAgent列表:')
        for i, agent_info in enumerate(agents_info, 1):
            print(f'{i}. ID: {agent_info["id"]}')
            print(f'   名称: {agent_info.get("name", "未知")}')
            print(f'   描述: {agent_info.get("description", "无描述")[:50]}...')
            print()
            
        # 检查FinancialReportAgent是否在列表中
        financial_agents = [agent for agent in agents_info if 'FinancialReport' in agent.get('id', '')]
        if financial_agents:
            print(f'✅ 找到财报相关Agent: {[agent["id"] for agent in financial_agents]}')
        else:
            print('❌ 没有找到FinancialReportAgent')
            
        # 手动检查agent_manager状态
        print(f'\nagent_manager状态:')
        print(f'  _classes: {list(agent_manager._classes.keys())}')
        print(f'  _instances: {list(agent_manager._instances.keys())}')
        
        # 检查FinancialReportAgent实例的get_info方法
        if 'FinancialReportAgent' in agent_manager._instances:
            agent = agent_manager._instances['FinancialReportAgent']
            try:
                info = await agent.get_info()
                print(f'\nFinancialReportAgent.get_info()结果:')
                print(f'  ID: {info.get("id")}')
                print(f'  名称: {info.get("name")}')
                print(f'  描述: {info.get("description")[:50]}...')
            except Exception as e:
                print(f'\nFinancialReportAgent.get_info()失败: {e}')
        
    except Exception as e:
        print(f'测试失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_agents())