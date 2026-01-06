#!/usr/bin/env python3
"""测试纯CSS生成器"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.pure_css_generator import PureCSSGenerator

# 加载环境变量
load_dotenv()

def main():
    # 初始化LLM
    llm = ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        temperature=0.7
    )

    # 测试数据
    user_input = {
        "topic": "成都美食探险",
        "major": "烹饪艺术",
        "target_audience": "美食爱好者",
        "duration": "30分钟"
    }

    planning = {
        "course_title": "成都美食探险 - 舌尖上的川菜",
        "total_pages": 6,
        "image_page_count": 2,
        "text_only_page_count": 4,
        "pages": [
            {
                "page_num": 1,
                "type": "title",
                "layout": "center",
                "title": "成都美食探险",
                "content_brief": "课程标题和副标题",
                "key_points": ["品味川菜精髓", "探索古街美食", "体验火辣文化"]
            },
            {
                "page_num": 2,
                "type": "intro",
                "layout": "text_with_cards",
                "title": "为什么来成都吃？",
                "content_brief": "成都的美食文化介绍",
                "key_points": ["美食之都", "三千年传承", "包罗万象"],
                "image_description": "成都宽窄巷子美食街夜景",
                "image_size": "top"
            },
            {
                "page_num": 3,
                "type": "concept",
                "layout": "grid",
                "title": "川菜的灵魂 - 麻辣",
                "content_brief": "解释麻辣的四个层次",
                "key_points": ["麻-花椒", "辣-辣椒", "鲜-食材", "香-调料"]
            },
            {
                "page_num": 4,
                "type": "structure",
                "layout": "list",
                "title": "必吃的三大美食",
                "content_brief": "推荐三种必吃美食",
                "key_points": ["火锅派对", "串串香", "担担面"],
                "image_description": "成都火锅特写",
                "image_size": "side"
            },
            {
                "page_num": 5,
                "type": "warning",
                "layout": "warning_grid",
                "title": "美食注意事项",
                "content_brief": "吃辣的注意事项",
                "key_points": ["不要空腹吃太辣", "准备纸巾", "可以点微辣", "喝酸奶缓解", "慢慢吃"]
            },
            {
                "page_num": 6,
                "type": "summary",
                "layout": "summary_cards",
                "title": "成都美食之旅总结",
                "content_brief": "总结收获",
                "key_points": ["学会麻辣精髓", "知道三大美食", "掌握吃辣技巧", "准备大吃一顿"]
            }
        ]
    }

    # 生成
    generator = PureCSSGenerator(llm)

    state = {
        "user_input": user_input,
        "planning": planning
    }

    print("=" * 70)
    print("🚀 开始生成纯CSS幻灯片")
    print("=" * 70)

    start_time = datetime.now()

    result = generator.generate(state)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # 保存HTML
    if result.get('status') == 'html_generated':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/pure_css_ppt_{timestamp}.html"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['html_code'])

        print("\n" + "=" * 70)
        print("📊 生成完成")
        print("=" * 70)
        print(f"⏱️  总耗时: {duration:.2f} 秒")
        print(f"\n✅ 纯CSS课件已生成: {output_path}")
        print("\n💡 使用方法:")
        print("   1. 用浏览器打开生成的 HTML 文件")
        print("   2. 点击右下角的数字按钮切换页面")
        print("   3. 完全不依赖外部库，可离线使用")
        print("=" * 70)
    else:
        print(f"\n❌ 生成失败: {result.get('error')}")

if __name__ == "__main__":
    main()
