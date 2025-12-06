import sys
import os
import base64
import requests

def sanitize(text: str) -> str:
    t = text.replace('"', '').replace("'", '')
    t = t.replace('<br/>', '\n').replace('<br>', '\n')
    t = t.replace('\r\n', '\n').replace('\r', '\n')
    return t

def render(mermaid_text: str, out_basename: str):
    b64 = base64.urlsafe_b64encode(mermaid_text.encode('utf-8')).decode('ascii')
    svg_url = f'https://mermaid.ink/svg/{b64}'
    img_url = f'https://mermaid.ink/img/{b64}'

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'images')
    os.makedirs(out_dir, exist_ok=True)

    try:
        r = requests.get(svg_url, timeout=20)
        r.raise_for_status()
        svg_path = os.path.join(out_dir, out_basename + '.svg')
        with open(svg_path, 'wb') as f:
            f.write(r.content)
        print('Wrote', svg_path)
    except Exception as e:
        print('SVG render failed:', e)

    try:
        r2 = requests.get(img_url, timeout=20)
        r2.raise_for_status()
        png_path = os.path.join(out_dir, out_basename + '.png')
        with open(png_path, 'wb') as f2:
            f2.write(r2.content)
        print('Wrote', png_path)
    except Exception as e:
        print('PNG render failed:', e)


def main():
    if len(sys.argv) < 3:
        print('Usage: python render_mermaid_single.py <input.mmd> <output_basename>')
        sys.exit(2)
    in_path = sys.argv[1]
    out_basename = sys.argv[2]
    with open(in_path, 'r', encoding='utf-8') as f:
        text = f.read()
    cleaned = sanitize(text)
    render(cleaned, out_basename)

if __name__ == '__main__':
    main()
