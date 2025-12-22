#!/usr/bin/env python3
"""
知识库查询助手测试脚本
用于验证KnowledgeAgent的各项功能
"""

import asyncio
from src.agents.knowledge_agent.graph import KnowledgeAgent
from src.agents.knowledge_agent.tools import (
    search_knowledge_base,
    browse_knowledge_category,
    get_document_content,
    get_latest_updates,
    full_text_search
)


async def test_tools():
    """测试所有工具功能"""
    print("=== 测试知识库查询工具 ===\n")
    
    # 1. 测试搜索功能
    print("1. 测试搜索功能")
    print("搜索关键词: ['入职', '流程']")
    search_result = search_knowledge_base.invoke({
        'keywords': ['入职', '流程'], 
        'category': '全部', 
        'max_results': 5
    })
    print(f"状态: {search_result['status']}")
    print(f"找到文档数: {search_result['total_found']}")
    for doc in search_result['results']:
        print(f"  - {doc['title']} ({doc['category']}) - 相关度: {doc['relevance_score']}")
    print()
    
    # 2. 测试分类浏览
    print("2. 测试分类浏览")
    print("浏览类别: 员工手册")
    browse_result = browse_knowledge_category.invoke({
        'category': '员工手册', 
        'sort_by': 'update_date', 
        'limit': 3
    })
    print(f"状态: {browse_result['status']}")
    print(f"文档数量: {browse_result['total_count']}")
    for doc in browse_result['results']:
        print(f"  - {doc['title']} - 更新日期: {doc['update_date']}")
    print()
    
    # 3. 测试获取文档内容
    print("3. 测试获取文档内容")
    print("文档ID: EMP001")
    content_result = get_document_content.invoke({'doc_id': 'EMP001'})
    print(f"状态: {content_result['status']}")
    print(f"标题: {content_result['title']}")
    print(f"类别: {content_result['category']}")
    print(f"内容长度: {len(content_result['content'])}字符")
    print(f"作者: {content_result['metadata']['author']}")
    print(f"更新日期: {content_result['metadata']['update_date']}")
    print()
    
    # 4. 测试最新更新
    print("4. 测试最新更新查询")
    print("查询最近7天内的更新")
    updates_result = get_latest_updates.invoke({
        'days': 7,
        'category': '全部'
    })
    print(f"状态: {updates_result['status']}")
    print(f"更新数量: {updates_result['total_updates']}")
    for update in updates_result['results']:
        print(f"  - {update['title']} ({update['update_type']}) - {update['update_date']}")
    print()
    
    # 5. 测试全文检索
    print("5. 测试全文检索")
    print("查询: '董事会职责'")
    search_result = full_text_search.invoke({
        'query': '董事会职责',
        'max_results': 3
    })
    print(f"状态: {search_result['status']}")
    print(f"找到结果数: {search_result['total_found']}")
    for result in search_result['results']:
        print(f"  - {result['title']} - 相关度: {result['relevance_score']}")
        print(f"    片段: {result['relevant_snippet'][:50]}...")
    print()


async def test_agent():
    """测试Agent完整功能"""
    print("=== 测试知识库Agent ===\n")
    
    # 创建Agent实例
    agent = KnowledgeAgent()
    print(f"Agent名称: {agent.name}")
    print(f"Agent描述: {agent.description}")
    print(f"Agent能力: {agent.capabilities}")
    
    # 测试工具列表
    tools = agent.get_tools()
    print(f"可用工具数量: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # 测试图创建
    try:
        graph = await agent.get_graph()
        print("✓ 图创建成功")
    except Exception as e:
        print(f"✗ 图创建失败: {e}")
    
    print()


async def test_error_handling():
    """测试错误处理"""
    print("=== 测试错误处理 ===\n")
    
    # 测试不存在的文档ID
    print("1. 测试不存在的文档ID")
    result = get_document_content.invoke({'doc_id': 'INVALID_ID'})
    print(f"状态: {result['status']}")
    print(f"消息: {result['message']}")
    print()
    
    # 测试不存在的类别
    print("2. 测试不存在的类别")
    result = browse_knowledge_category.invoke({'category': '不存在的类别'})
    print(f"状态: {result['status']}")
    print(f"消息: {result['message']}")
    print()


async def main():
    """主测试函数"""
    print("开始测试知识库查询助手\n")
    
    try:
        await test_tools()
        await test_agent()
        await test_error_handling()
        
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())