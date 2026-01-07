"""
批量JSON到HTML测试脚本
直接使用预定义的JSON数据生成HTML，无需LLM调用
覆盖6个学科类别 + 展示19种不同布局
"""
import os
import sys
import time
import json
import uuid
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.generator import HTMLGenerator
from src.agents.layouts import _determine_subject_category

# 可用的19种布局模板
# P0: cover, timeline, cards_3col, cards_4col, image_wall_2x2, image_wall_2x3
# P1: quote, stats, process_flow, before_after
# P2: masonry, circular, pyramid
# 基础: split, top_image, steps, warning, summary, comparison

# 6个学科的完整JSON测试数据 - 每个科目展示不同布局
SUBJECT_TEST_DATA = [
    # 1. 医护类 (medical) - 重点展示: steps, warning, process_flow
    {
        "major": "护理学",
        "category": "medical",
        "data": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "teaching_request": {
                "subject": "护理学 静脉输液操作规范",
                "knowledge_points": ["静脉输液操作规范"],
                "teaching_scene": "practice",
                "slide_count": 8
            },
            "style_config": {
                "style_name": "medical_clean",
                "color": {
                    "primary": "#16a085",
                    "secondary": "#1abc9c",
                    "accent": "#3498db",
                    "text": "#ecf0f1",
                    "background": "#0d1f2d",
                    "warning": "#e74c3c"
                }
            },
            "deck_content": {
                "deck_title": "护理学：静脉输液操作规范",
                "pages": [
                    {
                        "index": 1, "page_num": 1,
                        "slide_type": "cover",
                        "title": "静脉输液操作规范",
                        "layout": {"template": "cover"},
                        "content": ["护理学专业核心技能", "授课人：___"]
                    },
                    {
                        "index": 2, "page_num": 2,
                        "slide_type": "quote",
                        "title": "护理的艺术在于细节，安全的保障在于规范",
                        "subtitle": "南丁格尔",
                        "layout": {"template": "quote"},
                        "content": []
                    },
                    {
                        "index": 3, "page_num": 3,
                        "slide_type": "stats",
                        "title": "临床数据",
                        "layout": {"template": "stats"},
                        "content": [
                            "98%：规范操作成功率",
                            "3秒：标准消毒时间",
                            "15-60：正常滴速范围",
                            "0.1%：不良反应发生率"
                        ]
                    },
                    {
                        "index": 4, "page_num": 4,
                        "slide_type": "process",
                        "title": "输液操作流程",
                        "layout": {"template": "process_flow"},
                        "content": [
                            "核对医嘱",
                            "准备用物", 
                            "选择穿刺部位",
                            "消毒穿刺",
                            "固定调速"
                        ]
                    },
                    {
                        "index": 5, "page_num": 5,
                        "slide_type": "steps",
                        "title": "详细操作步骤",
                        "layout": {"template": "steps"},
                        "content": [
                            "第一步：核对医嘱，准备用物（输液器、药液、消毒棉签）",
                            "第二步：选择穿刺部位，常选手背静脉",
                            "第三步：扎止血带，消毒皮肤直径≥5cm",
                            "第四步：穿刺进针，见回血后松止血带",
                            "第五步：固定针头，调节滴速",
                            "第六步：观察患者反应，做好记录"
                        ]
                    },
                    {
                        "index": 6, "page_num": 6,
                        "slide_type": "warning",
                        "title": "⚠️ 安全警示",
                        "layout": {"template": "warning"},
                        "content": [
                            "严格执行三查八对制度",
                            "检查药液质量和有效期",
                            "密切观察输液反应",
                            "发现问题立即停止并报告",
                            "做好无菌操作"
                        ]
                    },
                    {
                        "index": 7, "page_num": 7,
                        "slide_type": "before_after",
                        "title": "规范操作对比",
                        "layout": {"template": "before_after"},
                        "content": [
                            "消毒不彻底",
                            "未核对患者信息",
                            "滴速调节不当",
                            "规范消毒≥5cm",
                            "三查八对到位",
                            "精准调节滴速"
                        ]
                    },
                    {
                        "index": 8, "page_num": 8,
                        "slide_type": "summary",
                        "title": "本节总结",
                        "layout": {"template": "summary"},
                        "content": [
                            "掌握静脉输液完整操作流程",
                            "三查八对是安全核心",
                            "无菌操作贯穿始终",
                            "密切观察患者反应"
                        ]
                    }
                ]
            }
        }
    },
    # 2. 工科类 (engineering) - 重点展示: timeline, comparison, split
    {
        "major": "机械制造",
        "category": "engineering",
        "data": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "teaching_request": {
                "subject": "机械制造 数控车床编程基础",
                "knowledge_points": ["数控车床编程"],
                "teaching_scene": "theory",
                "slide_count": 8
            },
            "style_config": {
                "style_name": "engineering_precise",
                "color": {
                    "primary": "#2980b9",
                    "secondary": "#3498db",
                    "accent": "#f39c12",
                    "text": "#ecf0f1",
                    "background": "#1a252f",
                    "warning": "#e74c3c"
                }
            },
            "deck_content": {
                "deck_title": "机械制造：数控车床编程基础",
                "pages": [
                    {
                        "index": 1, "page_num": 1,
                        "slide_type": "cover",
                        "title": "数控车床编程基础",
                        "layout": {"template": "cover"},
                        "content": ["机械制造专业", "CNC加工核心技能"]
                    },
                    {
                        "index": 2, "page_num": 2,
                        "slide_type": "cards_4col",
                        "title": "数控加工四大要素",
                        "layout": {"template": "cards_4col"},
                        "content": [
                            "程序：G/M代码指令",
                            "机床：数控车床硬件",
                            "刀具：刀具选型与补偿",
                            "工艺：加工工艺规划"
                        ]
                    },
                    {
                        "index": 3, "page_num": 3,
                        "slide_type": "timeline",
                        "title": "G代码发展历程",
                        "layout": {"template": "timeline"},
                        "content": [
                            "1950年代：MIT开发第一代NC系统",
                            "1970年代：CNC数控系统普及",
                            "1990年代：CAD/CAM集成编程",
                            "2010年代：智能加工与仿真",
                            "2020年代：AI辅助编程优化"
                        ]
                    },
                    {
                        "index": 4, "page_num": 4,
                        "slide_type": "comparison",
                        "title": "常用G代码对比",
                        "layout": {"template": "comparison"},
                        "content": [
                            "代码｜功能｜说明",
                            "G00｜快速定位｜刀具快速移动到指定位置",
                            "G01｜直线插补｜切削进给直线运动",
                            "G02｜顺时针圆弧｜顺时针圆弧插补",
                            "G03｜逆时针圆弧｜逆时针圆弧插补",
                            "G71｜外圆粗车｜外圆粗车循环"
                        ]
                    },
                    {
                        "index": 5, "page_num": 5,
                        "slide_type": "split",
                        "title": "坐标系建立",
                        "layout": {"template": "split"},
                        "content": [
                            "机床坐标系：机床固有原点",
                            "工件坐标系：G54-G59设定",
                            "编程坐标系：绝对/增量坐标",
                            "刀具补偿点：T01-T12刀位"
                        ],
                        "image_description": "数控车床坐标系示意图"
                    },
                    {
                        "index": 6, "page_num": 6,
                        "slide_type": "circular",
                        "title": "编程核心要素",
                        "subtitle": "CNC",
                        "layout": {"template": "circular"},
                        "content": [
                            "G代码",
                            "M代码",
                            "坐标系",
                            "刀具补偿",
                            "进给速度",
                            "主轴转速"
                        ]
                    },
                    {
                        "index": 7, "page_num": 7,
                        "slide_type": "pyramid",
                        "title": "编程技能层次",
                        "layout": {"template": "pyramid"},
                        "content": [
                            "高级：复杂轮廓宏程序",
                            "中级：循环指令应用",
                            "基础：G代码直接编程",
                            "入门：程序结构理解"
                        ]
                    },
                    {
                        "index": 8, "page_num": 8,
                        "slide_type": "summary",
                        "title": "课程总结",
                        "layout": {"template": "summary"},
                        "content": [
                            "掌握G代码基本指令",
                            "理解坐标系建立方法",
                            "学会简单程序编写",
                            "了解刀具补偿原理"
                        ]
                    }
                ]
            }
        }
    },
    # 3. 艺术设计类 (arts) - 重点展示: image_wall, masonry, gallery
    {
        "major": "视觉设计",
        "category": "arts",
        "data": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "teaching_request": {
                "subject": "视觉设计 平面设计构图原则",
                "knowledge_points": ["构图原则"],
                "teaching_scene": "theory",
                "slide_count": 8
            },
            "style_config": {
                "style_name": "arts_creative",
                "color": {
                    "primary": "#9b59b6",
                    "secondary": "#8e44ad",
                    "accent": "#e74c3c",
                    "text": "#ecf0f1",
                    "background": "#1a1a2e",
                    "warning": "#f39c12"
                }
            },
            "deck_content": {
                "deck_title": "视觉设计：平面设计构图原则",
                "pages": [
                    {
                        "index": 1, "page_num": 1,
                        "slide_type": "cover",
                        "title": "平面设计构图原则",
                        "layout": {"template": "cover"},
                        "content": ["视觉设计基础", "创意与美学的融合"]
                    },
                    {
                        "index": 2, "page_num": 2,
                        "slide_type": "quote",
                        "title": "设计不是装饰，而是解决问题的过程",
                        "subtitle": "原研哉",
                        "layout": {"template": "quote"},
                        "content": []
                    },
                    {
                        "index": 3, "page_num": 3,
                        "slide_type": "image_wall",
                        "title": "经典构图形式",
                        "layout": {"template": "image_wall_2x2"},
                        "content": [
                            "对称构图：稳重庄严",
                            "对角线构图：动感张力",
                            "三分法构图：视觉平衡",
                            "环形构图：聚焦包围"
                        ]
                    },
                    {
                        "index": 4, "page_num": 4,
                        "slide_type": "masonry",
                        "title": "优秀海报设计案例",
                        "layout": {"template": "masonry"},
                        "content": [
                            "极简主义风格",
                            "孟菲斯设计",
                            "瑞士国际风格",
                            "日式美学",
                            "波普艺术",
                            "包豪斯风格"
                        ]
                    },
                    {
                        "index": 5, "page_num": 5,
                        "slide_type": "image_wall",
                        "title": "色彩搭配方案",
                        "layout": {"template": "image_wall_2x3"},
                        "content": [
                            "互补色：强烈对比",
                            "类似色：和谐统一",
                            "三角色：丰富平衡",
                            "分裂互补：活泼协调",
                            "单色系：简洁高级",
                            "自然配色：舒适自然"
                        ]
                    },
                    {
                        "index": 6, "page_num": 6,
                        "slide_type": "split",
                        "title": "黄金分割法则",
                        "layout": {"template": "split"},
                        "content": [
                            "黄金比例：1:1.618",
                            "斐波那契螺旋：自然之美",
                            "三分法：简化的黄金分割",
                            "视觉重心：引导观者视线"
                        ],
                        "image_description": "黄金分割构图示意"
                    },
                    {
                        "index": 7, "page_num": 7,
                        "slide_type": "top_image",
                        "title": "版式设计实践",
                        "layout": {"template": "top_image"},
                        "content": [
                            "留白艺术：少即是多",
                            "网格系统：秩序之美",
                            "字体搭配：和谐对比"
                        ],
                        "image_description": "版式设计作品展示"
                    },
                    {
                        "index": 8, "page_num": 8,
                        "slide_type": "summary",
                        "title": "设计要点回顾",
                        "layout": {"template": "summary"},
                        "content": [
                            "掌握构图基本法则",
                            "理解色彩搭配原理",
                            "运用黄金分割比例",
                            "培养审美直觉"
                        ]
                    }
                ]
            }
        }
    },
    # 4. 商科类 (business) - 重点展示: stats, cards, timeline
    {
        "major": "电子商务",
        "category": "business",
        "data": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "teaching_request": {
                "subject": "电子商务 直播带货运营策略",
                "knowledge_points": ["直播带货运营"],
                "teaching_scene": "theory",
                "slide_count": 8
            },
            "style_config": {
                "style_name": "business_professional",
                "color": {
                    "primary": "#2c3e50",
                    "secondary": "#34495e",
                    "accent": "#3498db",
                    "text": "#ecf0f1",
                    "background": "#1a252f",
                    "warning": "#e74c3c"
                }
            },
            "deck_content": {
                "deck_title": "电子商务：直播带货运营策略",
                "pages": [
                    {
                        "index": 1, "page_num": 1,
                        "slide_type": "cover",
                        "title": "直播带货运营策略",
                        "layout": {"template": "cover"},
                        "content": ["电子商务专业", "新零售时代的流量密码"]
                    },
                    {
                        "index": 2, "page_num": 2,
                        "slide_type": "stats",
                        "title": "2025直播电商市场",
                        "layout": {"template": "stats"},
                        "content": [
                            "5.2万亿：市场规模",
                            "8.7亿：直播用户数",
                            "127%：年增长率",
                            "35%：电商渗透率"
                        ]
                    },
                    {
                        "index": 3, "page_num": 3,
                        "slide_type": "cards_4col",
                        "title": "直播电商四要素",
                        "layout": {"template": "cards_4col"},
                        "content": [
                            "人：主播人设与粉丝运营",
                            "货：选品策略与货源管理",
                            "场：直播间场景氛围",
                            "流量：公私域流量运营"
                        ]
                    },
                    {
                        "index": 4, "page_num": 4,
                        "slide_type": "timeline",
                        "title": "直播节奏把控",
                        "layout": {"template": "timeline"},
                        "content": [
                            "0-5分钟：福利预告，留住观众",
                            "5-15分钟：产品种草，建立信任",
                            "15-30分钟：限时秒杀，转化高峰",
                            "30-50分钟：连带销售，提升客单",
                            "50-60分钟：下次预告，私域引流"
                        ]
                    },
                    {
                        "index": 5, "page_num": 5,
                        "slide_type": "comparison",
                        "title": "主流平台对比",
                        "layout": {"template": "comparison"},
                        "content": [
                            "平台｜用户特征｜优势｜适合品类",
                            "抖音｜年轻群体｜算法精准｜快消、美妆",
                            "淘宝｜购物意图强｜电商生态｜全品类",
                            "快手｜下沉市场｜老铁经济｜农产品、服饰",
                            "视频号｜私域用户｜微信生态｜知识付费"
                        ]
                    },
                    {
                        "index": 6, "page_num": 6,
                        "slide_type": "cards_3col",
                        "title": "转化提升技巧",
                        "layout": {"template": "cards_3col"},
                        "content": [
                            "限时限量营造紧迫感",
                            "价格锚点突出优惠",
                            "互动福利提升活跃"
                        ]
                    },
                    {
                        "index": 7, "page_num": 7,
                        "slide_type": "process_flow",
                        "title": "直播运营流程",
                        "layout": {"template": "process_flow"},
                        "content": [
                            "选品定价",
                            "脚本撰写",
                            "预热引流",
                            "直播执行",
                            "复盘优化"
                        ]
                    },
                    {
                        "index": 8, "page_num": 8,
                        "slide_type": "summary",
                        "title": "核心要点",
                        "layout": {"template": "summary"},
                        "content": [
                            "人货场三位一体",
                            "节奏把控是关键",
                            "数据驱动决策",
                            "私域沉淀复购"
                        ]
                    }
                ]
            }
        }
    },
    # 5. 农林环境类 (nature) - 重点展示: image_wall, circular, split
    {
        "major": "园林技术",
        "category": "nature",
        "data": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "teaching_request": {
                "subject": "园林技术 城市绿化植物配置",
                "knowledge_points": ["植物配置"],
                "teaching_scene": "theory",
                "slide_count": 8
            },
            "style_config": {
                "style_name": "nature_green",
                "color": {
                    "primary": "#27ae60",
                    "secondary": "#2ecc71",
                    "accent": "#f1c40f",
                    "text": "#ecf0f1",
                    "background": "#0d2818",
                    "warning": "#e74c3c"
                }
            },
            "deck_content": {
                "deck_title": "园林技术：城市绿化植物配置",
                "pages": [
                    {
                        "index": 1, "page_num": 1,
                        "slide_type": "cover",
                        "title": "城市绿化植物配置",
                        "layout": {"template": "cover"},
                        "content": ["园林技术专业", "绿色城市的设计法则"]
                    },
                    {
                        "index": 2, "page_num": 2,
                        "slide_type": "quote",
                        "title": "城市需要绿色，绿色创造生活",
                        "subtitle": "园林设计理念",
                        "layout": {"template": "quote"},
                        "content": []
                    },
                    {
                        "index": 3, "page_num": 3,
                        "slide_type": "circular",
                        "title": "植物配置原则",
                        "subtitle": "生态",
                        "layout": {"template": "circular"},
                        "content": [
                            "适地适树",
                            "生态优先",
                            "四季有景",
                            "层次分明",
                            "色彩协调",
                            "功能兼顾"
                        ]
                    },
                    {
                        "index": 4, "page_num": 4,
                        "slide_type": "image_wall",
                        "title": "常用乔木品种",
                        "layout": {"template": "image_wall_2x2"},
                        "content": [
                            "银杏：秋叶金黄",
                            "香樟：常绿芳香",
                            "法桐：遮荫优秀",
                            "栾树：夏花秋果"
                        ]
                    },
                    {
                        "index": 5, "page_num": 5,
                        "slide_type": "pyramid",
                        "title": "植物配置层次",
                        "layout": {"template": "pyramid"},
                        "content": [
                            "上层：乔木（遮荫）",
                            "中层：灌木（造景）",
                            "下层：地被（覆盖）",
                            "底层：草坪（基础）"
                        ]
                    },
                    {
                        "index": 6, "page_num": 6,
                        "slide_type": "image_wall",
                        "title": "四季植物搭配",
                        "layout": {"template": "image_wall_2x3"},
                        "content": [
                            "春：樱花、玉兰",
                            "夏：紫薇、合欢",
                            "秋：红枫、银杏",
                            "冬：腊梅、松柏",
                            "常绿：香樟、桂花",
                            "地被：麦冬、鸢尾"
                        ]
                    },
                    {
                        "index": 7, "page_num": 7,
                        "slide_type": "split",
                        "title": "街道绿化设计",
                        "layout": {"template": "split"},
                        "content": [
                            "行道树：树冠开阔不飞絮",
                            "分车带：低矮灌木色块搭配",
                            "树池：透气铺装地被覆盖",
                            "养护：定期修剪病虫害防治"
                        ],
                        "image_description": "街道绿化断面图"
                    },
                    {
                        "index": 8, "page_num": 8,
                        "slide_type": "summary",
                        "title": "设计要点",
                        "layout": {"template": "summary"},
                        "content": [
                            "适地适树因地制宜",
                            "四季有景层次分明",
                            "生态优先功能兼顾",
                            "养护管理持续跟进"
                        ]
                    }
                ]
            }
        }
    },
    # 6. 理科类 (science) - 重点展示: stats, comparison, circular
    {
        "major": "应用数学",
        "category": "science",
        "data": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "teaching_request": {
                "subject": "应用数学 概率统计在工程中的应用",
                "knowledge_points": ["概率统计应用"],
                "teaching_scene": "theory",
                "slide_count": 8
            },
            "style_config": {
                "style_name": "science_academic",
                "color": {
                    "primary": "#2980b9",
                    "secondary": "#3498db",
                    "accent": "#9b59b6",
                    "text": "#ecf0f1",
                    "background": "#0a1628",
                    "warning": "#e74c3c"
                }
            },
            "deck_content": {
                "deck_title": "应用数学：概率统计在工程中的应用",
                "pages": [
                    {
                        "index": 1, "page_num": 1,
                        "slide_type": "cover",
                        "title": "概率统计在工程中的应用",
                        "layout": {"template": "cover"},
                        "content": ["应用数学", "数据驱动的工程决策"]
                    },
                    {
                        "index": 2, "page_num": 2,
                        "slide_type": "quote",
                        "title": "上帝不掷骰子，但工程师需要理解概率",
                        "subtitle": "数据科学理念",
                        "layout": {"template": "quote"},
                        "content": []
                    },
                    {
                        "index": 3, "page_num": 3,
                        "slide_type": "cards_4col",
                        "title": "常用概率分布",
                        "layout": {"template": "cards_4col"},
                        "content": [
                            "正态分布：自然现象建模",
                            "泊松分布：稀有事件分析",
                            "指数分布：设备寿命预测",
                            "二项分布：质量检验判定"
                        ]
                    },
                    {
                        "index": 4, "page_num": 4,
                        "slide_type": "stats",
                        "title": "正态分布关键参数",
                        "layout": {"template": "stats"},
                        "content": [
                            "μ：均值（分布中心）",
                            "σ：标准差（离散程度）",
                            "68%：±1σ范围概率",
                            "95%：±2σ范围概率"
                        ]
                    },
                    {
                        "index": 5, "page_num": 5,
                        "slide_type": "circular",
                        "title": "统计分析方法",
                        "subtitle": "统计",
                        "layout": {"template": "circular"},
                        "content": [
                            "假设检验",
                            "置信区间",
                            "回归分析",
                            "方差分析",
                            "相关分析",
                            "非参检验"
                        ]
                    },
                    {
                        "index": 6, "page_num": 6,
                        "slide_type": "comparison",
                        "title": "假设检验步骤",
                        "layout": {"template": "comparison"},
                        "content": [
                            "步骤｜操作｜说明",
                            "1｜建立假设｜H₀和H₁",
                            "2｜选择显著性水平｜α通常取0.05",
                            "3｜计算检验统计量｜t值或z值",
                            "4｜确定临界值｜查表或计算",
                            "5｜做出决策｜拒绝或接受H₀"
                        ]
                    },
                    {
                        "index": 7, "page_num": 7,
                        "slide_type": "before_after",
                        "title": "工程质量控制",
                        "layout": {"template": "before_after"},
                        "content": [
                            "经验判断产品质量",
                            "人工抽检效率低",
                            "质量波动难追踪",
                            "SPC控制图监控",
                            "自动化统计分析",
                            "实时预警与调整"
                        ]
                    },
                    {
                        "index": 8, "page_num": 8,
                        "slide_type": "summary",
                        "title": "核心知识点",
                        "layout": {"template": "summary"},
                        "content": [
                            "掌握常用概率分布",
                            "理解假设检验流程",
                            "运用SPC控制图",
                            "数据驱动工程决策"
                        ]
                    }
                ]
            }
        }
    }
]


def save_html(html_code: str, category: str, major: str) -> str:
    """保存HTML到文件"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_major = major.replace(" ", "_")[:15]
    filename = f"layouts_test_{category}-{safe_major}-{timestamp}.html"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_code)
    
    return filepath


def run_test(test_item: dict) -> dict:
    """运行单个测试"""
    major = test_item["major"]
    category = test_item["category"]
    data = test_item["data"]
    
    # 统计使用的布局
    layouts_used = set()
    for page in data["deck_content"]["pages"]:
        layout = page.get("layout", {}).get("template", "default")
        layouts_used.add(layout)
    
    print(f"\n{'='*60}")
    print(f"🎯 测试 [{category.upper()}] - {major}")
    print(f"   📐 使用布局: {', '.join(sorted(layouts_used))}")
    print('='*60)
    
    # 验证学科分类
    detected = _determine_subject_category(major)
    print(f"   检测到学科类别: {detected.value}")
    
    # 准备state数据
    state = {
        "user_input": {
            "topic": data["teaching_request"]["subject"],
            "major": major,
            "target_audience": "高职二年级学生",
            "duration": "45分钟"
        },
        "planning": {
            "deck_title": data["deck_content"]["deck_title"],
            "subject": data["teaching_request"]["subject"],
            "knowledge_points": data["teaching_request"]["knowledge_points"],
            "teaching_request": data["teaching_request"],
            "style_config": data["style_config"],
            "deck_content": data["deck_content"]
        }
    }
    
    start_time = time.time()
    
    try:
        # 使用HTMLGenerator生成HTML
        generator = HTMLGenerator()
        result = generator.generate(state)
        
        execution_time = time.time() - start_time
        
        html = result.get("final_html") or result.get("html_code")
        if html:
            filepath = save_html(html, category, major)
            print(f"   ✅ 生成成功！耗时: {execution_time:.1f}s")
            print(f"   📄 保存至: {filepath}")
            return {
                "category": category,
                "major": major,
                "layouts": list(layouts_used),
                "filepath": filepath,
                "time": execution_time,
                "success": True
            }
        else:
            print(f"   ❌ 生成失败：无HTML输出")
            return {"category": category, "success": False, "error": "No HTML output"}
            
    except Exception as e:
        import traceback
        print(f"   ❌ 错误: {e}")
        traceback.print_exc()
        return {"category": category, "success": False, "error": str(e)}


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🧪 批量布局测试 - 19种布局模板 × 6个学科类别")
    print("   📝 展示不同布局效果，无需LLM调用")
    print("="*70)
    
    print("\n📐 可用布局模板 (19种):")
    print("   P0: cover, timeline, cards_3col, cards_4col, image_wall_2x2, image_wall_2x3")
    print("   P1: quote, stats, process_flow, before_after")
    print("   P2: masonry, circular, pyramid")
    print("   基础: split, top_image, steps, warning, summary, comparison")
    
    results = []
    total_start = time.time()
    
    for i, test_item in enumerate(SUBJECT_TEST_DATA, 1):
        print(f"\n[{i}/{len(SUBJECT_TEST_DATA)}] 开始测试...")
        result = run_test(test_item)
        results.append(result)
    
    total_time = time.time() - total_start
    success_count = sum(1 for r in results if r.get("success"))
    
    # 统计所有使用的布局
    all_layouts = set()
    for r in results:
        if r.get("layouts"):
            all_layouts.update(r["layouts"])
    
    print("\n" + "="*70)
    print("📊 测试汇总")
    print("="*70)
    print(f"总测试数: {len(SUBJECT_TEST_DATA)}")
    print(f"成功: {success_count} | 失败: {len(SUBJECT_TEST_DATA) - success_count}")
    print(f"使用布局数: {len(all_layouts)}")
    print(f"总耗时: {total_time:.1f}秒")
    
    print("\n生成的文件:")
    for r in results:
        if r.get("success"):
            print(f"  ✅ [{r['category']}] {r['filepath']}")
            print(f"      布局: {', '.join(r['layouts'])}")
        else:
            print(f"  ❌ [{r['category']}] 失败: {r.get('error', '未知错误')}")
    
    print("\n" + "="*70)
    print("💡 提示: 用浏览器打开output目录下的HTML文件查看不同布局效果")
    print("   按 ← → 键翻页，按 F 键全屏")
    print("="*70)
    
    return results


if __name__ == "__main__":
    main()
