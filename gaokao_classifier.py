#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""高考真题智能分类模块

功能：
1. 自动识别题型（选择题/填空题/解答题）
2. 自动识别知识点和知识模块
3. 自动评估难度
4. 支持批量分类
"""

import json
import re

# 各科目详细知识点分类体系
SUBJECT_CATEGORIES = {
    '数学': {
        '一级分类': [
            '集合与逻辑', '函数与导数', '三角函数', '数列',
            '立体几何', '解析几何', '概率与统计', '不等式',
            '向量', '复数', '排列组合', '二项式定理'
        ],
        '二级分类': {
            '集合与逻辑': ['集合运算', '充要条件', '逻辑联结词', '全称量词与存在量词'],
            '函数与导数': ['函数性质', '基本初等函数', '函数图像', '导数应用', '函数零点', '函数最值'],
            '三角函数': ['三角恒等变换', '三角函数图像', '正弦定理', '余弦定理', '解三角形'],
            '数列': ['等差数列', '等比数列', '数列求和', '数列通项', '数列极限'],
            '立体几何': ['空间几何体', '点线面位置关系', '空间向量', '二面角', '体积计算'],
            '解析几何': ['直线', '圆', '椭圆', '双曲线', '抛物线', '曲线与方程'],
            '概率与统计': ['古典概型', '几何概型', '统计图表', '回归分析', '独立性检验', '分布列'],
            '不等式': ['均值不等式', '绝对值不等式', '线性规划', '不等式证明'],
            '向量': ['平面向量', '空间向量', '向量运算', '向量应用'],
            '复数': ['复数运算', '复数几何意义', '复数方程'],
            '排列组合': ['排列', '组合', '分类计数', '分步计数'],
            '二项式定理': ['二项展开式', '系数问题', '特定项']
        },
        '题型特征': {
            '选择题': ['下列', '正确的是', '错误的是', '等于', '为'],
            '填空题': ['则', '等于', '值为', '的值'],
            '解答题': ['证明', '求', '设', '若', '已知']
        }
    },
    '语文': {
        '一级分类': [
            '现代文阅读', '古诗文阅读', '语言文字运用', '写作',
            '文学类文本', '实用类文本', '论述类文本'
        ],
        '二级分类': {
            '现代文阅读': ['论述类文本', '文学类文本', '实用类文本'],
            '古诗文阅读': ['文言文阅读', '古代诗歌阅读', '名篇名句默写'],
            '语言文字运用': ['成语运用', '病句辨析', '语句衔接', '图文转换', '压缩语段'],
            '写作': ['材料作文', '任务驱动型作文', '话题作文'],
            '文学类文本': ['小说', '散文', '戏剧'],
            '实用类文本': ['新闻', '传记', '报告'],
            '论述类文本': ['学术论文', '评论', '杂文']
        },
        '题型特征': {
            '选择题': ['下列', '不正确', '正确', '符合', '不符合'],
            '填空题': ['补写', '默写', '填写'],
            '解答题': ['分析', '赏析', '概括', '探究', '理解']
        }
    },
    '英语': {
        '一级分类': [
            '听力', '阅读理解', '完形填空', '语法填空',
            '短文改错', '书面表达', '七选五'
        ],
        '二级分类': {
            '听力': ['短对话', '长对话', '独白'],
            '阅读理解': ['细节理解', '推理判断', '主旨大意', '词义猜测', '标题归纳'],
            '完形填空': ['记叙文', '说明文', '议论文'],
            '语法填空': ['动词时态', '非谓语', '从句', '冠词', '介词', '代词'],
            '短文改错': ['词法错误', '句法错误', '行文逻辑'],
            '书面表达': ['应用文', '读后续写', '概要写作'],
            '七选五': ['段落主题', '过渡句', '总结句']
        },
        '题型特征': {
            '选择题': ['A.', 'B.', 'C.', 'D.'],
            '填空题': ['___', 'blank'],
            '解答题': ['write', 'composition', 'letter']
        }
    },
    '物理': {
        '一级分类': [
            '力学', '电磁学', '热学', '光学',
            '原子物理', '实验题', '物理常识'
        ],
        '二级分类': {
            '力学': ['运动学', '牛顿定律', '功和能', '动量', '圆周运动', '万有引力', '机械振动', '机械波'],
            '电磁学': ['静电场', '恒定电流', '磁场', '电磁感应', '交变电流', '电磁波'],
            '热学': ['分子动理论', '气体性质', '热力学定律'],
            '光学': ['几何光学', '物理光学', '光的衍射', '光的干涉'],
            '原子物理': ['原子结构', '原子核', '核反应', '放射性'],
            '实验题': ['力学实验', '电学实验', '光学实验', '数据处理'],
            '物理常识': ['物理学史', '物理方法', '物理思想']
        },
        '题型特征': {
            '选择题': ['下列', '正确', '错误', '可能', '一定'],
            '填空题': ['则', '为', '等于', '大小'],
            '解答题': ['求', '计算', '证明', '分析']
        }
    },
    '化学': {
        '一级分类': [
            '有机化学', '无机化学', '化学反应原理',
            '化学实验', '物质结构', '化学与生活'
        ],
        '二级分类': {
            '有机化学': ['烃', '烃的衍生物', '有机合成', '有机推断', '同分异构体'],
            '无机化学': ['金属及其化合物', '非金属及其化合物', '离子反应', '氧化还原反应'],
            '化学反应原理': ['化学平衡', '电离平衡', '水解平衡', '电化学', '热化学'],
            '化学实验': ['实验设计', '实验评价', '定量实验', '物质检验', '物质分离'],
            '物质结构': ['原子结构', '分子结构', '晶体结构', '元素周期律'],
            '化学与生活': ['材料', '能源', '环境', '食品']
        },
        '题型特征': {
            '选择题': ['下列', '正确', '错误', '说法'],
            '填空题': ['写出', '化学式', '方程式'],
            '解答题': ['解释', '设计', '计算', '推断']
        }
    },
    '生物': {
        '一级分类': [
            '细胞生物学', '遗传学', '生态学',
            '动物生理', '植物生理', '生物技术', '现代生物科技'
        ],
        '二级分类': {
            '细胞生物学': ['细胞结构', '细胞代谢', '细胞增殖', '细胞分化'],
            '遗传学': ['遗传规律', '遗传分子基础', '遗传变异', '人类遗传病'],
            '生态学': ['种群', '群落', '生态系统', '环境保护'],
            '动物生理': ['神经调节', '体液调节', '免疫调节', '内环境稳态'],
            '植物生理': ['光合作用', '呼吸作用', '植物激素', '植物代谢'],
            '生物技术': ['发酵工程', '酶工程', '基因工程', '细胞工程'],
            '现代生物科技': ['基因工程', '细胞工程', '胚胎工程', '生态工程']
        },
        '题型特征': {
            '选择题': ['下列', '正确', '错误', '关于'],
            '填空题': ['填写', '补充', '图中'],
            '解答题': ['分析', '解释', '设计实验', '探究']
        }
    },
    '历史': {
        '一级分类': [
            '中国古代史', '中国近代史', '中国现代史',
            '世界古代史', '世界近代史', '世界现代史',
            '政治制度', '经济文化'
        ],
        '二级分类': {
            '中国古代史': ['先秦', '秦汉', '魏晋南北朝', '隋唐', '宋元', '明清'],
            '中国近代史': ['鸦片战争', '太平天国', '洋务运动', '辛亥革命', '五四运动'],
            '中国现代史': ['新中国成立', '社会主义建设', '改革开放'],
            '世界古代史': ['古希腊', '古罗马'],
            '世界近代史': ['文艺复兴', '工业革命', '资产阶级革命'],
            '世界现代史': ['两次世界大战', '冷战', '多极化'],
            '政治制度': ['古代政治', '近代政治', '现代政治'],
            '经济文化': ['古代经济', '近代经济', '思想文化']
        },
        '题型特征': {
            '选择题': ['下列', '关于', '正确', '错误'],
            '填空题': ['填写', '补充'],
            '解答题': ['分析', '概括', '比较', '评价']
        }
    },
    '地理': {
        '一级分类': [
            '自然地理', '人文地理', '区域地理',
            '地理信息技术', '旅游地理', '环境保护'
        ],
        '二级分类': {
            '自然地理': ['地球运动', '大气', '水', '地表形态', '自然带'],
            '人文地理': ['人口', '城市', '农业', '工业', '交通'],
            '区域地理': ['中国地理', '世界地理', '区域分析'],
            '地理信息技术': ['遥感', '全球定位系统', '地理信息系统'],
            '旅游地理': ['旅游资源', '旅游规划', '旅游发展'],
            '环境保护': ['环境问题', '生态保护', '可持续发展']
        },
        '题型特征': {
            '选择题': ['下列', '关于', '图中', '正确'],
            '填空题': ['填写', '图中'],
            '解答题': ['分析', '解释', '说明', '描述']
        }
    },
    '政治': {
        '一级分类': [
            '经济生活', '政治生活', '文化生活',
            '生活与哲学', '时事政治'
        ],
        '二级分类': {
            '经济生活': ['消费', '生产', '分配', '市场经济', '对外开放'],
            '政治生活': ['公民', '政府', '人大', '政党', '民族宗教', '国际关系'],
            '文化生活': ['文化作用', '文化传承', '中华文化', '文化建设'],
            '生活与哲学': ['唯物论', '认识论', '辩证法', '历史唯物主义'],
            '时事政治': ['国内时政', '国际时政', '政策解读']
        },
        '题型特征': {
            '选择题': ['下列', '关于', '体现', '说明'],
            '填空题': ['填写', '补充'],
            '解答题': ['分析', '说明', '体现', '如何']
        }
    }
}

# 难度评估标准
DIFFICULTY_CRITERIA = {
    '简单': [
        '直接应用公式',
        '单一知识点',
        '基础概念',
        '简单计算',
        '直接提取信息'
    ],
    '中等': [
        '多个知识点综合',
        '需要一定推理',
        '中等计算量',
        '需要分析材料',
        '常规题型变化'
    ],
    '困难': [
        '复杂综合题',
        '创新题型',
        '大量计算',
        '深度推理',
        '跨知识点综合',
        '压轴题难度'
    ]
}


def get_classification_prompt(subject, content, question_type=None):
    """生成AI分类提示词"""
    
    subject_info = SUBJECT_CATEGORIES.get(subject, {})
    categories = subject_info.get('一级分类', [])
    subcategories = subject_info.get('二级分类', {})
    
    # 构建分类参考
    category_ref = []
    for cat in categories:
        subs = subcategories.get(cat, [])
        if subs:
            category_ref.append(f"- {cat}: {', '.join(subs)}")
        else:
            category_ref.append(f"- {cat}")
    
    category_text = '\n'.join(category_ref)
    
    prompt = f"""请对以下{subject}高考题目进行智能分类。

题目内容：
{content[:1000]}

题目类型：{question_type or '未知'}

请从以下维度进行分类：

1. 知识模块（一级分类）：
{category_text}

2. 具体知识点（二级分类）：
请根据题目内容识别具体的知识点，多个知识点用逗号分隔。

3. 难度评估：
- 简单：基础题，直接应用
- 中等：综合题，需要一定推理
- 困难：压轴题，复杂综合

请返回JSON格式：
{{
    "category": "一级分类名称（知识模块）",
    "knowledge_points": ["知识点1", "知识点2"],
    "difficulty": "简单/中等/困难",
    "analysis": "分类理由（简要说明）"
}}

只返回JSON，不要其他内容。"""

    return prompt


def parse_classification_result(result_text, subject):
    """解析AI分类结果"""
    
    if not result_text:
        return None
    
    try:
        # 尝试直接解析
        data = json.loads(result_text.strip())
    except:
        # 尝试提取JSON
        json_match = re.search(r'\{[^{}]*\}', result_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
            except:
                return None
        else:
            return None
    
    # 验证和标准化
    subject_info = SUBJECT_CATEGORIES.get(subject, {})
    valid_categories = subject_info.get('一级分类', [])
    
    category = data.get('category', '')
    
    # 如果分类不在有效列表中，尝试匹配
    if category and valid_categories:
        # 精确匹配
        if category not in valid_categories:
            # 模糊匹配
            for valid_cat in valid_categories:
                if valid_cat in category or category in valid_cat:
                    category = valid_cat
                    break
            else:
                # 如果都不匹配，使用第一个词
                category = valid_categories[0] if valid_categories else category
    
    knowledge_points = data.get('knowledge_points', [])
    if isinstance(knowledge_points, str):
        knowledge_points = [kp.strip() for kp in knowledge_points.split(',')]
    
    difficulty = data.get('difficulty', '中等')
    if difficulty not in ['简单', '中等', '困难']:
        difficulty = '中等'
    
    return {
        'category': category,
        'knowledge_points': knowledge_points,
        'difficulty': difficulty,
        'analysis': data.get('analysis', '')
    }


def classify_question_type(content):
    """根据题目内容识别题型"""
    
    content_lower = content.lower()
    
    # 选择题特征
    if re.search(r'[A-D][.、．]', content) or '下列' in content:
        return '选择题'
    
    # 填空题特征
    if re.search(r'_{3,}|____|\(\s*\)', content) or '填写' in content:
        return '填空题'
    
    # 解答题特征
    if any(keyword in content for keyword in ['证明', '求', '计算', '分析', '解释', '说明']):
        return '解答题'
    
    # 默认
    return '解答题'


def estimate_difficulty(content, score=None):
    """评估题目难度（简单规则）"""
    
    content_len = len(content)
    
    # 根据题目长度
    if content_len < 100:
        base_difficulty = '简单'
    elif content_len < 300:
        base_difficulty = '中等'
    else:
        base_difficulty = '困难'
    
    # 根据分值调整
    if score:
        if score <= 5:
            if base_difficulty == '困难':
                base_difficulty = '中等'
        elif score >= 12:
            if base_difficulty == '简单':
                base_difficulty = '中等'
    
    # 关键词调整
    difficult_keywords = ['综合', '证明', '探究', '创新', '压轴']
    easy_keywords = ['下列', '简单', '基础', '直接']
    
    for keyword in difficult_keywords:
        if keyword in content:
            if base_difficulty == '简单':
                base_difficulty = '中等'
            elif base_difficulty == '中等':
                base_difficulty = '困难'
            break
    
    for keyword in easy_keywords:
        if keyword in content:
            if base_difficulty == '困难':
                base_difficulty = '中等'
            elif base_difficulty == '中等':
                base_difficulty = '简单'
            break
    
    return base_difficulty


def get_subject_categories(subject):
    """获取科目的分类体系"""
    return SUBJECT_CATEGORIES.get(subject, {})


def get_all_subjects():
    """获取所有支持的科目"""
    return list(SUBJECT_CATEGORIES.keys())


def validate_category(subject, category):
    """验证分类是否有效"""
    subject_info = SUBJECT_CATEGORIES.get(subject, {})
    valid_categories = subject_info.get('一级分类', [])
    
    if not valid_categories:
        return True  # 如果没有预设分类，允许任何分类
    
    return category in valid_categories


def get_category_suggestions(subject, partial_text):
    """根据输入获取分类建议"""
    subject_info = SUBJECT_CATEGORIES.get(subject, {})
    categories = subject_info.get('一级分类', [])
    
    if not partial_text:
        return categories
    
    return [cat for cat in categories if partial_text in cat]


# 测试函数
if __name__ == '__main__':
    print("=== 高考真题智能分类模块 ===")
    print()
    
    # 显示各科目分类
    for subject in get_all_subjects():
        print(f"【{subject}】")
        categories = SUBJECT_CATEGORIES[subject].get('一级分类', [])
        print(f"  一级分类: {', '.join(categories)}")
        print()
    
    # 测试题型识别
    test_cases = [
        ("下列说法正确的是（  ）\nA. ...\nB. ...\nC. ...\nD. ...", None),
        ("已知函数f(x)=x²+2x，则f(3)=____", None),
        ("证明：对任意正整数n，n³-n能被6整除。", None),
    ]
    
    print("=== 题型识别测试 ===")
    for content, expected in test_cases:
        result = classify_question_type(content)
        print(f"题目: {content[:30]}... -> {result}")
    
    print()
    print("=== 难度评估测试 ===")
    test_contents = [
        "1+1等于多少？",
        "已知函数f(x)=x³-3x²+2，求f(x)的极值。",
        "设椭圆C: x²/a²+y²/b²=1(a>b>0)的离心率为√3/2，且过点(1,3/2)。(1)求C的方程；(2)设直线l过点M(0,1)，与C交于A,B两点，求△AOB面积的最大值。"
    ]
    
    for content in test_contents:
        difficulty = estimate_difficulty(content)
        print(f"题目: {content[:40]}... -> {difficulty}")
