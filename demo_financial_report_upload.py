#!/usr/bin/env python3
"""
FinancialReportAgent文件上传功能演示

展示财报分析Agent如何处理用户上传的财务报表文件
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

def demo_financial_report_processing():
    """演示财报处理流程"""
    
    print("🎯 FinancialReportAgent 文件处理功能演示")
    print("=" * 60)
    
    # 模拟用户上传PDF财报文件后转换的markdown内容
    sample_financial_report_md = """
# XX股份有限公司2023年度财务报表

## 资产负债表
（单位：万元）

| 项目 | 2023年12月31日 | 2022年12月31日 |
|------|---------------|---------------|
| **流动资产** | | |
| 货币资金 | 8,500 | 7,200 |
| 应收账款 | 3,200 | 2,800 |
| 存货 | 4,500 | 4,000 |
| 其他流动资产 | 800 | 600 |
| **流动资产合计** | **17,000** | **14,600** |
| | | |
| **非流动资产** | | |
| 固定资产 | 25,000 | 23,000 |
| 无形资产 | 3,000 | 2,800 |
| **非流动资产合计** | **28,000** | **25,800** |
| | | |
| **资产总计** | **45,000** | **40,400** |
| | | |
| **流动负债** | | |
| 短期借款 | 2,500 | 2,200 |
| 应付账款 | 3,000 | 2,600 |
| **流动负债合计** | **5,500** | **4,800** |
| | | |
| **非流动负债** | | |
| 长期借款 | 8,000 | 7,500 |
| **非流动负债合计** | **8,000** | **7,500** |
| | | |
| **负债合计** | **13,500** | **12,300** |
| | | |
| **所有者权益** | | |
| 实收资本 | 20,000 | 18,000 |
| 资本公积 | 5,000 | 4,500 |
| 未分配利润 | 6,500 | 5,600 |
| **所有者权益合计** | **31,500** | **28,100** |
| | | |
| **负债和所有者权益总计** | **45,000** | **40,400** |

## 利润表
（单位：万元）

| 项目 | 2023年度 | 2022年度 |
|------|----------|----------|
| 营业收入 | 35,000 | 30,000 |
| 营业成本 | 22,000 | 19,500 |
| 营业税金及附加 | 1,200 | 1,000 |
| 销售费用 | 3,000 | 2,800 |
| 管理费用 | 2,500 | 2,300 |
| 财务费用 | 800 | 700 |
| 营业利润 | 5,500 | 3,700 |
| 利润总额 | 5,800 | 3,900 |
| 净利润 | 4,900 | 3,200 |

## 现金流量表
（单位：万元）

| 项目 | 2023年度 | 2022年度 |
|------|----------|----------|
| 经营活动现金流量净额 | 6,200 | 4,800 |
| 投资活动现金流量净额 | -3,500 | -2,800 |
| 筹资活动现金流量净额 | -1,200 | -800 |
| **现金及现金等价物净增加额** | **1,500** | **1,200** |
    """

    # 步骤1: 处理上传的财务文件
    print("\n📄 步骤1: 处理上传的财务文件")
    print("-" * 40)
    
    file_result = process_uploaded_financial_file.invoke({
        "file_content": sample_financial_report_md,
        "file_name": "XX股份2023年财报.pdf",
        "file_type": "pdf",
        "extract_tables": True,
        "extract_text": True
    })
    
    print(f"✅ 文件处理状态: {file_result['status']}")
    print(f"📊 提取表格数量: {file_result['table_count']}")
    print(f"📄 文本内容长度: {len(file_result['text_content'])} 字符")
    
    if file_result['tables']:
        print(f"📋 第一个表格列名: {file_result['tables'][0]['columns']}")
        print(f"📊 第一个表格数据行数: {file_result['tables'][0]['row_count']}")
    
    # 步骤2: 提取关键财务指标
    print("\n🔍 步骤2: 提取关键财务指标")
    print("-" * 40)
    
    financial_metrics = [
        "revenue", "net_profit", "total_assets", "total_liabilities",
        "current_assets", "current_liabilities", "total_equity",
        "operating_cash_flow"
    ]
    
    extracted_data = extract_financial_data.invoke({
        "text_content": file_result['text_content'],
        "tables": file_result['tables'],
        "metrics": financial_metrics
    })
    
    print(f"✅ 数据提取状态: {extracted_data['status']}")
    print(f"📈 提取的财务指标:")
    
    metrics = extracted_data.get('extracted_metrics', {})
    for metric, value in metrics.items():
        if value is not None:
            print(f"  - {metric}: {value:,} 万元")
        else:
            print(f"  - {metric}: 未提取到")
    
    if not metrics:
        print("  - 没有提取到财务指标数据")
    else:
        print(f"  - 总共提取到 {len([v for v in metrics.values() if v is not None])} 个有效指标")
    
    # 步骤3: 计算财务比率
    print("\n📊 步骤3: 计算财务比率")
    print("-" * 40)
    
    ratios_result = calculate_financial_ratios.invoke({
        "financial_data": extracted_data
    })
    
    print(f"✅ 比率计算状态: {ratios_result['status']}")
    
    if ratios_result['status'] == 'success':
        print("📈 关键财务比率:")
        all_ratios = {}
        all_ratios.update(ratios_result.get('profitability_ratios', {}))
        all_ratios.update(ratios_result.get('solvency_ratios', {}))
        all_ratios.update(ratios_result.get('operational_ratios', {}))
        all_ratios.update(ratios_result.get('growth_ratios', {}))
        
        for ratio_name, ratio_value in all_ratios.items():
            if ratio_value is not None:
                if isinstance(ratio_value, float):
                    print(f"  - {ratio_name}: {ratio_value:.2f}%")
                else:
                    print(f"  - {ratio_name}: {ratio_value}")
    
    # 步骤4: 生成分析图表
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
    
    if charts_result['status'] == 'success' and charts_result['charts']:
        print(f"📊 生成图表数量: {len(charts_result['charts'])}")
        for chart in charts_result['charts']:
            print(f"  - {chart['chart_type']}: {chart.get('title', '无标题')}")
            if chart.get('image_url'):
                print(f"    📷 图表URL: {chart['image_url'][:50]}...")
    
    # 步骤5: 生成完整分析报告
    print("\n📋 步骤5: 生成完整分析报告")
    print("-" * 40)
    
    report_result = generate_financial_report.invoke({
        "financial_data": extracted_data,
        "ratios": ratios_result['ratios'] if ratios_result['status'] == 'success' else {},
        "charts": charts_result['charts'] if charts_result['status'] == 'success' else [],
        "analysis_dimensions": ["profitability", "solvency", "operation", "growth", "cash_flow"],
        "company_name": "XX股份有限公司",
        "report_period": "2023年度"
    })
    
    print(f"✅ 报告生成状态: {report_result['status']}")
    
    if report_result['status'] == 'success':
        print(f"📄 报告长度: {len(report_result['content'])} 字符")
        print("\n📋 报告预览 (前300字符):")
        print("-" * 40)
        print(report_result['content'][:300] + "...")
    
    print("\n" + "=" * 60)
    print("🎉 FinancialReportAgent 文件处理演示完成!")
    print("💡 支持的文件类型: PDF, Excel, Word, 图片等")
    print("🔧 主要功能: 数据提取 → 比率计算 → 图表生成 → 报告输出")

if __name__ == "__main__":
    demo_financial_report_processing()