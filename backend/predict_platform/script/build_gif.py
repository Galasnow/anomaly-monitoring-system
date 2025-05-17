import os
import random
from PIL import Image, ImageDraw, ImageSequence

def pngs2gif(png_path, gif_name):
    """png帧图生成gif图像"""
    frames = []
    png_files = os.listdir(png_path)
    for frame_id in range(len(png_files)):
        frame = Image.open(os.path.join(png_path, png_files[frame_id]))
        frames.append(frame)
    # frames.reverse()  # 将图像序列逆转
    frames[0].save(gif_name, save_all=True, append_images=frames[1:], loop=0, duration=300, disposal=2)


if __name__ == '__main__':
    # gif2pngs('下班了.gif', 'images')
    pngs2gif('D:/zhongyan/functionality_test/predict', 'D:/zhongyan/functionality_test/tmp.gif')
