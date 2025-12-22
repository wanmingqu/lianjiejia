#!/usr/bin/env python3
"""
测试真实知识库连接的知识库Agent
"""

import asyncio
from src.agents.knowledge_agent.tools import (
    search_knowledge_base,
    browse_knowledge_category,
    get_document_content,
    get_latest_updates,
    full_text_search
)


async def test_real_kb_tools():
    """测试连接真实知识库的工具功能"""
    print("=== 测试真实知识库查询工具 ===\n")
    
    # 1. 测试浏览所有数据库
    print("1. 测试浏览所有知识库")
    browse_result = browse_knowledge_category.invoke({
        'category': '全部',
        'sort_by': 'update_date',
        'limit': 10
    })
    print(f"状态: {browse_result['status']}")
    print(f"总文件数: {browse_result['total_count']}")
    for file in browse_result['results'][:3]:  # 只显示前3个
        print(f"  - {file['title']} (来源: {file['database_name']})")
    print()
    
    # 2. 测试搜索功能
    print("2. 测试搜索功能")
    print("搜索关键词: ['规范', '制度']")
    search_result = search_knowledge_base.invoke({
        'keywords': ['规范', '制度'], 
        'category': '全部', 
        'max_results': 5
    })
    print(f"状态: {search_result['status']}")
    print(f"找到文档数: {search_result['total_found']}")
    for doc in search_result['results'][:3]:  # 只显示前3个
        print(f"  - {doc['title']} (数据库: {doc['database_name']}) - 相关度: {doc['relevance_score']}")
    print()
    
    # 3. 测试获取文件内容（需要先有文件ID）
    if browse_result['status'] == 'success' and browse_result['results']:
        first_file = browse_result['results'][0]
        file_id = first_file['doc_id']
        print(f"3. 测试获取文件内容 (文件ID: {file_id})")
        content_result = get_document_content.invoke({'doc_id': file_id})
        print(f"状态: {content_result['status']}")
        if content_result['status'] == 'success':
            print(f"文件标题: {content_result['title']}")
            print(f"来源数据库: {content_result['category']}")
            print(f"内容长度: {len(content_result['content'])}字符")
            print(f"内容片段: {content_result['content'][:200]}...")
        print()
    
    # 4. 测试全文检索
    print("4. 测试全文检索")
    print("查询: '公司规范'")
    search_result = full_text_search.invoke({
        'query': '公司规范',
        'max_results': 3
    })
    print(f"状态: {search_result['status']}")
    print(f"找到结果数: {search_result['total_found']}")
    for result in search_result['results']:
        print(f"  - {result['title']} - 相关度: {result['relevance_score']}")
        print(f"    片段: {result['relevant_snippet'][:100]}...")
    print()
    
    # 5. 测试最新更新
    print("5. 测试最新更新查询")
    print("查询最近30天的更新")
    updates_result = get_latest_updates.invoke({
        'days': 30,
        'category': '全部'
    })
    print(f"状态: {updates_result['status']}")
    print(f"更新数量: {updates_result['total_updates']}")
    for update in updates_result['results'][:3]:  # 只显示前3个
        print(f"  - {update['title']} ({update['update_date']}) - {update['database_name']}")
    print()


def test_kb_manager_directly():
    """直接测试知识库管理器"""
    print("=== 直接测试知识库管理器 ===\n")
    
    from src.knowledge.manager import KnowledgeBaseManager
    
    try:
        # 初始化知识库管理器
        kb_manager = KnowledgeBaseManager('./saves/knowledge_base_data')
        
        # 获取所有数据库信息
        databases = kb_manager.get_databases()
        print(f'数据库总数: {len(databases["databases"])}')
        
        for db in databases["databases"]:
            print(f'数据库: {db["name"]}')
            print(f'ID: {db["db_id"]}')
            print(f'描述: {db.get("description", "无")}')
            print(f'类型: {db.get("kb_type", "未知")}')
            print(f'文件数量: {db.get("row_count", 0)}')
            
            # 显示文件列表
            files = db.get("files", {})
            if files:
                print("文件列表:")
                for file_id, file_info in list(files.items())[:3]:  # 只显示前3个文件
                    print(f"  - {file_info.get('filename', '未知文件')} ({file_info.get('type', '未知类型')})")
            
            print('-' * 50)
        
    except Exception as e:
        print(f"测试知识库管理器失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("开始测试真实知识库Agent\n")
    
    try:
        # 直接测试知识库管理器
        test_kb_manager_directly()
        print()
        
        # 测试工具功能
        await test_real_kb_tools()
        
        print("🎉 所有真实知识库测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())