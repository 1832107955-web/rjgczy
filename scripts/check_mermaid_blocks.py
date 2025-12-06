import re
import base64
import requests
import os
import io
from PIL import Image

MD_FILE = os.path.join(os.path.dirname(__file__), '..', 'design_document.md')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'images', 'checked')
os.makedirs(OUT_DIR, exist_ok=True)

def sanitize(text):
    # Remove stray quotes around participant/notes, replace <br> with \n, keep arrows
    t = text.replace('"', '').replace("'", '')
    t = re.sub(r'<\s*br\s*/?>', '\\n', t, flags=re.IGNORECASE)
    # normalize CRLF
    t = t.replace('\r\n', '\n').replace('\r', '\n')
    # remove control chars except newline and tab
    t = ''.join(ch for ch in t if ch == '\n' or ch == '\t' or (32 <= ord(ch) <= 126) or ord(ch) >= 0x4e00)
    return t

def render_mermaid(text):
    b64 = base64.urlsafe_b64encode(text.encode('utf-8')).decode('ascii')
    url = f'https://mermaid.ink/img/{b64}'
    try:
        r = requests.get(url, timeout=20)
    except Exception as e:
        return False, f'HTTP error: {e}', None
    if r.status_code == 200:
        ctype = r.headers.get('Content-Type','')
        if 'jpeg' in ctype or 'jpg' in ctype:
            img = Image.open(io.BytesIO(r.content)).convert('RGBA')
            return True, 'ok', img
        elif 'svg' in ctype:
            return True, 'svg', r.content
        else:
            return False, f'Unsupported Content-Type: {ctype}', None
    else:
        return False, f'HTTP {r.status_code}', None

def main():
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        md = f.read()

    blocks = re.findall(r'```mermaid\n(.*?)\n```', md, flags=re.S)
    results = []
    for i, blk in enumerate(blocks, start=1):
        orig = blk.strip()
        cleaned = sanitize(orig)
        ok, info, img = render_mermaid(cleaned)
        out = {'index': i, 'original': orig, 'cleaned': cleaned, 'ok': ok, 'info': info}
        if ok and img is not None:
            out_path = os.path.join(OUT_DIR, f'block_{i}.png')
            img.save(out_path, format='PNG')
            out['image'] = out_path
        elif ok and isinstance(img, bytes):
            out_path = os.path.join(OUT_DIR, f'block_{i}.svg')
            with open(out_path, 'wb') as f:
                f.write(img)
            out['image'] = out_path
        results.append(out)

    # Print summary
    for r in results:
        print('--- Block', r['index'], '---')
        print('OK:', r['ok'], 'Info:', r['info'])
        print('Image:', r.get('image'))
        print('Cleaned source:\n')
        print(r['cleaned'])
        print('\n')

    # Also return non-ok blocks for manual inspection
    bad = [r for r in results if not r['ok']]
    print('Summary: total', len(results), 'failed', len(bad))
    if bad:
        print('Failed block indices:', [b['index'] for b in bad])

if __name__ == '__main__':
    main()
