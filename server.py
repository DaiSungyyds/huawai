from contextlib import closing
import getpass, hashlib, json, os, secrets, sqlite3, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from paratera import chat

# 安全风险关键词检测
SAFETY_KEYWORDS = {
    'high': ['自杀', '不想活', '自残', '割腕', '去死', '跳楼', '烧炭', '安眠药'],
    'medium': ['抑郁', '焦虑', '失眠', '厌食', '绝望', '无助', '崩溃'],
}

def check_safety_risk(text):
    """检查文本中的安全风险关键词"""
    text_lower = text.lower()
    for level, keywords in SAFETY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return {'risk': level, 'detected': True}
    return {'risk': 'none', 'detected': False}

# 非暴力沟通转译提示词
NVC_PROMPT = '''基于非暴力沟通原则改写原话，包含四要素：
1. 观察：描述具体行为，不加评判（"你总是..."→"最近三次..."）
2. 感受：用精准情绪词（"我觉得你不爱我"→"我感到孤单"）
3. 需要：说明感受源于什么需要（"因为我需要被理解/陪伴/尊重"）
4. 请求：具体、正向、可执行（"你能多陪我吗"→"这周末我们能一起吃饭吗"）

避免：道德评判、进行比较、回避责任、强人所难
保持"温柔的坚定"——既尊重对方，也清晰表达自己

示例：
"你们从来不听我说话"→"最近我想说话时，感觉没有被听到，我有些失落。我希望我们能找个时间好好聊聊。"
"我讨厌你们"→"我现在很生气，因为我需要被理解。我想先自己待一会儿。"
"你们总是很忙"→"最近我们在一起的时间比较少，我感到孤单。我希望能有一些时间和你们待在一起。"'''

DB = os.environ.get('HUAWAI_DB', str(Path(__file__).with_name('huawai.sqlite3')))
LOCK = threading.RLock()

# 数据保留天数（可通过环境变量配置）
DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS', '30'))

def cleanup_old_data():
    """清理过期的消息和令牌数据"""
    try:
        with closing(connect()) as c, c:
            # 清理过期令牌
            c.execute('DELETE FROM tokens WHERE expires < ?', (time.time(),))
            # 清理过期房间（房间24小时过期）
            c.execute('DELETE FROM rooms WHERE expires < ?', (time.time(),))
            # 清理过期消息（基于文件修改时间，简化处理）
            # 注意：这里使用 rowid 作为近似，实际应该存储时间戳
            cutoff_rowid = c.execute('SELECT MIN(rowid) FROM messages WHERE rowid > (SELECT MAX(rowid) - 1000 FROM messages)').fetchone()[0] or 0
            if cutoff_rowid > 100:
                c.execute('DELETE FROM messages WHERE rowid < ?', (cutoff_rowid - 100,))
    except Exception:
        pass  # 清理失败不影响主流程

def connect():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.executescript('''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,account TEXT UNIQUE,name TEXT,role TEXT,salt TEXT,password TEXT);
CREATE TABLE IF NOT EXISTS tokens(token TEXT PRIMARY KEY,user TEXT,expires REAL);
CREATE TABLE IF NOT EXISTS rooms(id TEXT PRIMARY KEY,code TEXT UNIQUE,expires REAL);
CREATE TABLE IF NOT EXISTS members(room TEXT,user TEXT,role TEXT,UNIQUE(room,user),UNIQUE(room,role));
CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,room TEXT,user TEXT,client TEXT,data TEXT,UNIQUE(room,user,client));
CREATE TABLE IF NOT EXISTS practices(id TEXT PRIMARY KEY,user TEXT,data TEXT);
CREATE TABLE IF NOT EXISTS retries(session TEXT,client TEXT,data TEXT,UNIQUE(session,client));''')
    return c
class APIError(Exception):
    def __init__(self, code, message): self.code,self.message=code,message

def field(b,k,n=500):
    v=b.get(k)
    if not isinstance(v,str) or not v.strip() or len(v)>n: raise APIError(400,'参数不合法：'+k)
    return v.strip()
def password(p,s): return hashlib.scrypt(p.encode(),salt=bytes.fromhex(s),n=16384,r=8,p=1).hex()
def dispatch(c,method,path,b,token):
    now=time.time()
    if path=='/api/health': return {'ok':True,'modelConfigured':bool((os.getenv('LLM_API_KEY') or os.getenv('PARATERA_API_KEY')) and (os.getenv('LLM_MODEL') or os.getenv('PARATERA_MODEL')))}
    if path=='/api/auth/login' and method=='POST':
        account=field(b,'account',128); p=field(b,'password',128)
        u=c.execute('SELECT * FROM users WHERE account=?',(account,)).fetchone()
        salt=u['salt'] if u else '00'*16
        valid=secrets.compare_digest(password(p,salt),u['password'] if u else '0'*128)
        if not u or not valid or b.get('role')!=u['role']: raise APIError(401,'账号、密码或身份不匹配')
        t=secrets.token_urlsafe(32); c.execute('INSERT INTO tokens VALUES(?,?,?)',(hashlib.sha256(t.encode()).hexdigest(),u['id'],now+28800))
        return {'user':{k:u[k] for k in ('id','name','role')},'accessToken':t}
    digest=hashlib.sha256(token.encode()).hexdigest()
    u=c.execute('SELECT users.* FROM users JOIN tokens ON users.id=tokens.user WHERE token=? AND expires>?',(digest,now)).fetchone()
    if not u: raise APIError(401,'请重新登录')
    if path=='/api/auth/logout' and method=='POST':
        c.execute('DELETE FROM tokens WHERE token=?',(digest,)); return {'ok':True}
    # 用户数据删除接口（隐私保护）
    if path=='/api/user/data' and method=='DELETE':
        user_id = u['id']
        # 删除用户的所有消息
        c.execute('DELETE FROM messages WHERE user=?',(user_id,))
        # 删除用户的练习记录
        c.execute('DELETE FROM practices WHERE user=?',(user_id,))
        # 删除用户的所有令牌
        c.execute('DELETE FROM tokens WHERE user=?',(user_id,))
        # 删除用户的房间成员关系
        c.execute('DELETE FROM members WHERE user=?',(user_id,))
        return {'ok':True,'message':'数据已删除'}
    if path=='/api/communication/rooms' and method=='POST':
        if b.get('role')!=u['role']: raise APIError(403,'身份不匹配')
        rid=secrets.token_hex(16); code=secrets.token_hex(4).upper()
        c.execute('INSERT INTO rooms VALUES(?,?,?)',(rid,code,now+86400)); c.execute('INSERT INTO members VALUES(?,?,?)',(rid,u['id'],u['role']))
        return {'roomId':rid,'inviteCode':code}
    if path=='/api/communication/rooms/join' and method=='POST':
        r=c.execute('SELECT * FROM rooms WHERE code=? AND expires>?',(field(b,'inviteCode',32).upper(),now)).fetchone()
        if not r: raise APIError(404,'邀请码不存在或已过期')
        if b.get('role')!=u['role']: raise APIError(403,'身份不匹配')
        member=c.execute('SELECT user FROM members WHERE room=? AND role=?',(r['id'],u['role'])).fetchone()
        if member and member['user']!=u['id']: raise APIError(409,'该身份已有人加入')
        c.execute('INSERT OR IGNORE INTO members VALUES(?,?,?)',(r['id'],u['id'],u['role']))
        return {'roomId':r['id'],'inviteCode':r['code']}

    # 转译接口：只做转译，不保存消息
    if path == '/api/translate' and method == 'POST':
        text = field(b, 'text')
        # 安全风险检测
        safety = check_safety_risk(text)
        if safety['risk'] == 'high':
            return {'safetyAlert': True, 'riskLevel': 'high', 'message': '我们注意到你可能正在经历很困难的时刻。请先暂停一下，联系你信任的人聊聊。'}
        # 调用 AI 转译（基于非暴力沟通四要素）
        translated = chat([{'role': 'system', 'content': NVC_PROMPT}, {'role': 'user', 'content': text}])
        return {'original': text, 'translated': translated, 'safetyAlert': safety['detected'], 'riskLevel': safety['risk']}

    parts = path.split('/')
    if len(parts)==6 and parts[2:4]==['communication','rooms'] and parts[5]=='messages':
        rid=parts[4]
        if not c.execute('SELECT 1 FROM members WHERE room=? AND user=?',(rid,u['id'])).fetchone(): raise APIError(403,'无权访问此房间')
        if method=='GET': return [json.loads(r[0]) for r in c.execute('SELECT data FROM messages WHERE room=? ORDER BY rowid',(rid,))]
        if method!='POST': raise APIError(405,'方法不支持')
        if b.get('role')!=u['role']: raise APIError(403,'身份不匹配')
        text=field(b,'text'); client=field(b,'clientMessageId',128)
        old=c.execute('SELECT data FROM messages WHERE room=? AND user=? AND client=?',(rid,u['id'],client)).fetchone()
        if old: return json.loads(old[0])
        # 安全风险检测
        safety = check_safety_risk(text)
        if safety['risk'] == 'high':
            return {'safetyAlert': True, 'riskLevel': 'high', 'message': '我们注意到你可能正在经历很困难的时刻。请先暂停一下，联系你信任的人聊聊。'}
        # 支持前端传入自定义转译文本（用户编辑后的版本）
        custom_translated = b.get('translated')
        if custom_translated and isinstance(custom_translated, str) and custom_translated.strip():
            translated = custom_translated.strip()
        else:
            translated = chat([{'role': 'system', 'content': NVC_PROMPT}, {'role': 'user', 'content': text}])
        data = {'id': secrets.token_hex(16), 'role': u['role'], 'original': text, 'translated': translated, 'safetyAlert': safety['detected'], 'riskLevel': safety['risk']}
        if u['role']=='child':
            avatar=b.get('senderCompanionId','lamp')
            if avatar not in ['lamp','star','cloud','sprout','lantern']: raise APIError(400,'形象不合法')
            data['senderCompanionId']=avatar
        c.execute('INSERT INTO messages VALUES(?,?,?,?,?)',(data['id'],rid,u['id'],client,json.dumps(data)))
        return data
    if path=='/api/practice/start' and method=='POST':
        scene=field(b,'sceneId',32)
        scenes={'missing':'想和爸妈聊一会儿','phone':'商量手机使用时间','friend':'和朋友说开小误会'}
        if scene not in scenes: raise APIError(400,'未知场景')
        sid=secrets.token_hex(16)
        history=[{'role':'system','content':'你是温和的沟通练习伙伴，正在模拟：'+scenes[scene]+'。明确这是模拟，回应简短，帮助表达感受、需要和边界。不要诊断、羞辱、操纵或索取私人信息。'}]
        reply=chat(history+[{'role':'user','content':'请开始模拟，用一句话邀请我表达。'}])
        history.append({'role':'assistant','content':reply})
        data={'sessionId':sid,'reply':reply,'turn':0,'done':False,'history':history}
        c.execute('INSERT INTO practices VALUES(?,?,?)',(sid,u['id'],json.dumps(data)))
        return {k:v for k,v in data.items() if k!='history'}
    if path in ['/api/practice/reply','/api/practice/exit'] and method=='POST':
        sid=field(b,'sessionId',128)
        row=c.execute('SELECT data FROM practices WHERE id=? AND user=?',(sid,u['id'])).fetchone()
        if not row: raise APIError(404,'练习不存在')
        data=json.loads(row[0])
        if path.endswith('/exit'):
            data['done']=True
        else:
            client=field(b,'clientMessageId',128)
            old=c.execute('SELECT data FROM retries WHERE session=? AND client=?',(sid,client)).fetchone()
            if old: return json.loads(old[0])
            if data['done']: raise APIError(409,'练习已经结束')
            text=field(b,'text'); data['history'].append({'role':'user','content':text})
            data['turn']+=1; data['done']=data['turn']>=5
            if data['done']: data['history'].append({'role':'system','content':'结束本次练习。给出简短、具体、不做诊断的表达反馈。'})
            data['reply']=chat(data['history']); data['history'].append({'role':'assistant','content':data['reply']})
            if data['done']: data['feedback']=data['reply']
        c.execute('UPDATE practices SET data=? WHERE id=?',(json.dumps(data),sid))
        result={k:v for k,v in data.items() if k!='history'}
        if path.endswith('/reply'): c.execute('INSERT INTO retries VALUES(?,?,?)',(sid,client,json.dumps(result)))
        return result
    raise APIError(404,'接口不存在')

class Handler(BaseHTTPRequestHandler):
    attempts={}
    def log_message(self,*args): pass
    def do_GET(self): self.handle_api()
    def do_POST(self): self.handle_api()
    def handle_api(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<0 or length>16384: raise APIError(413,'请求过大')
            b=json.loads(self.rfile.read(length)) if length else {}
            if not isinstance(b,dict): raise APIError(400,'请求必须为对象')
            # 只锁速率限制，不锁整个请求（避免 LLM 调用阻塞其他请求）
            with LOCK:
                key=(self.client_address[0], 'login' if self.path=='/api/auth/login' else 'api')
                now=time.time(); times=[t for t in self.attempts.get(key,[]) if now-t<60]
                if len(times)>=(10 if key[1]=='login' else 120): raise APIError(429,'请求过于频繁，请稍后重试')
                self.attempts[key]=times+[now]
            # 数据库操作单独加锁
            with closing(connect()) as c, c: result=dispatch(c,self.command,self.path,b,self.headers.get('Authorization','').removeprefix('Bearer '))
            code,payload=200,{'data':result}
        except APIError as e: code,payload=e.code,{'message':e.message}
        except (ValueError,json.JSONDecodeError): code,payload=400,{'message':'请求格式错误'}
        except RuntimeError as e: code,payload=502,{'message':str(e)}
        except Exception: code,payload=500,{'message':'服务内部错误'}
        raw=json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--create-user'); p.add_argument('--role',choices=['child','parent']); p.add_argument('--name'); args=p.parse_args()
    if args.create_user:
        if not args.role: p.error('--role is required')
        secret=getpass.getpass('Password (at least 12 characters): ')
        if len(secret)<12 or len(secret)>128: p.error('Password length must be 12-128')
        salt=secrets.token_hex(16)
        with closing(connect()) as c, c: c.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',(secrets.token_hex(16),args.create_user,args.name or args.create_user,args.role,salt,password(secret,salt)))
        print('User created')
    else:
        connect().close(); print('Backend: http://127.0.0.1:8000')
        # 启动定期数据清理任务（每6小时执行一次）
        def cleanup_scheduler():
            while True:
                time.sleep(6 * 3600)  # 6小时
                cleanup_old_data()
        cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
        cleanup_thread.start()

        # 支持环境变量配置监听地址（Railway 使用 0.0.0.0）
        host = os.environ.get('HUAWAI_HOST', os.environ.get('HOST', '127.0.0.1'))
        port = int(os.environ.get('HUAWAI_PORT', os.environ.get('PORT', '8000')))
        print(f'Backend: http://{host}:{port}')
        ThreadingHTTPServer((host, port), Handler).serve_forever()

