from pathlib import Path
p=Path('backend/app.py'); s=p.read_text(encoding='utf-8-sig')
s=s.replace("def health(): return jsonify(status='ok',provider_configured=bool(os.getenv('AI_API_KEY')))\n", "def health(): return jsonify(status='ok',provider_configured=bool(os.getenv('AI_API_KEY')),provider='gemini' if 'generativelanguage.googleapis.com' in os.getenv('AI_BASE_URL','https://generativelanguage.googleapis.com/v1beta/openai/') else 'openai-compatible')\n")
s=s.replace(" api=os.getenv('AI_API_KEY'); base=os.getenv('AI_BASE_URL','https://api.openai.com/v1'); model=os.getenv('AI_MODEL')\n if not api or not model:return jsonify(error='AI_API_KEY and AI_MODEL are not configured. Add them to backend/.env to enable real AI transformations.'),503\n", " api=(os.getenv('AI_API_KEY') or '').strip(); base=os.getenv('AI_BASE_URL','https://generativelanguage.googleapis.com/v1beta/openai/').strip(); model=os.getenv('AI_MODEL','gemini-3.5-flash-lite').strip()\n if not api:return jsonify(error='AI_API_KEY is missing. Create a Gemini API key in Google AI Studio and add it to backend/.env. No inference was attempted.'),503\n if not base or not model:return jsonify(error='AI_BASE_URL and AI_MODEL must be configured in backend/.env.'),503\n")
old=""" try:
  resp=requests.post(base.rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+api,'Content-Type':'application/json'},json={'model':model,'messages':[{'role':'system','content':prompt},{'role':'user','content':text}], 'temperature':0.4},timeout=45)
  if resp.status_code==429:return jsonify(error='The AI provider quota is currently unavailable. Please try again later.'),503
  resp.raise_for_status(); rewritten=resp.json()['choices'][0]['message']['content'].strip()
  if not rewritten: raise ValueError('Empty provider response')
 except requests.Timeout:return jsonify(error='The AI provider took too long to respond. Please retry.'),504
 except Exception:return jsonify(error='The AI provider could not complete this request. Check server configuration and try again.'),502
"""
new=""" try:
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
"""
if old not in s: raise SystemExit('provider block did not match')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
Path('backend/.env.example').write_text('''# Optional session security; replace before any shared/public deployment.\nFLASK_SECRET_KEY=replace-with-a-long-random-secret\n\n# Gemini API (OpenAI-compatible endpoint). Create a key in Google AI Studio.\n# This is a free-tier model default; the key must belong to a project without billing enabled\n# to prevent paid usage. Do not commit backend/.env.\nAI_API_KEY=\nAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/\nAI_MODEL=gemini-3.5-flash-lite\nCOOKIE_SECURE=0\n''',encoding='utf-8')
