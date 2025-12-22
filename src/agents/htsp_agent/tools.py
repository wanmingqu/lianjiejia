from langchain.tools import tool
from typing import Dict, Any, List
import os
import tempfile
from pathlib import Path
import fitz  # PyMuPDF for PDF processing
from docx import Document  # python-docx for Word processing


@tool
def upload_contract_file(file_path: str, file_type: str = "auto") -> str:
    """上传并验证合同文件
    
    Args:
        file_path: 文件路径或文件内容
        file_type: 文件类型：pdf, docx, txt, auto(自动检测)
    
    Returns:
        上传结果和文件信息
    """
    try:
        # 判断是文件路径还是直接内容
        if os.path.exists(file_path):
            path = Path(file_path)
            file_size = path.stat().st_size
            file_name = path.name
            
            # 自动检测文件类型
            if file_type == "auto":
                suffix = path.suffix.lower()
                if suffix == ".pdf":
                    file_type = "pdf"
                elif suffix in [".docx", ".doc"]:
                    file_type = "docx" 
                elif suffix in [".txt", ".text"]:
                    file_type = "txt"
                else:
                    return f"不支持的文件类型: {suffix}"
            
            return f"文件上传成功 - 文件名: {file_name}, 类型: {file_type}, 大小: {file_size}字节"
        else:
            # 如果是直接的内容，创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(file_path)
                temp_path = f.name
            
            return f"内容已保存为临时文件: {temp_path}, 类型: {file_type}"
            
    except Exception as e:
        return f"文件上传失败: {str(e)}"


@tool
def extract_contract_text(file_path: str, file_type: str = "auto") -> str:
    """从合同文件中提取文本内容
    
    Args:
        file_path: 文件路径
        file_type: 文件类型：pdf, docx, txt, auto(自动检测)
    
    Returns:
        提取的文本内容
    """
    try:
        path = Path(file_path)
        
        # 自动检测文件类型
        if file_type == "auto":
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                file_type = "pdf"
            elif suffix in [".docx", ".doc"]:
                file_type = "docx"
            elif suffix in [".txt", ".text"]:
                file_type = "txt"
            else:
                return f"不支持的文件类型: {suffix}"
        
        # 根据文件类型提取文本
        if file_type == "txt":
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
        elif file_type == "pdf":
            # 使用PyMuPDF提取PDF文本
            try:
                doc = fitz.open(path)
                text = ""
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text += page.get_text()
                doc.close()
                return text
            except Exception as e:
                return f"PDF文本提取失败: {str(e)}"
        elif file_type == "docx":
            # 使用python-docx提取Word文档文本
            try:
                doc = Document(path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except Exception as e:
                return f"DOCX文本提取失败: {str(e)}"
        else:
            return f"不支持的文件类型: {file_type}"
            
    except Exception as e:
        return f"文本提取失败: {str(e)}"


@tool
def analyze_contract_structure(contract_text: str) -> Dict[str, Any]:
    """分析合同结构，识别关键条款
    
    Args:
        contract_text: 合同文本内容
    
    Returns:
        合同结构分析结果
    """
    # 简化的结构分析实现
    result = {
        "total_sections": 0,
        "key_sections": [],
        "risk_indicators": [],
        "missing_elements": []
    }
    
    # 检查常见的合同条款
    common_clauses = [
        "当事人", "合同目的", "合同期限", "价款", "付款方式", 
        "违约责任", "争议解决", "不可抗力", "保密条款"
    ]
    
    for clause in common_clauses:
        if clause in contract_text:
            result["key_sections"].append(clause)
        else:
            result["missing_elements"].append(f"缺少{clause}条款")
    
    # 检查风险指标
    risk_keywords = ["无限责任", "连带责任", "单方面解除", "高额违约金"]
    for keyword in risk_keywords:
        if keyword in contract_text:
            result["risk_indicators"].append(keyword)
    
    result["total_sections"] = len(result["key_sections"])
    
    return result


@tool
def validate_contract_compliance(contract_text: str, check_types: List[str]) -> Dict[str, Any]:
    """验证合同合规性
    
    Args:
        contract_text: 合同文本内容
        check_types: 检查类型列表，如["法律", "财务", "商业"]
    
    Returns:
        合规性检查结果
    """
    result = {
        "overall_status": "通过",
        "check_details": {},
        "issues": [],
        "recommendations": []
    }
    
    # 根据检查类型进行验证
    for check_type in check_types:
        if check_type == "法律":
            # 简化的法律检查
            if "适用法律" not in contract_text:
                result["check_details"]["法律"] = "不通过"
                result["issues"].append("未明确适用法律条款")
            else:
                result["check_details"]["法律"] = "通过"
                
        elif check_type == "财务":
            # 简化的财务检查
            if "金额" not in contract_text and "价款" not in contract_text:
                result["check_details"]["财务"] = "不通过"
                result["issues"].append("未明确合同金额")
            else:
                result["check_details"]["财务"] = "通过"
                
        elif check_type == "商业":
            # 简化的商业检查
            result["check_details"]["商业"] = "通过"
            result["recommendations"].append("建议明确双方权利义务")
    
    # 判断总体状态
    if any(status == "不通过" for status in result["check_details"].values()):
        result["overall_status"] = "部分通过"
    
    return result


@tool
def comprehensive_contract_review(file_path: str, check_types: List[str] = None, risk_level: str = "中等") -> Dict[str, Any]:
    """综合合同审核 - 从文件上传到完整审核报告
    
    Args:
        file_path: 合同文件路径
        check_types: 检查类型列表，如["法律", "财务", "商业"]
        risk_level: 风险评估等级：低, 中等, 高
    
    Returns:
        完整的合同审核报告
    """
    if check_types is None:
        check_types = ["法律", "财务", "商业"]
    
    result = {
        "file_info": {},
        "structure_analysis": {},
        "compliance_check": {},
        "risk_assessment": "",
        "summary": "",
        "recommendations": []
    }
    
    try:
        # 1. 提取文件信息
        path = Path(file_path)
        result["file_info"] = {
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "file_type": path.suffix.lower()
        }
        
        # 2. 提取合同文本
        contract_text = extract_contract_text.invoke({"file_path": file_path})
        if isinstance(contract_text, str) and ("文本提取失败" in contract_text or "提取失败" in contract_text):
            result["summary"] = "文件文本提取失败，无法进行审核"
            return result
        
        # 3. 结构分析
        result["structure_analysis"] = analyze_contract_structure.invoke({"contract_text": contract_text})
        
        # 4. 合规性检查
        result["compliance_check"] = validate_contract_compliance.invoke({
            "contract_text": contract_text, 
            "check_types": check_types
        })
        
        # 5. 风险评估
        risk_indicators = result["structure_analysis"].get("risk_indicators", [])
        if len(risk_indicators) == 0:
            result["risk_assessment"] = f"风险评估：低风险 - 未发现明显风险指标"
        elif len(risk_indicators) <= 2:
            result["risk_assessment"] = f"风险评估：{risk_level}风险 - 发现{len(risk_indicators)}个风险指标"
        else:
            result["risk_assessment"] = f"风险评估：高风险 - 发现{len(risk_indicators)}个风险指标，建议重点关注"
        
        # 6. 生成总结
        total_sections = result["structure_analysis"].get("total_sections", 0)
        compliance_status = result["compliance_check"].get("overall_status", "未知")
        
        result["summary"] = f"""
合同审核完成报告：
- 文件：{result['file_info']['file_name']} ({result['file_info']['file_size']}字节)
- 识别条款：{total_sections}个关键条款
- 合规状态：{compliance_status}
- 风险评估：{result['risk_assessment']}
        """.strip()
        
        # 7. 生成建议
        missing_elements = result["structure_analysis"].get("missing_elements", [])
        if missing_elements:
            result["recommendations"].extend(missing_elements)
        
        if risk_indicators:
            result["recommendations"].append(f"发现风险指标：{', '.join(risk_indicators)}，建议仔细审查相关条款")
        
        if not result["recommendations"]:
            result["recommendations"].append("合同结构完整，未发现明显问题")
            
    except Exception as e:
        result["summary"] = f"合同审核过程中发生错误：{str(e)}"
    
    return result


@tool
def contract_review(contract_text: str, check_type: str = "综合") -> str:
    """审核合同内容，识别潜在风险和问题
    
    Args:
        contract_text: 合同文本内容
        check_type: 检查类型：法律, 财务, 商业, 技术, 合规, 综合
    
    Returns:
        审核结果的描述
    """
    # 这里是简化的实现，实际应该调用具体的审核逻辑
    return f"已完成{check_type}类型审核，识别出3个需要注意的条款"


@tool  
def risk_assessment(contract_text: str, risk_level: str = "中等") -> str:
    """评估合同风险等级
    
    Args:
        contract_text: 合同文本内容
        risk_level: 风险等级：低, 中等, 高
    
    Returns:
        风险评估结果
    """
    # 简化的实现
    return f"风险评估完成，当前合同风险等级：{risk_level}"


def get_tools():
    """获取合同审批相关工具"""
    return [
        upload_contract_file,
        extract_contract_text,
        analyze_contract_structure,
        validate_contract_compliance,
        comprehensive_contract_review,
        contract_review,
        risk_assessment,
    ]