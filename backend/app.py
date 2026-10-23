import os, re, sqlite3, secrets, json, requests, base64
from datetime import datetime, timezone
from functools import wraps
from contextlib import contextmanager
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

ROOT=os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT,'.env'), override=True)
DB=os.path.join(ROOT,'vibeshift.sqlite3')
app=Flask(__name__)
app.secret_key=os.getenv('FLASK_SECRET_KEY') or 'local-development-only-change-this'
app.config.update(MAX_CONTENT_LENGTH=6*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','0')=='1')
PERSONAS={
'Executive / C-Level':'Be concise, professional, decision-oriented, and focused on business outcomes.',
'Supportive Peer':'Be friendly, constructive, empathetic, collaborative, and encouraging.',
'Legal / Compliance':'Be precise, neutral, formal, unambiguous, and careful about claims. This is not legal advice.',
'Gen-Z Hype':'Be casual, energetic, expressive, and contemporary without forcing slang.'}

@contextmanager
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 try:
  with c: yield c
 finally:
  c.close()
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY,user_id INTEGER,original TEXT,rewritten TEXT,persona TEXT,length TEXT,tone TEXT,created_at TEXT,FOREIGN KEY(user_id) REFERENCES users(id))')

def current_user(): return session.get('user_id')
def auth(fn):
 @wraps(fn)
 def inner(*a,**kw):
  if not current_user(): return jsonify(error='Please log in to access this feature.'),401
  return fn(*a,**kw)
 return inner

def tone(text):
 s=text.strip(); low=s.lower(); words=re.findall(r"[\w’'-]+",s)
 cues=[]
 for term in ['please','thank you','appreciate','sorry','frustrated','urgent','asap','probably','maybe','I think','must','immediately','excited','great','concerned']:
  m=re.search(re.escape(term),s,re.I)
  if m and len(cues)<4: cues.append(m.group(0))
 form=70 if any(x in low for x in ['please','regards','dear ','sincerely']) else 45
 professional=min(95,35+sum(x in low for x in ['please','thank you','regards','deadline','project','team'])*10)
 intensity=min(95,25+sum(x in s for x in ['!','!!','?'])*12+sum(x in low for x in ['urgent','asap','immediately','must'])*15)
 sentiment='positive' if any(x in low for x in ['great','thanks','appreciate','excited','happy','love']) else 'negative' if any(x in low for x in ['angry','frustrated','bad','problem','issue','disappointed','sorry']) else 'neutral'
 labels=[sentiment.title(), 'Formal' if form>=60 else 'Conversational']
 direct='diplomatic' if any(x in low for x in ['maybe','probably','I think','could we','would it']) else 'direct'
 return {'summary':f'The message reads as {sentiment} and {direct}, with {"moderate" if intensity<60 else "elevated"} perceived intensity. This is a text-based estimate.', 'labels':labels,'formality':form,'professionalism':professional,'intensity':intensity,'sentiment':sentiment,'directness':direct,'cues':cues}

def serialize(row):
 return {'id':row['id'],'original':row['original'],'rewritten':row['rewritten'],'persona':row['persona'],'length':row['length'],'tone':json.loads(row['tone']),'created_at':row['created_at']}

@app.after_request
def csrf_header(res):
 res.headers['X-Content-Type-Options']='nosniff'; res.headers['Referrer-Policy']='strict-origin-when-cross-origin'; return res
@app.get('/api/health')
def health():
 base=os.getenv('AI_BASE_URL','https://generativelanguage.googleapis.com/v1beta/openai/')
 return jsonify(application='vibeshift-ai',backend_port=int(os.getenv('PORT','5001')),status='ok',provider_configured=bool((os.getenv('AI_API_KEY') or '').strip()),provider='gemini' if 'generativelanguage.googleapis.com' in base else 'openai-compatible')
@app.get('/api/session')
def session_status():
 if not current_user(): return jsonify(authenticated=False)
 with db() as c: u=c.execute('SELECT email FROM users WHERE id=?',(current_user(),)).fetchone()
 return jsonify(authenticated=bool(u),email=u['email'] if u else None)
@app.post('/api/register')
def register():
 data=request.get_json(silent=True) or {}; email=str(data.get('email','')).strip().lower(); password=str(data.get('password',''))
 if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(password)<10:return jsonify(error='Enter a valid email and a password with at least 10 characters.'),400
 try:
  with db() as c: cur=c.execute('INSERT INTO users(email,password) VALUES(?,?)',(email,generate_password_hash(password)))
  session.clear(); session['user_id']=cur.lastrowid
 except sqlite3.IntegrityError:return jsonify(error='An account with that email already exists.'),409
 return jsonify(authenticated=True,email=email),201
@app.post('/api/login')
def login():
 data=request.get_json(silent=True) or {}; email=str(data.get('email','')).strip().lower()
 with db() as c:u=c.execute('SELECT id,email,password FROM users WHERE email=?',(email,)).fetchone()
 if not u or not check_password_hash(u['password'],str(data.get('password',''))):return jsonify(error='Email or password is incorrect.'),401
 session.clear();session['user_id']=u['id'];return jsonify(authenticated=True,email=u['email'])
@app.post('/api/logout')
def logout():session.clear();return jsonify(authenticated=False)
@app.post('/api/transform')
def transform():
 data=request.get_json(silent=True) or {}; text=data.get('text')
 if not isinstance(text,str) or not text.strip() or len(text)>5000:return jsonify(error='Enter a message between 1 and 5,000 characters.'),400
 persona=data.get('persona','Executive / C-Level'); length=data.get('length','Keep original length'); language=data.get('language','Keep original language')
 if persona not in PERSONAS or length not in ['Make shorter','Keep original length','Make longer']:return jsonify(error='Choose a valid persona and length preference.'),400
 api=(os.getenv('AI_API_KEY') or '').strip(); base=os.getenv('AI_BASE_URL','https://generativelanguage.googleapis.com/v1beta/openai/').strip(); model=os.getenv('AI_MODEL','gemini-3.5-flash-lite').strip()
 if not api:return jsonify(error='AI_API_KEY is missing. Create a Gemini API key in Google AI Studio and add it to backend/.env. No inference was attempted.'),503
 if not base or not model:return jsonify(error='AI_BASE_URL and AI_MODEL must be configured in backend/.env.'),503
 target='Preserve the original language.' if language=='Keep original language' else f'Write in {language}.'
 prompt=f"Rewrite the message using this persona: {PERSONAS[persona]} Length preference: {length}. {target} Context: {str(data.get('context',''))[:500]}. Audience: {str(data.get('audience',''))[:300]}. Preserve all facts, names, dates, intent, and commitments. Do not invent details. Return only the rewritten message."
 try:
  resp=requests.post(base.rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+api,'Content-Type':'application/json'},json={'model':model,'messages':[{'role':'system','content':prompt},{'role':'user','content':text}], 'temperature':0.4},timeout=(5,45))
 except requests.Timeout:
  return jsonify(error='The AI provider timed out. Please retry; no rewrite was returned.'),504
 except requests.ConnectionError:
  return jsonify(error='Could not reach the AI provider. Check the network and AI_BASE_URL, then retry.'),502
 except requests.RequestException:
  return jsonify(error='The AI provider request failed before a response arrived. Check network access and try again.'),502
 if resp.status_code in (401,403):
  return jsonify(error='The AI provider rejected AI_API_KEY. Check that the key is valid and belongs to the configured provider.'),502
 if resp.status_code==429:
  return jsonify(error='The AI provider quota or rate limit is exhausted. Check the provider quota dashboard or retry later; billing was not changed.'),503
 if resp.status_code in (400,404):
  return jsonify(error='The provider rejected AI_MODEL or the request format. Confirm the model is available to this key and matches AI_BASE_URL.'),502
 if resp.status_code>=500:
  return jsonify(error='The AI provider is temporarily unavailable. Please retry later.'),502
 if not resp.ok:
  return jsonify(error=f'The AI provider returned an unexpected HTTP {resp.status_code} response.'),502
 try:
  payload=resp.json()
  rewritten=payload['choices'][0]['message']['content']
  if not isinstance(rewritten,str) or not rewritten.strip(): raise ValueError('No text content')
  rewritten=rewritten.strip()
 except (ValueError,KeyError,IndexError,TypeError):
  return jsonify(error='The AI provider returned an invalid response. No rewrite was saved.'),502
 t=tone(text); item={'original':text,'rewritten':rewritten,'persona':persona,'length':length,'tone':t,'created_at':datetime.now(timezone.utc).isoformat()}
 if current_user():
  with db() as c: cur=c.execute('INSERT INTO history(user_id,original,rewritten,persona,length,tone,created_at) VALUES(?,?,?,?,?,?,?)',(current_user(),text,rewritten,persona,length,json.dumps(t),item['created_at']));item['id']=cur.lastrowid
 return jsonify(item)
@app.get('/api/history')
@auth
def get_history():
 with db() as c: rows=c.execute('SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT 100',(current_user(),)).fetchall()
 return jsonify([serialize(r) for r in rows])
@app.get('/api/history/<int:item_id>')
@auth
def get_one(item_id):
 with db() as c:r=c.execute('SELECT * FROM history WHERE id=? AND user_id=?',(item_id,current_user())).fetchone()
 return (jsonify(serialize(r)),200) if r else (jsonify(error='History item not found.'),404)
@app.delete('/api/history/<int:item_id>')
@auth
def delete_one(item_id):
 with db() as c:c.execute('DELETE FROM history WHERE id=? AND user_id=?',(item_id,current_user()))
 return '',204
@app.delete('/api/history')
@auth
def clear_history():
 with db() as c:c.execute('DELETE FROM history WHERE user_id=?',(current_user(),))
 return '',204
@app.post('/api/analyze-tone')
def analyze_tone():
 data=request.get_json(silent=True) or {}; text=data.get('text','')
 if not isinstance(text,str) or len(text)>5000:return jsonify(error='Text must be at most 5,000 characters.'),400
 return jsonify(tone(text))
def detect_image_mime(data):
 if data.startswith(b'\x89PNG\r\n\x1a\n'): return 'image/png'
 if data.startswith(b'\xff\xd8\xff'): return 'image/jpeg'
 if len(data)>=12 and data[:4]==b'RIFF' and data[8:12]==b'WEBP': return 'image/webp'
 return None

def vision_connection_error(exc):
 """Return a safe network diagnosis without exposing request data."""
 kinds={type(exc).__name__}
 pending=list(exc.args)
 while pending:
  value=pending.pop()
  if isinstance(value,BaseException):
   kinds.add(type(value).__name__); pending.extend(value.args)
  elif isinstance(value,str):
   for name in ('NameResolutionError','NewConnectionError','ProtocolError','SSLError','ProxyError'):
    if name in value:kinds.add(name)
 if 'SSLError' in kinds:
  message='TLS negotiation with Google Gemini failed before an HTTP response. Check the system clock, certificate trust, and network inspection settings.'
 elif 'ProxyError' in kinds:
  message='The configured network proxy could not connect to Google Gemini. Check proxy access and retry.'
 elif 'NameResolutionError' in kinds or 'gaierror' in kinds:
  message='DNS could not resolve Google Gemini before an HTTP response. Check DNS/network access and retry.'
 elif 'NewConnectionError' in kinds:
  message='A connection to Google Gemini could not be opened; no HTTP response was received. Check outbound HTTPS access and retry.'
 elif 'ProtocolError' in kinds:
  message='The network connection to Google Gemini was interrupted before an HTTP response. Retry and check the network path if it continues.'
 else:
  message='The connection to Google Gemini failed before any HTTP response was received. Retry and check outbound HTTPS access.'
 app.logger.warning('Gemini image request failed before HTTP response (cause=%s)', ','.join(sorted(kinds)))
 return message

@app.post('/api/analyze-image')
def analyze_image():
 upload=request.files.get('image')
 if not upload:return jsonify(error='Choose an image to analyze.'),400
 image_data=upload.stream.read(5*1024*1024+1)
 if len(image_data)>5*1024*1024:return jsonify(error='Images must be 5 MB or smaller.'),413
 mime=detect_image_mime(image_data)
 if not mime:return jsonify(error='The uploaded file is not a supported PNG, JPEG, or WebP image.'),415
 question=(request.form.get('question') or '').strip()
 if len(question)>500:return jsonify(error='Image questions must be 500 characters or fewer.'),400
 api=(os.getenv('AI_API_KEY') or '').strip(); base=os.getenv('AI_BASE_URL','https://generativelanguage.googleapis.com/v1beta/openai/').strip(); model=os.getenv('AI_MODEL','gemini-3.5-flash-lite').strip()
 if not api:return jsonify(error='AI_API_KEY is missing. Add it to backend/.env before analyzing images. No image was sent.'),503
 if not base or not model:return jsonify(error='AI_BASE_URL and AI_MODEL must be configured in backend/.env.'),503
 question_rule=f'Also answer this user question using only visible evidence: {question!r}. If it cannot be answered reliably, state the uncertainty.' if question else 'Set question_answer to an empty string.'
 prompt=('Inspect the attached image and return a JSON object with exactly two string fields: summary and question_answer. '
         'The summary must naturally describe the important visible subjects, objects, scene, actions, spatial relations, colors, and readable text when relevant. '
         'Only state details supported by the pixels. Do not infer identities, occupations, intentions, or internal emotions. '
         'Acknowledge blur, occlusion, ambiguity, and uncertain counts instead of guessing. '
         f'{question_rule} The summary must not depend on a presumed image category.')
 encoded=base64.b64encode(image_data).decode('ascii')
 try:
  resp=requests.post(base.rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+api,'Content-Type':'application/json'},json={
   'model':model,'messages':[{'role':'system','content':'You are a careful visual description assistant. Ground every claim in the supplied image.'},
   {'role':'user','content':[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':f'data:{mime};base64,{encoded}'}}]}],
   'response_format':{'type':'json_object'},'temperature':0.2},timeout=(5,60))
 except requests.ConnectTimeout:return jsonify(error='The connection to Google Gemini timed out before an HTTP response. Check outbound HTTPS access and retry.'),504
 except requests.ReadTimeout:return jsonify(error='Google Gemini did not finish processing the image before the request timed out. Retry; no description was returned.'),504
 except requests.Timeout:return jsonify(error='The Gemini image request timed out before a complete response arrived. Retry; no description was returned.'),504
 except requests.ConnectionError as exc:return jsonify(error=vision_connection_error(exc)),502
 except requests.RequestException:return jsonify(error='The vision provider request failed before a response arrived. Check network access and try again.'),502
 if resp.status_code in (401,403):return jsonify(error='The AI provider rejected AI_API_KEY. Check that the key is valid and belongs to the configured provider.'),502
 if resp.status_code==429:return jsonify(error='The AI provider quota or rate limit is exhausted. Check the provider quota dashboard or retry later; billing was not changed.'),503
 if resp.status_code==404:return jsonify(error=f'Gemini could not find AI_MODEL "{model}" at the configured endpoint (HTTP 404). Check the model identifier and endpoint.'),502
 if resp.status_code==400:return jsonify(error='Gemini rejected the image-analysis request (HTTP 400). The configured model may reject the image format or JSON response mode; check the request format and model capabilities.'),502
 if resp.status_code>=500:return jsonify(error='The vision provider is temporarily unavailable. Please retry later.'),502
 if not resp.ok:return jsonify(error=f'The vision provider returned an unexpected HTTP {resp.status_code} response.'),502
 try:
  provider_data=resp.json(); content=provider_data['choices'][0]['message']['content']
  if isinstance(content,list):content=''.join(part.get('text','') for part in content if isinstance(part,dict))
  if not isinstance(content,str):raise ValueError('No text content')
  if content.strip().startswith('```'):
   content=re.sub(r'^```(?:json)?\s*|\s*```$','',content.strip(),flags=re.I)
  result=json.loads(content)
  summary=result.get('summary'); answer=result.get('question_answer','')
  if not isinstance(summary,str) or not summary.strip() or not isinstance(answer,str):raise ValueError('Missing description')
 except (ValueError,KeyError,IndexError,TypeError,AttributeError):
  return jsonify(error='The vision provider returned an invalid response. No description was accepted.'),502
 return jsonify(image_summary=summary.strip(),question_answer=answer.strip(),model=model)
@app.post('/api/transcribe')
def transcribe():return jsonify(error='Server transcription is not configured. Browser speech recognition may be available in Chrome or Edge.'),503
if __name__=='__main__':app.run(host='127.0.0.1',port=int(os.getenv('PORT','5001')),debug=False)




