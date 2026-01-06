import os
import sys
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Setup path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.workflow import create_workflow
from src.state import PPTWebState
from src.utils.logger import logger

load_dotenv()

# User's exact prompt (Core Instructions + Content)
USER_PLAN = """
核心指令： 你是一位顶尖的数字课程视觉设计师。请为我制作一份严格遵循16:9比例的《土木工程建筑材料》微课PPT，以“第二章：石灰与石膏”为范本。这是外部大纲，请解析。

一、整体风格 (Overall Style)
比例： 16:9
主题： 现代工业学术风
主色调： 深蓝、浅灰、白
点缀色： 橙色

二、页面内容与布局 (16:9 Visual-First Layout)
第1页：封面页
标题： 石灰与石膏：气硬性胶凝材料的双生子
副标题： 《建筑材料》微课系列
视觉： 全屏高质量大图。图片选择：一张对比感强烈的照片，例如——左边是粗糙的石灰石墙面，右边是光滑精美的石膏装饰线条，光线从中间打下来。
布局： 标题置于图片视觉留白处，使用醒目的白色字体。

第2页：目录页
标题： 探索之旅
内容与视觉： 采用“图片墙”导航。使用四张有代表性的小图作为按钮：
1. 概念之基 (配图：干燥的墙体 vs 湿润的桥墩)
2. 烈火重生·石灰 (配图：燃烧的石灰窑或生石灰遇水沸腾)
3. 凝结艺术·石膏 (配图：精美的石膏雕塑与石膏板)
4. 双雄对决 (配图：石灰与石膏的实物并排对比)

第3页：核心概念：气硬 vs 水硬
标题： 关键区别：它们在哪里变硬？
内容： 仅保留最核心的对比关键词。
气硬性 (石灰/石膏)：空气 干燥
水硬性 (水泥)：空气+水 潮湿/水下
视觉： 左右分栏，巨幅图片对比。左侧全幅：古老的石灰抹灰建筑（如徽派建筑白墙）。右侧全幅：宏伟的水下桥梁基础或大坝施工场景。中间用简洁的文字标注区别。

第4页：石灰的诞生与挑战
标题： 石灰：从岩石到材料的蜕变
内容：
诞生： 石灰石 → 煅烧 → 生石灰
挑战： 过火石灰 —— 工程的“潜伏炸弹”
视觉： 上图下文。上部为三联图：石灰石原料 → 石灰窑外观/示意图 → 块状生石灰特写。下部重点展示一张因过火石灰导致墙体严重鼓包开裂的现场照片，极具冲击力。

第5页：石灰的“驯服”与硬化
标题： 如何“驯服”石灰？
内容：
关键步骤：熟化 (CaO + H₂O) → 特性： 高温、膨胀
安全措施：陈伏 (静置待其稳定)
获得强度： 干燥 · 结晶 · 碳化
视觉： 左图右字。左侧放置一个短视频截图或动态GIF图，展示生石灰块加水后瞬间沸腾。右侧用大号字体和图标列出三个核心概念。

第6页：石膏：温度成就的艺术
标题： 石膏：温度掌控下的魔术
内容：
魔法公式： 二水石膏 + 热 → 建筑石膏 (β-半水石膏)
魔力来源： “溶解-析晶”理论 (微观晶体交织)
视觉： 背景图+前景图。背景使用一张天然石膏矿石的晶莹剔透特写。前景上方用一个清晰的温度计刻度盘图示，高亮标出107-170°C。

第7页：石膏：为何是室内装饰之王？
标题： 石膏：室内空间的塑造者
内容： 用关键词揭示其特性与应用的因果关系。
微膨胀 & 细腻 → 棱角饱满的装饰线条
多孔 & 轻质 → 隔热隔音的石膏板
防火 & 易塑形 → 复杂的雕塑构件
视觉： 拼图式布局。页面由3-4张高质量的室内应用实景图无缝拼接而成。

第8页：终极对决：石灰 vs 石膏
标题： 终极特性对决
内容： 使用一个极简的视觉化表格。
| 特性 | 石灰 | 石膏 |
| :--- | :--- | :--- |
| 硬化 | 靠空气(CO₂) | 靠水 |
| 性格 | 慢热、收缩 | 速凝、微胀 |
| 主场 | 基础、路面 | 室内、装饰 |
视觉： 表格居中，每个单元格内可配以微小的图标。

第9页：核心知识回顾
标题： 核心知识图谱
内容： 核心知识点回顾。
视觉： 使用一张信息图风格的思维导图作为唯一视觉元素。
"""

def test_external_plan():
    print("🚀 Starting External Plan Verification...")
    
    # Init LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=0.7
    )
    
    # Create workflow
    workflow = create_workflow(llm, use_ppt_pro=True)
    app = workflow.compile()
    
    # Initial state with long topic
    state = {
        "user_input": {
            "topic": USER_PLAN,  # Pass the full plan as topic
            "major": "土木工程",
            "target_audience": "高职学生",
            "duration": "45分钟"
        },
        "planning": None,
        "html_code": None,
        "quality_issues": [],
        "iteration_count": 0,
        "final_html": None,
        "status": "pending",
        "messages": [],
        "error": None
    }
    
    # Run
    result = app.invoke(state)
    
    if result.get("status") == "completed":
        print("✅ Workflow Completed Successfully")
        html = result.get("final_html", "")
        print(f"📄 Generated HTML Length: {len(html)}")
        
        # Verify specific content markers
        checks = [
            "石灰与石膏", 
            "终极特性对决",  # Table title
            "gallery-grid", # New layout class for gallery (page 2 or 7)
            "comparison-container", # New layout class for page 8
            "compare-table"
        ]
        
        all_passed = True
        for check in checks:
            if check in html:
                print(f"   ✅ Found: {check}")
            else:
                print(f"   ❌ Missing: {check}")
                all_passed = False
                
        if all_passed:
            # Save output for user inspection
            output_path = "output/verify_external_plan.html"
            os.makedirs("output", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"💾 Saved to {output_path}")
            print(f"Wait, also check if Parser Mode was triggered.")
            
    else:
        print(f"❌ Workflow Failed: {result.get('error')}")

if __name__ == "__main__":
    test_external_plan()
