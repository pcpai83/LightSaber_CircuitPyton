import os
from PIL import Image
import numpy as np

def bmp_to_bin_rgb_resample(bmp_path, bin_path, num_leds=80):
    bmp = Image.open(bmp_path)
    if bmp.mode != "RGB":
        bmp = bmp.convert("RGB")
    with open(bin_path, "wb") as f:
        for y in reversed(range(bmp.height)):  # de baixo para cima
            src_x = np.linspace(0, bmp.width-1, num=num_leds)
            row = [bmp.getpixel((int(x), y)) for x in src_x]
            for rgb in row:
                f.write(bytes([int(v) for v in rgb[:3]]))

def process_folder(root_folder, num_leds=80):
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith('.bmp'):
                bmp_path = os.path.join(dirpath, filename)
                bin_path = os.path.splitext(bmp_path)[0] + f".bin"
                print(f"Convertendo: {bmp_path} -> {bin_path}")
                bmp_to_bin_rgb_resample(bmp_path, bin_path, num_leds)
    print("Conversão completa.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python bmp_folder2bin.py <pasta> <num_leds>")
        sys.exit(1)
    folder = sys.argv[1]
    num_leds = int(sys.argv[2])
    process_folder(folder, num_leds)
