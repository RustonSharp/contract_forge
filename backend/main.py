from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 修改为全路径导入
from backend.api.routes import router 
import uvicorn
import os

app = FastAPI(
    title="Contract Forge API",
    description="智能合同审计系统后端",
    version="1.0.0"
)

# 1. 更加稳健的 CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# 2. 确保上传目录在服务启动前就存在
UPLOAD_DIR = "./uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 3. 包含 API 路由
app.include_router(router)

@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "running", "api_docs": "/docs"}

if __name__ == "__main__":
    print("🚀 Contract Forge 后端启动中...")
    print("📖 接口文档地址: http://localhost:8000/docs")
    # 这里必须写 "backend.main:app" 而不是 "main:app"
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)