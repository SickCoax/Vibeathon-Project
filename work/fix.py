from pathlib import Path
p=Path('src/App.tsx'); s=p.read_text(encoding='utf-8-sig')
s=s.replace("const wc=(s:string)=>s.trim()?s.trim().split(/\\s+/).length:0;", "const wc=(s:string)=>s.trim()?s.trim().split(/\\s+/).length:0;\nasync function readJSON(r:Response){const raw=await r.text();try{return raw?JSON.parse(raw):{}}catch{throw Error(r.ok?'The server returned an invalid response.':'Could not read the server response. Make sure the Flask API is running on port 5000, then retry.')}}")
s=s.replace('const d=await r.json();if(!r.ok)throw Error(d.error||\'Unable to transform message.\');','const d=await readJSON(r);if(!r.ok)throw Error(d.error||\'Unable to transform message.\');')
s=s.replace("const r=await fetch('/api/analyze-image',{method:'POST',body:fd}),d=await r.json();", "const r=await fetch('/api/analyze-image',{method:'POST',body:fd}),d=await readJSON(r);")
p.write_text(s,encoding='utf-8')
