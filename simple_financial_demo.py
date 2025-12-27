#!/usr/bin/env python3
"""
FinancialReportAgent 完整功能演示
"""

import sys
import os
sys.path.insert(0, '/workspace')

from src.agents.financial_report.tools import (
    process_uploaded_financial_file,
    extract_financial_data,
    calculate_financial_ratios,
    generate_financial_charts,
    generate_financial_report
)

def demo_complete_workflow():
    """演示完整的财报分析工作流程"""
    
    print("🎯 FinancialReportAgent 完整工作流程演示")
    print("=" * 60)
    
    # 简化的测试数据（确保能正确提取）
    simple_financial_markdown = """
# 简化财务报表

## 资产负债表

| 项目 | 金额（万元） |
|------|-------------|
| 流动资产 | 10,000 |
| 非流动资产 | 20,000 |
| 总资产 | 30,000 |
| 流动负债 | 5,000 |
| 非流动负债 | 8,000 |
| 总负债 | 13,000 |
| 所有者权益 | 17,000 |

## 利润表

| 项目 | 金额（万元） |
|------|-------------|
| 营业收入 | 15,000 |
| 营业成本 | 10,000 |
| 净利润 | 2,500 |

## 现金流量表

| 项目 | 金额（万元） |
|------|-------------|
| 经营活动现金流量净额 | 4,000 |
    """

    # 步骤1: 处理上传文件
    print("\n📄 步骤1: 处理上传的财务文件")
    print("-" * 40)
    
    file_result = process_uploaded_financial_file.invoke({
        "file_content": simple_financial_markdown,
        "file_name": "简化财报.pdf",
        "file_type": "pdf"
    })
    
    print(f"✅ 文件处理状态: {file_result['status']}")
    print(f"📊 提取表格数量: {file_result['table_count']}")
    
    # 步骤2: 提取财务指标
    print("\n🔍 步骤2: 提取关键财务指标")
    print("-" * 40)
    
    extracted_data = extract_financial_data.invoke({
        "text_content": file_result['text_content'],
        "tables": file_result['tables'],
        "metrics": ["revenue", "net_profit", "total_assets", "total_liabilities", 
                   "current_assets", "current_liabilities", "total_equity", "operating_cash_flow"]
    })
    
    print(f"✅ 数据提取状态: {extracted_data['status']}")
    
    metrics = extracted_data.get('extracted_metrics', {})
    valid_metrics = {k: v for k, v in metrics.items() if v is not None}
    
    if valid_metrics:
        print(f"📈 成功提取 {len(valid_metrics)} 个财务指标:")
        for metric, value in valid_metrics.items():
            print(f"  - {metric}: {value:,} 万元")
    else:
        print("❌ 没有提取到有效财务指标")
        # 手动添加测试数据继续演示
        valid_metrics = {
            "revenue": 15000.0,
            "net_profit": 2500.0,
            "total_assets": 30000.0,
            "total_liabilities": 13000.0,
            "current_assets": 10000.0,
            "current_liabilities": 5000.0,
            "total_equity": 17000.0,
            "operating_cash_flow": 4000.0
        }
        print("🔧 使用测试数据继续演示...")
        extracted_data['extracted_metrics'] = valid_metrics
    
    # 步骤3: 计算财务比率
    print("\n📊 步骤3: 计算财务比率")
    print("-" * 40)
    
    ratios_result = calculate_financial_ratios.invoke({
        "financial_data": extracted_data
    })
    
    print(f"✅ 比率计算状态: {ratios_result['status']}")
    
    if ratios_result['status'] == 'success':
        all_ratios = {}
        for category in ['profitability_ratios', 'solvency_ratios', 'operational_ratios', 'growth_ratios']:
            all_ratios.update(ratios_result.get(category, {}))
        
        if all_ratios:
            print("📈 计算得出的财务比率:")
            for ratio_name, ratio_value in all_ratios.items():
                if ratio_value is not None:
                    if isinstance(ratio_value, float):
                        print(f"  - {ratio_name}: {ratio_value:.2f}%")
                    else:
                        print(f"  - {ratio_name}: {ratio_value}")
        else:
            print("⚠️ 没有计算出有效比率")
    else:
        print(f"❌ 比率计算失败: {ratios_result.get('error', '未知错误')}")
    
    # 步骤4: 生成图表
    print("\n📈 步骤4: 生成分析图表")
    print("-" * 40)
    
    charts_result = generate_financial_charts.invoke({
        "financial_data": extracted_data,
        "chart_type": "bar",
        "chart_theme": "professional",
        "chart_size": "medium",
        "metrics": ["revenue", "net_profit", "total_assets", "total_equity"]
    })
    
    print(f"✅ 图表生成状态: {charts_result['status']}")
    
    if charts_result['status'] == 'success' and charts_result.get('charts'):
        print(f"📊 生成图表数量: {len(charts_result['charts'])}")
        for chart in charts_result['charts']:
            print(f"  - {chart.get('chart_type', '未知类型')}: {chart.get('title', '无标题')}")
    else:
        print("⚠️ 图表生成失败或无图表数据")
    
    # 步骤5: 生成报告
    print("\n📋 步骤5: 生成完整分析报告")
    print("-" * 40)
    
    report_result = generate_financial_report.invoke({
        "financial_data": extracted_data,
        "ratios": ratios_result.get('profitability_ratios', {}) if ratios_result['status'] == 'success' else {},
        "charts": charts_result.get('charts', []) if charts_result['status'] == 'success' else [],
        "analysis_dimensions": ["profitability", "solvency"],
        "company_name": "演示股份有限公司",
        "report_period": "2023年度"
    })
    
    print(f"✅ 报告生成状态: {report_result['status']}")
    
    if report_result['status'] == 'success':
        content = report_result.get('content', '')
        print(f"📄 报告长度: {len(content)} 字符")
        
        # 显示报告摘要
        if content:
            lines = content.split('\n')[:20]  # 显示前20行
            print("\n📋 报告预览:")
            print("-" * 40)
            for line in lines:
                if line.strip():
                    print(line)
            if len(content.split('\n')) > 20:
                print("...（更多内容）")
    else:
        print(f"❌ 报告生成失败: {report_result.get('error', '未知错误')}")
    
    print("\n" + "=" * 60)
    print("🎉 FinancialReportAgent 功能演示完成!")
    print("💡 功能包括: 文件处理 → 数据提取 → 比率计算 → 图表生成 → 报告输出")
    print("🔧 支持的文件类型: PDF, Excel, Word, 图片等")

if __name__ == "__main__":
    demo_complete_workflow()