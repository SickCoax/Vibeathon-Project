from pathlib import Path
p=Path('backend/app.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('from functools import wraps\n', 'from functools import wraps\nfrom contextlib import contextmanager\n')
s=s.replace("def db():\n c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c\n", "@contextmanager\ndef db():\n c=sqlite3.connect(DB); c.row_factory=sqlite3.Row\n try:\n  with c: yield c\n finally:\n  c.close()\n")
p.write_text(s,encoding='utf-8')
