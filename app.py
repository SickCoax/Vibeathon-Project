import os, re, sqlite3, secrets, json, requests
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

ROOT=os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT,'.env'))
DB=os.path.join(ROOT,'vibeshift.sqlite3')
app=Flask(__name__)
app.secret_key=os.getenv('FLASK_SECRET_KEY') or 'local-development-only-change-this'
app.config.update(MAX_CONTENT_LENGTH=6*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','0')=='1')
PERSONAS={
'Executive / C-Level':'Be concise, professional, decision-oriented, and focused on business outcomes.',
'Supportive Peer':'Be friendly, constructive, empathetic, collaborative, and encouraging.',
'Legal / Compliance':'Be precise, neutral, formal, unambiguous, and careful about claims. This is not legal advice.',
'Gen-Z Hype':'Be casual, energetic, expressive, and contemporary without forcing slang.'}

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
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
def health(): return jsonify(status='ok',provider_configured=bool(os.getenv('AI_API_KEY')))
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
 api=os.getenv('AI_API_KEY'); base=os.getenv('AI_BASE_URL','https://api.openai.com/v1'); model=os.getenv('AI_MODEL')
 if not api or not model:return jsonify(error='AI_API_KEY and AI_MODEL are not configured. Add them to backend/.env to enable real AI transformations.'),503
 target='Preserve the original language.' if language=='Keep original language' else f'Write in {language}.'
 prompt=f"Rewrite the message using this persona: {PERSONAS[persona]} Length preference: {length}. {target} Context: {str(data.get('context',''))[:500]}. Audience: {str(data.get('audience',''))[:300]}. Preserve all facts, names, dates, intent, and commitments. Do not invent details. Return only the rewritten message."
 try:
  resp=requests.post(base.rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+api,'Content-Type':'application/json'},json={'model':model,'messages':[{'role':'system','content':prompt},{'role':'user','content':text}], 'temperature':0.4},timeout=45)
  if resp.status_code==429:return jsonify(error='The AI provider quota is currently unavailable. Please try again later.'),503
  resp.raise_for_status(); rewritten=resp.json()['choices'][0]['message']['content'].strip()
  if not rewritten: raise ValueError('Empty provider response')
 except requests.Timeout:return jsonify(error='The AI provider took too long to respond. Please retry.'),504
 except Exception:return jsonify(error='The AI provider could not complete this request. Check server configuration and try again.'),502
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
@app.post('/api/analyze-image')
def analyze_image():
 f=request.files.get('image')
 if not f:return jsonify(error='Choose an image to analyze.'),400
 if f.mimetype not in ['image/png','image/jpeg','image/webp'] or len(f.read())>5*1024*1024:return jsonify(error='Upload a PNG, JPEG, or WebP image under 5 MB.'),400
 return jsonify(error='Image OCR is not configured. No text was extracted; set up an OCR provider to enable this feature.'),503
@app.post('/api/transcribe')
def transcribe():return jsonify(error='Server transcription is not configured. Browser speech recognition may be available in Chrome or Edge.'),503
if __name__=='__main__':app.run(host='127.0.0.1',port=5000,debug=False)


