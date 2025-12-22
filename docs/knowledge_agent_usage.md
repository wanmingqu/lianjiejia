# 知识库查询助手使用指南

## 概述

知识库查询助手（KnowledgeAgent）是专门用于查询公司内部知识库的智能助手，支持政策制度、员工手册、流程规范、业务知识等信息查询。

### 🎯 新增功能：知识库选择配置

模仿ChatbotAgent的配置方式，KnowledgeAgent现在支持在配置界面中选择要查询的知识库：

- **多选支持**：可以同时选择多个知识库进行查询
- **动态选项**：自动获取系统中所有可用的知识库
- **默认配置**：默认选择"公司内部规范"知识库
- **灵活切换**：用户可以根据需要随时切换知识库选择

**可用知识库：**
- `公司内部规范` - 公司规章制度、政策文件等
- `合同范本` - 各类合同模板和范本等

## 功能特性

### 🔍 核心查询能力
- **政策制度查询**：公司章程、管理制度、业务规范
- **员工手册查询**：入职指南、行为准则、福利政策  
- **流程规范查询**：工作流程、审批流程、操作指南
- **业务知识查询**：产品知识、服务标准、技术规范

### 📋 查询策略
1. **精确查询**：关键词精确搜索
2. **分类查询**：按类别浏览文档
3. **最新更新**：查询最新政策变更
4. **全文检索**：深度内容搜索

## 可用工具

### 1. search_knowledge_base
在知识库中搜索相关文档
```python
# 示例
search_knowledge_base.invoke({
    'keywords': ['入职', '流程'], 
    'category': '全部', 
    'max_results': 10
})
```

**参数：**
- `keywords`: 搜索关键词列表
- `category`: 文档类别（全部/政策制度/员工手册/流程规范/业务知识）
- `max_results`: 最大返回结果数量

**返回：**
- 搜索结果列表，包含文档信息和相关度评分

### 2. browse_knowledge_category
按类别浏览知识库文档
```python
# 示例
browse_knowledge_category.invoke({
    'category': '员工手册',
    'sort_by': 'update_date',
    'limit': 20
})
```

**参数：**
- `category`: 文档类别
- `sort_by`: 排序方式（update_date/title/relevance）
- `limit`: 返回文档数量限制

### 3. get_document_content
获取具体文档的详细内容
```python
# 示例
get_document_content.invoke({'doc_id': 'EMP001'})
```

**参数：**
- `doc_id`: 文档ID

**返回：**
- 文档的详细内容和元数据

### 4. get_latest_updates
获取最近更新的文档列表
```python
# 示例
get_latest_updates.invoke({
    'days': 7,
    'category': '全部'
})
```

### 5. full_text_search
全文检索功能
```python
# 示例
full_text_search.invoke({
    'query': '员工福利待遇',
    'category': '员工手册',
    'max_results': 10
})
```

## 🚀 快速开始

### 1. 获取Agent实例
```python
from src.agents import agent_manager

# 获取知识库查询助手
knowledge_agent = agent_manager.get_agent('KnowledgeAgent')
```

### 2. 配置知识库选择
```python
# 创建上下文配置
Context = knowledge_agent.context_schema
context = Context()

# 选择要查询的知识库（可多选）
context.knowledge_bases = ["公司内部规范", "合同范本"]

# 配置其他选项
context.search_scope = "全部"  # 查询范围
context.result_format = "详细"  # 结果格式
context.streaming = False  # 是否启用流式输出
context.show_thinking = False  # 是否显示思考过程
```

### 3. 创建会话
```python
# 创建会话
conversation = knowledge_agent.create_conversation("我想了解公司的入职流程")

# 进行对话
response = conversation.send("请帮我查询一下新员工入职需要准备哪些材料？")
print(response)
```

**参数：**
- `days`: 查询最近多少天内的更新
- `category`: 文档类别

### 5. full_text_search
对知识库进行全文检索
```python
# 示例
full_text_search.invoke({
    'query': '董事会职责',
    'max_results': 10
})
```

**参数：**
- `query`: 检索查询语句
- `max_results`: 最大返回结果数量

## 配置选项

### 查询范围（search_scope）
- 全部
- 政策制度
- 员工手册
- 流程规范
- 业务知识

### 结果格式（result_format）
- 简洁：只返回关键信息
- 详细：包含完整描述
- 汇总：返回摘要信息

### 流式输出控制（streaming）
- `true`：启用流式输出
- `false`：等待完整响应后返回

### 思考过程控制（show_thinking）
- `true`：显示模型思考过程
- `false`：不显示思考过程

## 使用示例

### 查询入职流程
```
用户：我想了解公司的入职流程
助手：我来帮您查询新员工入职相关的信息...
[使用search_knowledge_base搜索关键词"入职"和"流程"]
```

### 浏览员工手册
```
用户：请列出所有员工手册相关的文档
助手：我来为您浏览员工手册分类下的所有文档...
[使用browse_knowledge_category按类别浏览]
```

### 查看具体文档
```
用户：我想查看新员工入职指南的详细内容
助手：我来获取新员工入职指南的详细内容...
[使用get_document_content获取文档内容]
```

### 查询最新更新
```
用户：最近一周有哪些政策制度更新？
助手：我来查询最近7天内政策制度类别的最新更新...
[使用get_latest_updates查询最新更新]
```

## 技术实现

- **基础框架**：基于LangChain Agent框架
- **工具系统**：使用@tool装饰器定义5个核心查询工具
- **配置管理**：支持YAML配置文件和动态配置
- **错误处理**：完善的异常处理和用户反馈机制
- **模块化设计**：独立的Agent模块，易于扩展和维护

## 扩展建议

1. **接入真实知识库**：替换模拟数据，连接企业实际知识库系统
2. **权限管理**：添加用户权限和文档访问控制
3. **智能推荐**：基于用户查询历史推荐相关文档
4. **多语言支持**：支持英文等其他语言的知识查询
5. **文档版本控制**：支持文档版本管理和历史记录查询

## 部署说明

1. 知识库Agent已自动注册到系统中
2. 配置文件位于：`/workspace/saves/agents/knowledge_agent/config.yaml`
3. 可通过Agent管理器获取实例使用
4. 支持热重载和配置动态更新