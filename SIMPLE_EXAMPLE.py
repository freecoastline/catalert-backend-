"""
CatAlert后端项目 - 简化示例
这个文件展示了项目的核心概念，适合零基础学习
"""

# =============================================================================
# 1. 基础概念：什么是API？
# =============================================================================

# API就像餐厅的服务员
# 客户(前端) → 服务员(API) → 厨师(业务逻辑) → 厨房(数据库)

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

# 创建一个FastAPI应用
app = FastAPI(title="CatAlert 简化版")

# =============================================================================
# 2. 数据模型：如何表示数据？
# =============================================================================

# 用Python类表示数据库表
class Cat(BaseModel):
    """猫咪数据模型"""
    id: Optional[int] = None
    name: str
    age: int
    breed: str
    owner_name: str

# 模拟数据库（实际项目中用PostgreSQL）
cats_database = [
    Cat(id=1, name="胡胡", age=4, breed="英短", owner_name="小明"),
    Cat(id=2, name="咪咪", age=2, breed="美短", owner_name="小红")
]

# =============================================================================
# 3. API端点：如何提供数据服务？
# =============================================================================

@app.get("/")
def read_root():
    """根路径，返回欢迎信息"""
    return {"message": "欢迎使用CatAlert API！", "Hello": "World"}

@app.get("/cats", response_model=List[Cat])
def get_all_cats():
    """获取所有猫咪信息"""
    return cats_database

@app.get("/cats/{cat_id}", response_model=Cat)
def get_cat_by_id(cat_id: int):
    """根据ID获取特定猫咪信息"""
    for cat in cats_database:
        if cat.id == cat_id:
            return cat
    return {"error": "猫咪不存在"}

@app.post("/cats", response_model=Cat)
def create_cat(cat: Cat):
    """创建新的猫咪记录"""
    # 生成新的ID
    new_id = max([c.id for c in cats_database if c.id]) + 1
    cat.id = new_id
    
    # 添加到数据库
    cats_database.append(cat)
    
    return cat

# =============================================================================
# 4. AI功能：如何添加智能分析？
# =============================================================================

class AIAnalysis(BaseModel):
    """AI分析结果"""
    cat_name: str
    health_score: float
    recommendations: List[str]

@app.get("/cats/{cat_id}/ai-analysis", response_model=AIAnalysis)
def get_ai_analysis(cat_id: int):
    """获取AI健康分析"""
    # 找到猫咪
    cat = None
    for c in cats_database:
        if c.id == cat_id:
            cat = c
            break
    
    if not cat:
        return {"error": "猫咪不存在"}
    
    # 模拟AI分析（实际项目中调用OpenAI）
    health_score = 0.8  # 健康评分
    recommendations = [
        f"{cat.name}的年龄是{cat.age}岁，建议定期体检",
        f"{cat.breed}品种需要特别注意饮食",
        "建议每天至少15分钟的玩耍时间"
    ]
    
    return AIAnalysis(
        cat_name=cat.name,
        health_score=health_score,
        recommendations=recommendations
    )

# =============================================================================
# 5. 如何运行这个示例？
# =============================================================================

#入口点1：简单启动（不运行测试）
if __name__ == "__main__":
    import uvicorn
    print("启动CatAlert简化版API...")
    print("访问 http://localhost:8000/docs 查看API文档")
    print("访问 http://localhost:8000/cats 查看所有猫咪")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# =============================================================================
# 6. 学习要点总结
# =============================================================================

"""
这个简化示例展示了以下核心概念：

1. API设计：
   - GET /cats - 获取所有猫咪
   - GET /cats/{id} - 获取特定猫咪
   - POST /cats - 创建新猫咪
   - GET /cats/{id}/ai-analysis - AI分析

2. 数据模型：
   - 用Pydantic定义数据结构
   - 类型提示和验证
   - 响应模型定义

3. 业务逻辑：
   - 数据查询和过滤
   - 数据创建和存储
   - 错误处理

4. AI集成：
   - AI分析接口
   - 结构化响应
   - 智能建议生成

学习建议：
1. 先运行这个简化版本，理解基本概念
2. 逐步学习完整的项目代码
3. 尝试修改和扩展功能
4. 对比简化版和完整版的差异
"""

# =============================================================================
# 7. 测试示例
# =============================================================================

def test_api():
    """测试API功能"""
    print("=== CatAlert API 测试 ===")
    
    # 测试获取所有猫咪
    print("1. 获取所有猫咪：")
    for cat in cats_database:
        print(f"   - {cat.name} ({cat.breed}, {cat.age}岁)")
    
    # 测试AI分析
    print("\n2. AI健康分析：")
    analysis = get_ai_analysis(1)
    print(f"   猫咪：{analysis.cat_name}")
    print(f"   健康评分：{analysis.health_score}")
    print("   建议：")
    for rec in analysis.recommendations:
        print(f"     - {rec}")

# 入口点2：完整启动（运行测试 + 启动服务器）
if __name__ == "__main__":
    import sys
    import uvicorn
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # 简单模式：只启动服务器
        print("启动CatAlert简化版API...")
        print("访问 http://localhost:8000/docs 查看API文档")
        print("访问 http://localhost:8000/cats 查看所有猫咪")
    else:
        # 完整模式：运行测试 + 启动服务器
        test_api()
        print("\n" + "="*50)
        print("启动CatAlert简化版API...")
    
    # 启动API服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)
