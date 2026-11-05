#!/usr/bin/env python3
"""Junta fatias base64 salvas pelo browser_batch (tool-results/*.txt) num mp4.
Uso: python3 join_b64.py out.mp4 file1.txt file2.txt ...
Cada arquivo é um JSON [{type, text}] onde text = '[javascript_tool:javascript_exec] "<b64>"...'.
"""
import sys, json, re, base64

out = sys.argv[1]
parts = []
for f in sys.argv[2:]:
    raw = open(f).read()
    try:
        d = json.load(open(f))
        texts = [x['text'] for x in d]
    except Exception:
        texts = [raw]  # resultado único vem como texto puro
    for t in texts:
        ms = re.findall(r'"([A-Za-z0-9+/=]{1000,})"', t)
        parts.extend(ms)
b64 = ''.join(parts)
data = base64.b64decode(b64)
open(out, 'wb').write(data)
print(out, len(parts), 'fatias', len(b64), 'chars', len(data), 'bytes')
