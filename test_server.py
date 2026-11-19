import os,tempfile,unittest,json
import server
class Contracts(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=os.path.dirname(__file__)); server.DB=os.path.join(self.temp.name,'test.db'); self.c=server.connect(); self.original=server.chat; server.chat=lambda m:'测试模型回复'
  self.tokens={}
  for a,r in [('kid','child'),('adult','parent'),('outsider','child')]:
   salt='11'*16; self.c.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',(a,a,a,r,salt,server.password('correct-password',salt)))
   self.tokens[a]=self.call('/auth/login',{'account':a,'password':'correct-password','role':r})['accessToken']
 def tearDown(self):
  server.chat=self.original; self.c.close(); self.temp.cleanup()
 def call(self,path,body=None,user='kid',method='POST'):
  return server.dispatch(self.c,method,'/api'+path,body or {},self.tokens.get(user,''))
 def test_room_access_idempotency(self):
  room=self.call('/communication/rooms',{'role':'child'})
  with self.assertRaises(server.APIError) as e:self.call('/communication/rooms/'+room['roomId']+'/messages',user='outsider',method='GET')
  self.assertEqual(e.exception.code,403)
  self.call('/communication/rooms/join',{'inviteCode':room['inviteCode'],'role':'parent'},'adult')
  path='/communication/rooms/'+room['roomId']+'/messages'; body={'role':'child','text':'你好','clientMessageId':'one'}
  a=self.call(path,body); self.assertEqual(a,self.call(path,body)); self.assertEqual(len(self.call(path,user='adult',method='GET')),1)
  with self.assertRaises(server.APIError):self.call(path,dict(body,role='parent'))
 def test_practice_ownership_and_end(self):
  p=self.call('/practice/start',{'sceneId':'missing'}); sid=p['sessionId']
  with self.assertRaises(server.APIError):self.call('/practice/reply',{'sessionId':sid,'text':'hi','clientMessageId':'x'},'outsider')
  for i in range(5):
   body={'sessionId':sid,'text':'我想聊聊','clientMessageId':str(i)}; p=self.call('/practice/reply',body); self.assertEqual(p,self.call('/practice/reply',body))
  self.assertTrue(p['done']); self.assertIn('feedback',p)
  with self.assertRaises(server.APIError):self.call('/practice/reply',dict(body,clientMessageId='six'))
 def test_login_and_expiration(self):
  with self.assertRaises(server.APIError):self.call('/auth/login',{'account':'kid','password':'wrong','role':'child'})
  self.call('/auth/logout')
  with self.assertRaises(server.APIError):self.call('/communication/rooms',{'role':'child'})
 def test_upstream_failure_does_not_save_message(self):
  room=self.call('/communication/rooms',{'role':'child'}); path='/communication/rooms/'+room['roomId']+'/messages'
  def fail(m):raise RuntimeError('upstream failed')
  server.chat=fail
  with self.assertRaises(RuntimeError):self.call(path,{'role':'child','text':'你好','clientMessageId':'x'})
  self.assertEqual(self.call(path,method='GET'),[])
if __name__=='__main__':unittest.main()

