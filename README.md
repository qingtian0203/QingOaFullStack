# QingOaFullStack

全栈透明 OA 演示项目总仓库，用于 QingAgent 自动化测试实验。

## 目录规划

```text
QingOaFullStack/
├── API_QingOA/      # FastAPI + SQLite 接口后台
├── App_QingOA/      # Android App，后续放置
└── WAP_QingOA/      # WAP / H5 页面，v2 再加入
```

当前已完成 `API_QingOA` v1.0。

## 后端启动

```bash
cd /Users/konglingjia/AIProject/QingOaFullStack/API_QingOA
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

默认端口：`8010`。

