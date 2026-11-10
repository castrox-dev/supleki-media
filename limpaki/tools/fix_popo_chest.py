#!/usr/bin/env python3
"""Apaga o emblema/logo turquesa que o Flow costuma desenhar no peito do Popó.
Uso: python3 fix_popo_chest.py in.mp4 out.mp4
Por frame: acha a tela facial (maior região escura), procura componentes turquesa
pequenos centralizados logo abaixo dela (peito) e faz inpaint neles.
"""
import sys, subprocess, numpy as np, cv2
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
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
n = fixed = 0
while True:
    buf = rd.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
    dark = (hsv[:, :, 2] < 70)
    lab, k = ndimage.label(dark)
    face = None
    if k:
        sizes = ndimage.sum(dark, lab, range(1, k + 1))
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
            ys, xs = np.where(lab == best)
            face = (xs.min(), ys.min(), xs.max(), ys.max())
    if face:
        x0, y0, x1, y1 = face
        cx = (x0 + x1) / 2; fw = x1 - x0; fh = y1 - y0
        turq = (hsv[:, :, 0] > 78) & (hsv[:, :, 0] < 100) & (hsv[:, :, 1] > 90) & (hsv[:, :, 2] > 90)
        lab2, k2 = ndimage.label(turq)
        mask = np.zeros((H, W), np.uint8)
        if k2:
            objs = ndimage.find_objects(lab2)
            for i, sl in enumerate(objs, 1):
                if sl is None:
                    continue
                ys, xs = np.where(lab2[sl] == i)
                s = len(ys)
                if s < 15 or s > fw * fh * 0.25:
                    continue
                yy = ys.mean() + sl[0].start; xx = xs.mean() + sl[1].start
                if abs(xx - cx) > fw * 0.35:
                    continue
                if not (y1 + fh * 0.25 < yy < y1 + fh * 1.2):
                    continue
                mask[lab2 == i] = 255
        if mask.any():
            mask = cv2.dilate(mask, np.ones((9, 9), np.uint8), iterations=2)
            f = cv2.inpaint(f, mask, 7, cv2.INPAINT_TELEA)
            fixed += 1
    wr.stdin.write(f.tobytes()); n += 1
wr.stdin.close(); wr.wait(); rd.wait()
print('frames', n, 'fixed', fixed, '->', dst)
