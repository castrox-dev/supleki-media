#!/usr/bin/env python3
"""Cobre texto indesejado na parte de cima da tela facial do Popó.
Uso: python3 fix_popo_face.py in.mp4 out.mp4 [frac=0.30]
Por frame: acha a maior região escura (tela do rosto), preenche os buracos,
e pinta de preto a faixa superior (frac da altura da tela) dentro dessa região.
"""
import sys, subprocess, numpy as np, cv2
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
frac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.30

probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,r_frame_rate', '-of', 'csv=p=0', src],
                       capture_output=True, text=True).stdout.strip().split(',')
W, H = int(probe[0]), int(probe[1]); fps = probe[2]
rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                      stdout=subprocess.PIPE)
wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                       '-r', fps, '-i', '-', '-i', src, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264',
                       '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'copy', dst],
                      stdin=subprocess.PIPE)
n = 0
while True:
    buf = rd.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    dark = (hsv[:, :, 2] < 70)
    lab, k = ndimage.label(dark)
    if k:
        sizes = ndimage.sum(dark, lab, range(1, k + 1))
        # maior região escura na metade de cima do frame
        best, bsz = None, 0
        for i, s in enumerate(sizes, 1):
            if s < 3000:
                continue
            ys, xs = np.where(lab == i)
            if ys.mean() > H * 0.6:
                continue
            if s > bsz:
                best, bsz = i, s
        if best:
            m = ndimage.binary_fill_holes(lab == best)
            m = ndimage.binary_closing(m, iterations=6)
            m = ndimage.binary_fill_holes(m)
            ys, xs = np.where(m)
            top, bot = ys.min(), ys.max()
            cut = int(top + frac * (bot - top))
            band = np.zeros_like(m); band[top:cut, :] = True
            f[m & band] = (6, 6, 8)
    wr.stdin.write(f.tobytes()); n += 1
wr.stdin.close(); wr.wait(); rd.wait()
print('frames', n, '->', dst)
