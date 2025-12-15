from flask import Flask, render_template, request
import jieba

app = Flask(__name__)

# ---------------------- 数学分析知识点规则库 ----------------------
# 结构：{关键词: {知识点名称: 内容（支持LaTeX公式）, 例题: 解析, 习题: 推荐}}
knowledge_base = {
    "极限": {
        "title": "函数极限的定义与性质",
        "content": """
        1. 数列极限定义（ε-N语言）：对∀ε>0，∃N∈N₊，当n>N时，|xₙ - a| < ε，则limₙ→∞xₙ = a；
        2. 函数极限定义（ε-δ语言）：对∀ε>0，∃δ>0，当0<|x - x₀| < δ时，|f(x) - A| < ε，则limₓ→x₀f(x) = A；
        3. 核心性质：唯一性、局部有界性、局部保号性、夹逼准则、单调有界准则。
        """,
        "example": """
        例题：证明limₓ→2(x² - 4)/(x - 2) = 4<br>
        解析：<br>
        1. 化简函数：(x² - 4)/(x - 2) = x + 2（x≠2）；<br>
        2. 对∀ε>0，要使|(x + 2) - 4| = |x - 2| < ε，取δ=ε；<br>
        3. 当0<|x - 2| < δ时，|f(x) - 4| < ε，故极限为4。
        """,
        "exercise": "1. 用ε-N语言证明limₙ→∞(n+1)/(2n) = 1/2；2. 求limₓ→0(sin3x)/x（提示：等价无穷小替换）"
    },
    "导数": {
        "title": "导数的定义与求导法则",
        "content": """
        1. 导数定义：f’(x₀) = limₖ→0[f(x₀+h) - f(x₀)]/h 或 limₓ→x₀[f(x) - f(x₀)]/(x - x₀)；
        2. 基本求导法则：四则运算、复合函数链式法则、隐函数求导、参数方程求导；
        3. 常见导数公式：(sinx)’=cosx，(lnx)’=1/x，(eˣ)’=eˣ，(xⁿ)’=nxⁿ⁻¹。
        """,
        "example": """
        例题：求y = sin(2x + 3)的导数<br>
        解析：<br>
        1. 设复合函数：u = 2x + 3，y = sinu；<br>
        2. 链式法则：dy/dx = (dy/du)·(du/dx) = cosu·2 = 2cos(2x + 3)。
        """,
        "exercise": "1. 求y = x²lnx的导数；2. 用导数定义证明(cosx)’ = -sinx"
    },
    "积分": {
        "title": "定积分与不定积分",
        "content": """
        1. 不定积分：∫f(x)dx = F(x) + C，其中F’(x) = f(x)（原函数族）；
        2. 定积分（黎曼积分）：∫ₐᵇf(x)dx = limₙ→∞Σᵢ₌₁ⁿf(ξᵢ)Δxᵢ（Δxᵢ=(b-a)/n，ξᵢ∈[xᵢ₋₁,xᵢ]）；
        3. 牛顿-莱布尼茨公式：∫ₐᵇf(x)dx = F(b) - F(a)（F为f的原函数）。
        """,
        "example": """
        例题：计算∫₀¹x²dx<br>
        解析：<br>
        1. 求原函数：∫x²dx = (1/3)x³ + C；<br>
        2. 应用牛顿-莱布尼茨公式：(1/3)(1³ - 0³) = 1/3。
        """,
        "exercise": "1. 计算∫sin2xdx；2. 求∫₁ᵉ(1 + lnx)/x dx（提示：换元法，令u=1+lnx）"
    },
    "级数": {
        "title": "数项级数与幂级数",
        "content": """
        1. 数项级数收敛定义：limₙ→∞Sₙ = S（Sₙ=Σᵢ₌₁ⁿaᵢ），则级数Σaₙ收敛；
        2. 收敛判别法：正项级数（比较判别法、比值判别法）、交错级数（莱布尼茨判别法）；
        3. 幂级数收敛半径：R = 1/limₙ→∞|aₙ₊₁/aₙ|（比值法），收敛区间为(-R, R)。
        """,
        "example": """
        例题：判断级数Σₙ=1^∞(1/n²)的收敛性<br>
        解析：<br>
        1. 该级数为正项级数，且1/n² ≤ 1/(n(n-1))（n≥2）；<br>
        2. 级数Σₙ=2^∞1/(n(n-1)) = Σₙ=2^∞[1/(n-1) - 1/n]（裂项），前n项和Sₙ=1 - 1/n→1（n→∞），收敛；<br>
        3. 由比较判别法，Σ(1/n²)收敛。
        """,
        "exercise": "1. 判断级数Σₙ=1^∞(1/√n)的收敛性；2. 求幂级数Σₙ=1^∞xⁿ/n的收敛半径与收敛区间"
    }
}

# ---------------------- 核心问答逻辑 ----------------------
def match_knowledge(user_question):
    """关键词匹配知识点"""
    keywords = jieba.lcut(user_question)  # 分词提取关键词
    matched_topic = None
    # 优先匹配核心知识点关键词
    for topic in knowledge_base.keys():
        if topic in keywords:
            matched_topic = topic
            break
    # 无匹配时返回引导信息
    if not matched_topic:
        return {
            "title": "未找到相关知识点",
            "content": "请尝试询问以下数学分析核心知识点：极限、导数、积分、级数（例如：什么是导数？如何求定积分？）",
            "example": "",
            "exercise": ""
        }
    return knowledge_base[matched_topic]

# ---------------------- Web界面路由 ----------------------
@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    if request.method == "POST":
        user_question = request.form.get("question")
        answer = match_knowledge(user_question)
    return render_template("index.html", answer=answer)

if __name__ == "__main__":
    app.run(debug=True)