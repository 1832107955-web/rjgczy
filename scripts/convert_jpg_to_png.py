from PIL import Image
import os

in_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'images', 'create_ac_bill.jpg')
out_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'images', 'create_ac_bill.png')

img = Image.open(in_path)
img = img.convert('RGBA')
img.save(out_path)
print('Converted', in_path, '->', out_path)
