"""
工具函数
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict
from src.state import WebGenState


def save_output(html: str, css: str, output_dir: str = "./output") -> Dict[str, str]:
    """
    保存生成的HTML和CSS到文件
    
    Returns:
        包含文件路径的字典
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = output_path / f"page_{timestamp}.html"
    css_file = output_path / f"styles_{timestamp}.css"
    
    # 将CSS嵌入到HTML中
    full_html = html.replace("</head>", f"<style>\n{css}\n</style>\n</head>")
    
    # 保存文件
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    with open(css_file, "w", encoding="utf-8") as f:
        f.write(css)
    
    return {
        "html_file": str(html_file),
        "css_file": str(css_file),
        "combined_file": str(html_file)
    }


def print_state_summary(state: WebGenState) -> None:
    """打印state的摘要信息"""
    print("\n" + "="*60)
    print("📊 执行摘要")
    print("="*60)
    
    if state.get("plan"):
        print("✅ Planning Agent: 完成")
    
    if state.get("design_spec"):
        print("✅ Design Agent: 完成")
    
    if state.get("content_data"):
        print("✅ Content Agent: 完成")
    
    if state.get("html"):
        html_lines = len(state["html"].split("\n"))
        print(f"✅ Generator Agent: 完成 (HTML: {html_lines}行)")
    
    if state.get("css"):
        css_lines = len(state["css"].split("\n"))
        print(f"   CSS: {css_lines}行")
    
    if state.get("error"):
        print(f"❌ 错误: {state['error']}")
    
    print("="*60 + "\n")