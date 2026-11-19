"""Interactive local launcher. Secrets stay in process memory."""
import getpass
import os
from pathlib import Path
import subprocess
import sys

os.chdir(Path(__file__).resolve().parent)
print('话外本地后端：使用支持 Chat Completions 的 API。')
url = input('完整接口 URL [https://llmapi.paratera.com/v1/chat/completions]: ').strip()
os.environ['LLM_CHAT_URL'] = url or 'https://llmapi.paratera.com/v1/chat/completions'
os.environ['LLM_MODEL'] = input('模型 ID（从供应商控制台复制）: ').strip()
os.environ['LLM_API_KEY'] = getpass.getpass('你自己的 API Key（输入不可见，不保存到文件）: ').strip()
if not os.environ['LLM_MODEL'] or not os.environ['LLM_API_KEY']:
    sys.exit('模型和密钥不能为空')
subprocess.run([sys.executable, 'server.py'], check=True)
