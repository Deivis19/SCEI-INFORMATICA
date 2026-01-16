from PIL import Image
import os

img_path = r"c:\xampp\htdocs\CMBP_INFORMATICA\scei\resources\images\palavecino.png"
ico_path = r"c:\xampp\htdocs\CMBP_INFORMATICA\icon.ico"

try:
    img = Image.open(img_path)
    # Resize to common icon sizes
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Successfully converted {img_path} to {ico_path}")
except Exception as e:
    print(f"Error converting image: {e}")
