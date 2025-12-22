#!/usr/bin/env python3
"""测试文档撰写Agent"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.document_agent.context import Context
from src.agents.document_agent.graph import DocumentAgent

async def test_document_agent():
    """测试文档撰写Agent"""
    print("🚀 测试文档撰写Agent...")
    
    try:
        # 创建上下文
        context = Context(
            document_type="技术文档",
            output_format="Markdown",
            writing_style="正式专业",
            knowledge_dependency="70%",
            knowledge_bases=["默认知识库"],
            include_references=True,
            auto_optimize=True
        )
        
        print(f"✅ 上下文创建成功")
        print(f"   - 文档类型: {context.document_type}")
        print(f"   - 输出格式: {context.output_format}")
        print(f"   - 知识库: {context.knowledge_bases}")
        
        # 创建Agent
        agent = DocumentAgent()
        print(f"✅ Agent创建成功")
        
        # 测试工具获取
        tools = agent.get_available_tools()
        print(f"✅ 获取工具列表成功: {len(tools)}个工具")
        for tool in tools[:3]:  # 显示前3个工具
            print(f"   - {tool['name']}: {tool['description'][:50]}...")
        
        # 测试简单消息处理
        test_messages = [
            "请帮我生成一个关于微服务架构的技术文档，包含主要概念和实现要点"
        ]
        
        # 创建上下文实例以获取自动生成的 thread_id 和 user_id
        from src.agents.document_agent.context import Context as DocumentContext
        
        # 先创建一个上下文实例来获取生成的 ID
        temp_context = DocumentContext(
            document_type="技术文档",
            output_format="Markdown", 
            writing_style="正式专业",
            knowledge_dependency="70%",
            knowledge_bases=["默认知识库"],
            include_references=True,
            auto_optimize=True,
            enable_voice_notification=True,
            voice_type="女声"
        )
        
        # 使用上下文中的 ID 创建 input_context
        input_context = {
            "thread_id": temp_context.thread_id,
            "user_id": temp_context.user_id,
            "document_type": "技术文档",
            "output_format": "Markdown", 
            "writing_style": "正式专业",
            "knowledge_dependency": "70%",
            "knowledge_bases": ["默认知识库"],
            "include_references": True,
            "auto_optimize": True,
            "enable_voice_notification": True,
            "voice_type": "女声"
        }
        
        print(f"📝 测试消息处理...")
        # 先尝试简单的调用，不传递 input_context
        try:
            print("尝试简单调用...")
            result = await agent.invoke_messages(test_messages)
            print(f"简单调用成功，结果类型: {type(result)}")
        except Exception as e1:
            print(f"简单调用失败: {e1}")
            print("尝试传递配置...")
            result = await agent.invoke_messages(test_messages, input_context=input_context)
            print(f"配置调用成功，结果类型: {type(result)}")
        
        if result.get("messages"):
            print(f"✅ 消息处理成功")
            print(f"📄 生成的文档内容预览:")
            print("-" * 50)
            
            # 提取最后一条消息的内容
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                content = str(last_message.content)
                # 处理复杂内容格式
                if isinstance(content, list):
                    text_content = ""
                    for item in content:
                        if item.get("type") == "text":
                            text_content += item.get("text", "")
                    content = text_content
            else:
                content = str(last_message)
                
            print(content[:500] + "..." if len(content) > 500 else content)
            print("-" * 50)
        else:
            print(f"❌ 消息处理失败: {result}")
        
        # 测试上下文信息获取
        context_info = agent.get_context_info(context=context)
        print(f"✅ 上下文信息获取成功")
        print(f"   配置项数量: {len(context_info)}")
        
        print(f"🎉 DocumentAgent测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_agent())