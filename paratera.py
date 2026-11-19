"""Server-side Paratera adapter. No credentials are stored in source."""
import json
import os
import time
import urllib.request
import urllib.error


def chat(messages, max_retries=2):
    """调用 LLM，支持自动重试"""
    key = os.environ.get('LLM_API_KEY') or os.environ.get('PARATERA_API_KEY', '')
    model = os.environ.get('LLM_MODEL') or os.environ.get('PARATERA_MODEL', '')
    if not key or not model:
        raise RuntimeError('请配置 LLM_API_KEY 和 LLM_MODEL')
    endpoint = os.environ.get('LLM_CHAT_URL') or os.environ.get('PARATERA_CHAT_URL', 'https://llmapi.paratera.com/v1/chat/completions')
    body = json.dumps({'model': model, 'messages': messages, 'stream': False, 'max_tokens': 300, 'temperature': 0.7}).encode()

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(endpoint, data=body, headers={
                'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.load(response)
            content = result['choices'][0]['message']['content']
            if not isinstance(content, str) or not content.strip():
                raise ValueError('empty response')
            return content
        except urllib.error.HTTPError as exc:
            last_error = RuntimeError(f'模型服务返回 HTTP {exc.code}，请检查额度、模型权限和配置')
            if exc.code in (429, 500, 502, 503) and attempt < max_retries:
                time.sleep(1 * (attempt + 1))  # 递增等待
                continue
            raise last_error from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = RuntimeError('模型服务连接失败或超时')
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
                continue
            raise last_error from None
        except (KeyError, IndexError, ValueError, TypeError):
            raise RuntimeError('模型服务响应格式不符合预期') from None
    raise last_error


if __name__ == '__main__':
    print(chat([{'role': 'user', 'content': '请只回复：连接成功'}]))
