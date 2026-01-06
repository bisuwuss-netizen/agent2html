"""
测试创意布局系统
演示歪斜图片、不规则排列等视觉效果
"""
import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def save_html(html_code: str, filename: str = None) -> str:
    """保存 HTML 到文件"""
    if not filename:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"creative_ppt_{timestamp}.html"

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_code)

    return filepath


def main():
    """主函数"""

    print("\n" + "="*70)
    print("🎨 测试创意布局系统")
    print("   - 歪斜图片（旋转 -3° 到 3°）")
    print("   - 不规则排列")
    print("   - 卡片、拼贴、网格等多种布局")
    print("="*70)

    # 初始化 LLM
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4"),
        temperature=float(os.getenv("TEMPERATURE", 0.7)),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_BASE_URL")
    )

    # 使用创意生成器
    from src.agents.creative_generator import CreativeGenerator

    # 测试数据
    user_input = {
        "topic": "成都美食探险",
        "major": "烹饪艺术",
        "target_audience": "美食爱好者",
        "duration": "30分钟"
    }

    # 模拟 planning（带创意布局）
    planning = {
        "course_title": "成都美食探险 - 舌尖上的川菜",
        "total_pages": 6,
        "theme_suggestion": "暖色橙红色系",
        "image_page_count": 3,
        "text_only_page_count": 3,
        "pages": [
            {
                "page_num": 1,
                "type": "title",
                "title": "成都美食探险",
                "content": ["品味川菜精髓", "探索古街美食", "体验火辣文化"],
                "layout": "center",
                "visual_emphasis": "标题要大，副标题醒目"
            },
            {
                "page_num": 2,
                "type": "intro",
                "title": "为什么来成都吃？",
                "content": "成都被誉为'美食之都'，拥有三千年饮食文化积淀。从街边小吃到高档餐厅，从麻辣火锅到清淡甜点，成都美食包罗万象，是吃货的天堂！",
                "layout": "top_image_center",
                "visual_emphasis": "图片要吸引人",
                "image_description": "成都宽窄巷子美食街夜景，红灯笼高挂，游客如织，烟火气十足",
                "image_size": "top"
            },
            {
                "page_num": 3,
                "type": "concept",
                "title": "川菜的灵魂 - 麻辣",
                "content": ["麻：花椒带来的麻麻感觉", "辣：辣椒的层次辣味", "鲜：食材的本味", "香：复合调料的香气"],
                "layout": "text_with_bullets",
                "visual_emphasis": "重点词汇用红色"
            },
            {
                "page_num": 4,
                "type": "structure",
                "title": "必吃的三大美食",
                "content": ["火锅派对：红红的汤锅里煮着牛肉、蔬菜，蘸香油超美味！", "串串香：竹签串着肉丸、豆腐，边走边吃像参加美食节！", "担担面：细面条拌上花生酱和辣椒油，一口下去，香喷喷！"],
                "layout": "left_text_right_image",
                "visual_emphasis": "美食名称用粗体",
                "image_description": "成都火锅特写，红油翻滚，食材丰富，烟雾缭绕",
                "image_size": "side"
            },
            {
                "page_num": 5,
                "type": "warning",
                "title": "美食注意事项",
                "content": ["不要空腹吃太辣，容易胃疼", "记得准备纸巾，会流汗哦", "怕辣的话可以点微辣", "喝点酸奶能缓解辣味", "慢慢吃，别烫到舌头"],
                "layout": "warning_grid",
                "visual_emphasis": "警告用红色卡片"
            },
            {
                "page_num": 6,
                "type": "summary",
                "title": "成都美食之旅总结",
                "content": ["学会了麻辣的精髓", "知道了三大必吃美食", "掌握了吃辣技巧", "下次去成都，准备大吃一顿！"],
                "layout": "summary_boxes",
                "visual_emphasis": "总结要清晰"
            }
        ]
    }

    print("\n📋 课程信息：")
    print(f"   主题：{user_input['topic']}")
    print(f"   总页数：{planning['total_pages']}")
    print(f"   有图页面：{planning.get('image_page_count', 0)}")
    print("="*70)

    # 初始化状态
    from src.state import PPTWebState

    initial_state: PPTWebState = {
        "user_input": user_input,
        "planning": planning,
        "html_code": None,
        "quality_issues": [],
        "iteration_count": 0,
        "final_html": None,
        "status": "pending",
        "execution_time": None,
        "messages": [],
        "error": None,
        "generated_images": {}  # 暂不使用真实图片
    }

    # 执行创意生成
    print("\n🚀 开始生成创意页面...\n")

    start_time = time.time()

    try:
        generator = CreativeGenerator(llm, max_workers=4)
        final_state = generator.generate_with_images(initial_state)
        execution_time = time.time() - start_time

        # 显示结果
        print("\n" + "="*70)
        print("📊 生成完成")
        print("="*70)
        print(f"⏱️  总耗时: {execution_time:.2f} 秒")

        # 保存文件
        html_to_save = final_state.get("html_code")
        if html_to_save:
            filepath = save_html(html_to_save)
            print(f"\n✅ 创意课件已生成: {filepath}")

            # 统计创意元素
            rotate_count = html_to_save.count('rotate(')
            shadow_count = html_to_save.count('box-shadow')

            print(f"\n🎨 创意元素统计:")
            print(f"   旋转效果: {rotate_count} 处")
            print(f"   阴影效果: {shadow_count} 处")

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n💡 使用方法:")
    print("   1. 用浏览器打开生成的 HTML 文件")
    print("   2. 按 F11 进入全屏模式")
    print("   3. 使用 ← → 键或空格键翻页")
    print("   4. 观察图片的旋转、阴影等创意效果\n")
    print("="*70)


if __name__ == "__main__":
    main()
