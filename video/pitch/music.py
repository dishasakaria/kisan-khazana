"""Soft synthesized background pad (no samples, no copyright): python3 music.py <seconds> <out.wav>"""
import sys, wave
import numpy as np

SR = 44100
dur, out = float(sys.argv[1]), sys.argv[2]
t = np.arange(int(dur * SR)) / SR
hz = lambda midi: 440 * 2 ** ((midi - 69) / 12)
CHORDS = [[62, 66, 69, 74], [57, 64, 69, 73], [59, 66, 71, 74], [55, 62, 67, 71]]  # D  A  Bm  G
BAR = 4.0
y = np.zeros_like(t)
for k in range(int(dur // BAR) + 1):
    s, e = int(k * BAR * SR), min(len(t), int((k + 1.25) * BAR * SR))   # bars overlap 1s for a smooth crossfade
    seg = t[s:e] - k * BAR
    env = np.minimum(1, seg / 1.2) * np.clip((BAR + 1 - seg) / 1.2, 0, 1)
    for n in CHORDS[k % 4]:
        f = hz(n)
        y[s:e] += env * (np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(2 * np.pi * 2.003 * f * seg)) / 4
# low drone on Sa/Pa (D2/A2) with slow shimmer, like a quiet tanpura bed
y += 0.35 * (np.sin(2 * np.pi * hz(38) * t) + 0.6 * np.sin(2 * np.pi * hz(45) * t)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.25 * t))
y *= np.minimum(1, t / 2) * np.minimum(1, (dur - t) / 3)            # fade in/out
y = (y / np.abs(y).max() * 0.09 * 32767).astype(np.int16)           # ~-21 dBFS peak: stays under the voices
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())
