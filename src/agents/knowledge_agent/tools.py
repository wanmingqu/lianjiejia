from langchain.tools import tool
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
from src.knowledge.manager import KnowledgeBaseManager


# 初始化知识库管理器实例
_kb_manager = None

def get_kb_manager():
    """获取知识库管理器实例（单例模式）"""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager('./saves/knowledge_base_data')
    return _kb_manager


@tool
def search_knowledge_base(keywords: List[str], category: str = "全部", max_results: int = 10) -> Dict[str, Any]:
    """在知识库中搜索相关文档
    
    Args:
        keywords: 搜索关键词列表
        category: 文档类别：全部, 政策制度, 员工手册, 流程规范, 业务知识
        max_results: 最大返回结果数量
    
    Returns:
        搜索结果列表，包含文档信息和相关度评分
    """
    try:
        # 获取知识库管理器
        kb_manager = get_kb_manager()
        
        # 构建查询文本
        query_text = " ".join(keywords)
        
        # 获取所有可用数据库
        databases = kb_manager.get_databases()
        all_results = []
        
        # 根据类别筛选数据库
        target_databases = []
        if category == "全部":
            target_databases = databases["databases"]
        else:
            # 根据数据库名称判断类别
            for db in databases["databases"]:
                db_name = db.get("name", "").lower()
                if category == "政策制度" and ("规范" in db_name or "制度" in db_name):
                    target_databases.append(db)
                elif category == "合同范本" and ("合同" in db_name or "范本" in db_name):
                    target_databases.append(db)
                else:
                    target_databases.append(db)  # 默认包含所有
        
        # 在每个数据库中搜索
        for db in target_databases:
            db_id = db.get("db_id")
            db_name = db.get("name", "")
            
            if not db_id:
                continue
                
            try:
                # 使用知识库的同步查询功能
                results = kb_manager.query(query_text, db_id)
                
                # 处理搜索结果
                if isinstance(results, list):
                    for result in results[:max_results]:
                        # 计算相关度分数
                        relevance_score = 0
                        content_text = str(result.get("content", "")).lower()
                        title_text = str(result.get("title", "")).lower()
                        
                        for keyword in keywords:
                            keyword_lower = keyword.lower()
                            if keyword_lower in title_text:
                                relevance_score += 3
                            if keyword_lower in content_text:
                                relevance_score += 1
                        
                        if relevance_score > 0:
                            all_results.append({
                                "doc_id": result.get("doc_id", ""),
                                "title": result.get("title", ""),
                                "content": result.get("content", "")[:200] + "...",
                                "category": db_name,
                                "update_date": result.get("update_date", ""),
                                "relevance_score": relevance_score,
                                "database_id": db_id,
                                "database_name": db_name,
                                "matched_keywords": [kw for kw in keywords if kw.lower() in title_text or kw.lower() in content_text]
                            })
                
            except Exception as e:
                print(f"在数据库 {db_name} 中搜索失败: {e}")
                continue
        
        # 按相关度排序并限制结果数量
        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        final_results = all_results[:max_results]
        
        return {
            "status": "success",
            "total_found": len(all_results),
            "returned_count": len(final_results),
            "search_keywords": keywords,
            "search_category": category,
            "results": final_results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"搜索失败: {str(e)}",
            "results": []
        }


@tool
def browse_knowledge_category(category: str = "全部", sort_by: str = "update_date", limit: int = 20) -> Dict[str, Any]:
    """按类别浏览知识库文档
    
    Args:
        category: 文档类别：全部, 政策制度, 员工手册, 流程规范, 业务知识
        sort_by: 排序方式：update_date(更新时间), title(标题), relevance(相关度)
        limit: 返回文档数量限制
    
    Returns:
        指定类别的文档列表
    """
    try:
        # 获取知识库管理器
        kb_manager = get_kb_manager()
        
        # 获取所有数据库
        databases = kb_manager.get_databases()
        
        # 根据类别筛选数据库和文件
        target_databases = []
        if category == "全部":
            target_databases = databases["databases"]
        else:
            # 根据数据库名称判断类别
            for db in databases["databases"]:
                db_name = db.get("name", "").lower()
                if category == "政策制度" and ("规范" in db_name or "制度" in db_name):
                    target_databases.append(db)
                elif category == "合同范本" and ("合同" in db_name or "范本" in db_name):
                    target_databases.append(db)
                else:
                    target_databases.append(db)  # 默认包含所有
        
        # 收集所有文件
        all_files = []
        for db in target_databases:
            db_id = db.get("db_id")
            db_name = db.get("name", "")
            files = db.get("files", {})
            
            for file_id, file_info in files.items():
                all_files.append({
                    "doc_id": file_id,
                    "title": file_info.get("filename", ""),
                    "description": f"来自数据库: {db_name}",
                    "update_date": file_info.get("created_at", ""),
                    "file_type": file_info.get("type", ""),
                    "size": str(file_info.get("size", "")) + " bytes",
                    "database_id": db_id,
                    "database_name": db_name,
                    "status": file_info.get("status", "")
                })
        
        # 根据排序方式排序
        if sort_by == "update_date":
            all_files.sort(key=lambda x: x["update_date"], reverse=True)
        elif sort_by == "title":
            all_files.sort(key=lambda x: x["title"])
        elif sort_by == "relevance":
            # 在实际应用中，这里可以根据用户历史行为或文档热度排序
            all_files.sort(key=lambda x: x["update_date"], reverse=True)
        
        # 限制返回数量
        limited_files = all_files[:limit]
        
        return {
            "status": "success",
            "category": category,
            "total_count": len(all_files),
            "returned_count": len(limited_files),
            "sort_by": sort_by,
            "results": limited_files
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"浏览失败: {str(e)}",
            "results": []
        }


@tool
def get_document_content(doc_id: str) -> Dict[str, Any]:
    """获取具体文档的详细内容
    
    Args:
        doc_id: 文档ID（实际上是file_id）
    
    Returns:
        文档的详细内容和元数据
    """
    try:
        # 获取知识库管理器
        kb_manager = get_kb_manager()
        
        # 获取所有数据库
        databases = kb_manager.get_databases()
        
        # 在所有数据库中查找对应的文件
        file_content = None
        file_metadata = None
        database_info = None
        
        for db in databases["databases"]:
            db_id = db.get("db_id")
            files = db.get("files", {})
            
            if doc_id in files:
                file_info = files[doc_id]
                database_info = db
                
                try:
                    # 简化版本：只获取基本信息，不获取完整内容以避免异步问题
                    file_content = None
                    
                    file_metadata = file_info
                    break
                    
                except Exception as e:
                    print(f"获取文件内容失败: {e}")
                    # 如果无法获取内容，至少返回基本信息
                    file_metadata = file_info
                    break
        
        if not file_metadata:
            return {
                "status": "error",
                "message": f"文档ID '{doc_id}' 不存在",
                "content": None
            }
        
        # 构建返回内容
        content_text = ""
        if file_content and "chunks" in file_content:
            # 从chunks中提取文本内容
            for chunk in file_content["chunks"]:
                if "text" in chunk:
                    content_text += chunk["text"] + "\n"
        elif file_content and "content" in file_content:
            content_text = str(file_content["content"])
        else:
            # 提供文档的基本信息而不是内容
            file_size = file_metadata.get("size", "未知")
            file_type = file_metadata.get("type", "未知")
            content_text = f"文档基本信息:\n- 文件名: {file_metadata.get('filename', '')}\n- 文件大小: {file_size} bytes\n- 文件类型: {file_type}\n- 数据库: {database_info.get('name', '')}\n\n注意: 完整内容需要通过异步方式获取，当前只显示基本信息。"
        
        return {
            "status": "success",
            "doc_id": doc_id,
            "title": file_metadata.get("filename", ""),
            "category": database_info.get("name", "") if database_info else "未知",
            "content": content_text.strip(),
            "metadata": {
                "update_date": file_metadata.get("created_at", ""),
                "file_size": file_metadata.get("size", ""),
                "file_type": file_metadata.get("type", ""),
                "database_id": database_info.get("db_id", "") if database_info else "",
                "database_name": database_info.get("name", "") if database_info else "",
                "status": file_metadata.get("status", ""),
                "path": file_metadata.get("path", "")
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取文档内容失败: {str(e)}",
            "content": None
        }


@tool
def get_latest_updates(days: int = 7, category: str = "全部") -> Dict[str, Any]:
    """获取最近更新的文档列表
    
    Args:
        days: 查询最近多少天内的更新，默认7天
        category: 文档类别，默认全部
    
    Returns:
        最近更新的文档列表
    """
    try:
        # 获取知识库管理器
        kb_manager = get_kb_manager()
        
        # 计算查询的起始日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取所有数据库
        databases = kb_manager.get_databases()
        
        # 收集所有文件
        all_files = []
        for db in databases["databases"]:
            db_id = db.get("db_id")
            db_name = db.get("name", "")
            files = db.get("files", {})
            
            # 根据类别筛选数据库
            if category != "全部":
                db_name_lower = db_name.lower()
                if category == "政策制度" and ("规范" in db_name_lower or "制度" in db_name_lower):
                    pass
                elif category == "合同范本" and ("合同" in db_name_lower or "范本" in db_name_lower):
                    pass
                else:
                    continue  # 跳过不符合类别的数据库
            
            for file_id, file_info in files.items():
                created_at_str = file_info.get("created_at", "")
                try:
                    if created_at_str:
                        # 尝试解析日期
                        if "T" in created_at_str:
                            # ISO格式时间
                            created_date = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).date()
                        else:
                            # 简单日期格式
                            created_date = datetime.strptime(created_at_str[:10], "%Y-%m-%d").date()
                        
                        # 检查是否在时间范围内
                        if start_date.date() <= created_date <= end_date.date():
                            all_files.append({
                                "doc_id": file_id,
                                "title": file_info.get("filename", ""),
                                "category": db_name,
                                "update_date": created_at_str[:10],  # 只保留日期部分
                                "update_type": "新增",  # 默认为新增
                                "description": f"文件上传到 {db_name}",
                                "author": "系统",
                                "database_id": db_id,
                                "database_name": db_name
                            })
                except Exception as e:
                    print(f"解析日期失败: {created_at_str}, 错误: {e}")
                    continue
        
        # 按更新时间排序
        all_files.sort(key=lambda x: x["update_date"], reverse=True)
        
        return {
            "status": "success",
            "query_period": f"最近{days}天",
            "category": category,
            "total_updates": len(all_files),
            "results": all_files
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"查询最新更新失败: {str(e)}",
            "results": []
        }


@tool
def full_text_search(query: str, max_results: int = 10) -> Dict[str, Any]:
    """对知识库进行全文检索
    
    Args:
        query: 检索查询语句
        max_results: 最大返回结果数量
    
    Returns:
        包含相关片段的检索结果
    """
    try:
        # 获取知识库管理器
        kb_manager = get_kb_manager()
        
        # 获取所有数据库
        databases = kb_manager.get_databases()
        all_results = []
        
        # 在每个数据库中进行全文搜索
        for db in databases["databases"]:
            db_id = db.get("db_id")
            db_name = db.get("name", "")
            
            if not db_id:
                continue
                
            try:
                # 使用知识库的同步查询功能
                results = kb_manager.query(query, db_id)
                
                # 处理搜索结果
                if isinstance(results, list):
                    for result in results:
                        content = str(result.get("content", ""))
                        title = str(result.get("title", ""))
                        
                        # 提取相关片段（简单的文本截取）
                        relevant_snippet = content[:200] + "..." if len(content) > 200 else content
                        
                        # 计算相关度分数（基于查询词在内容中的出现频率）
                        query_lower = query.lower()
                        content_lower = content.lower()
                        title_lower = title.lower()
                        
                        relevance_score = 0
                        if query_lower in title_lower:
                            relevance_score += 0.3
                        # 统计查询词在内容中的出现次数
                        content_score = content_lower.count(query_lower) * 0.1
                        relevance_score += min(content_score, 0.7)  # 限制内容分数最大为0.7
                        
                        if relevance_score > 0:
                            all_results.append({
                                "doc_id": result.get("doc_id", ""),
                                "title": title,
                                "category": db_name,
                                "relevant_snippet": relevant_snippet,
                                "relevance_score": relevance_score,
                                "context_before": f"来自数据库: {db_name}",
                                "context_after": f"文档ID: {result.get('doc_id', '')}",
                                "database_id": db_id,
                                "database_name": db_name
                            })
                
            except Exception as e:
                print(f"在数据库 {db_name} 中搜索失败: {e}")
                continue
        
        # 按相关度排序并限制结果数量
        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        limited_results = all_results[:max_results]
        
        return {
            "status": "success",
            "query": query,
            "total_found": len(all_results),
            "returned_count": len(limited_results),
            "results": limited_results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"全文检索失败: {str(e)}",
            "results": []
        }


def get_tools():
    """获取知识库查询相关工具"""
    return [
        search_knowledge_base,
        browse_knowledge_category,
        get_document_content,
        get_latest_updates,
        full_text_search,
    ]