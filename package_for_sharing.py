#!/usr/bin/env python3
"""
打包话外项目用于分享给其他组员测试
排除 node_modules、__pycache__、.claude 等不需要的大文件
"""

import os
import sys
import io
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

# 修复编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 需要打包的文件和目录
INCLUDE_PATTERNS = [
    # 后端文件
    "server.py",
    "paratera.py",
    "start_backend.py",
    "huawai.sqlite3",
    # 前端文件（排除 node_modules）
    "frontend/src",
    "frontend/public",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/vite.config.ts",
    "frontend/tsconfig.json",
    "frontend/index.html",
    "frontend/.env.local",
    # 文档
    "README.md",
    "OPTIMIZATION-PLAN.md",
    "CHANGES.md",
    "TEST-REPORT.md",
    "START-HERE.md",
    # 测试脚本
    "test_safety.py",
    "test_api.py",
    "test_latency.py",
    "create_test_user.py",
    "create_test_parent.py",
]

# 排除的目录和文件
EXCLUDE_PATTERNS = [
    "node_modules",
    "__pycache__",
    ".claude",
    ".git",
    "*.pyc",
    ".DS_Store",
    "dist",
]

def should_exclude(path):
    """检查是否应该排除"""
    path_str = str(path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if path_str.endswith(pattern[1:]):
                return True
        elif pattern in path_str:
            return True
    return False

def create_package():
    """创建打包文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"huawai-test-package-{timestamp}.zip"
    package_path = PROJECT_ROOT.parent / package_name

    print(f"正在创建测试包: {package_name}")
    print("=" * 60)

    file_count = 0
    total_size = 0

    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pattern in INCLUDE_PATTERNS:
            full_path = PROJECT_ROOT / pattern

            if not full_path.exists():
                print(f"[跳过] {pattern} (不存在)")
                continue

            if full_path.is_file():
                if not should_exclude(full_path):
                    arcname = f"huawai/{pattern}"
                    zipf.write(full_path, arcname)
                    size = full_path.stat().st_size
                    total_size += size
                    file_count += 1
                    print(f"[添加] {pattern} ({size/1024:.1f} KB)")
            elif full_path.is_dir():
                dir_file_count = 0
                for root, dirs, files in os.walk(full_path):
                    # 过滤目录
                    dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]

                    for file in files:
                        file_path = Path(root) / file
                        if not should_exclude(file_path):
                            rel_path = file_path.relative_to(PROJECT_ROOT)
                            arcname = f"huawai/{rel_path}"
                            zipf.write(file_path, arcname)
                            size = file_path.stat().st_size
                            total_size += size
                            file_count += 1
                            dir_file_count += 1
                print(f"[添加] {pattern}/ ({dir_file_count} 个文件)")

    # 计算压缩包大小
    package_size = package_path.stat().st_size

    print("=" * 60)
    print(f"打包完成!")
    print(f"  文件数量: {file_count}")
    print(f"  原始大小: {total_size/1024/1024:.2f} MB")
    print(f"  压缩大小: {package_size/1024/1024:.2f} MB")
    print(f"  保存位置: {package_path}")
    print("=" * 60)

    # 创建接收方说明文件
    readme_path = PROJECT_ROOT.parent / "README-FOR-RECEIVER.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""# 话外项目测试包 - 接收方说明

## 环境要求

- Python 3.11+
- Node.js 18+
- Paratera API Key（请联系分享者获取）

## 快速开始

### 1. 解压文件

将压缩包解压到任意目录。

### 2. 启动后端

```powershell
cd huawai

# PowerShell 安全输入 API Key
$secret = Read-Host 'Paratera API Key' -AsSecureString
$env:LLM_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
$env:LLM_MODEL = 'Qwen3.7-Plus'
$env:LLM_CHAT_URL = 'https://llmapi.paratera.com/v1/chat/completions'
python server.py
```

### 3. 启动前端

打开另一个终端：

```bash
cd huawai/frontend
npm ci
npm run dev
```

### 4. 打开浏览器

访问 http://localhost:5174/

### 5. 登录测试

| 账号 | 密码 | 角色 |
|------|------|------|
| testchild | testpass123456 | 孩子 |
| testparent | testpass123456 | 家长 |

## 测试步骤

1. 浏览器1：使用 testchild 登录，进入"沟通翻译"，创建沟通空间，复制邀请码
2. 浏览器2：使用 testparent 登录，进入"亲子沟通"，输入邀请码加入
3. 测试消息发送和转译
4. 测试原话可见性（只有发送者能看到"看看原话"）
5. 测试安全检测（输入"不想活了"等高风险词）

## 注意事项

- huawai.sqlite3 包含测试用户数据，如需清空可删除后重启后端
- 前端 node_modules 需要重新安装（npm ci）
- API Key 不会包含在压缩包中，需要单独获取

## 常见问题

**Q: 前端启动失败？**
A: 确保 Node.js 版本 >= 18，删除 node_modules 后重新 npm ci

**Q: 后端启动失败？**
A: 确保 Python 版本 >= 3.11，检查端口 8000 是否被占用

**Q: 消息改写失败？**
A: 检查 API Key 是否正确配置，网络是否能访问 Paratera API
""")

    print(f"\n接收方说明已生成: {readme_path}")
    return package_path

if __name__ == "__main__":
    create_package()
