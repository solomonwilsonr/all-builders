"""An original score and sound effects for the 40-second reel (reel-40s.html), synthesised here so there are no
licensing questions, then muxed onto the rendered video.

    engine/.venv/bin/python promo/score.py                   # out/safeshelf-reel-40s.mp4 -> out/safeshelf-reel-40s-music.mp4
    engine/.venv/bin/python promo/score.py --wav-only        # just out/reel-40s-score.wav
    engine/.venv/bin/python promo/score.py --reel site       # reel-site-40s.html: quieter, website-scene effects

Music: 120 BPM (a bar is 2 s), D major. A soft intro under the logo, tension under "ten open tabs", the beat drops
when the extension demo starts (7.5 s), eases off for Eddy (24.3 s), lifts again for the numbers and ends on one
chord with the logo. Sound effects sit on the reel's own animation times (data-in, scene data-a/data-b, demo()).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 48000
DUR = 40.0
BPM = 120
BEAT = 60 / BPM
HERE = Path(__file__).parent
rng = np.random.default_rng(7)


def t_(seconds: float) -> np.ndarray:
    return np.arange(int(seconds * SR)) / SR


def hz(note: int) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def env(n: int, a: float, d: float, s: float, r: float) -> np.ndarray:
    """ADSR over n samples (times in seconds, s is the sustain level)."""
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    out = np.full(n, s, dtype=float)
    a = min(a, n)
    out[:a] = np.linspace(0, 1, a, endpoint=False)
    dd = min(d, max(n - a, 0))
    out[a:a + dd] = np.linspace(1, s, dd, endpoint=False)
    rr = min(r, n)
    out[n - rr:] *= np.linspace(1, 0, rr)
    return out


def lowpass(x: np.ndarray, cutoff) -> np.ndarray:
    """One-pole low-pass; cutoff may be a number or a per-sample array."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    k = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y, acc = np.empty_like(x), 0.0
    for i in range(len(x)):  # small and only run once, so a plain loop is fine
        acc += k[i] * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    return x - lowpass(x, cutoff)


def saw(f, t: np.ndarray) -> np.ndarray:
    phase = np.cumsum(np.broadcast_to(f, t.shape)) / SR
    return 2 * (phase % 1) - 1


class Track:
    def __init__(self):
        self.buf = np.zeros((int(DUR * SR) + SR, 2))

    def add(self, at: float, sig: np.ndarray, gain: float = 1.0, pan: float = 0.0):
        i = int(at * SR)
        if i >= len(self.buf):
            return
        sig = sig[: len(self.buf) - i]
        left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.buf[i:i + len(sig), 0] += sig * gain * left * 1.414
        self.buf[i:i + len(sig), 1] += sig * gain * right * 1.414


# ---------------------------------------------------------------- instruments
def kick() -> np.ndarray:
    t = t_(0.45)
    f = 45 + 95 * np.exp(-t * 28)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    click = rng.standard_normal(len(t)) * np.exp(-t * 300) * 0.3
    return np.tanh((body + click) * 1.6)


def hat(open_: bool = False) -> np.ndarray:
    t = t_(0.25 if open_ else 0.06)
    return highpass(rng.standard_normal(len(t)), 7000) * np.exp(-t * (12 if open_ else 70))


def clap() -> np.ndarray:
    t = t_(0.3)
    n = highpass(rng.standard_normal(len(t)), 1200)
    e = np.exp(-t * 18) + 0.6 * np.exp(-np.maximum(t - 0.012, 0) * 60) * (t > 0.012)
    return lowpass(n * e, 6000) * 0.8


def pluck(note: int, length: float = 0.35) -> np.ndarray:
    t = t_(length)
    f = hz(note)
    x = 0.6 * saw(f, t) + 0.4 * np.sin(2 * np.pi * f * 2 * t)
    return lowpass(x, 900 + 4000 * np.exp(-t * 14)) * np.exp(-t * 9)


def bass(note: int, length: float) -> np.ndarray:
    t = t_(length)
    f = hz(note)
    x = 0.7 * saw(f, t) + 0.6 * np.sin(2 * np.pi * f * t)
    return lowpass(x, 500 + 600 * np.exp(-t * 10)) * env(len(t), 0.005, 0.1, 0.7, 0.05)


def pad(notes: list[int], length: float, bright: float = 1.0) -> np.ndarray:
    t = t_(length)
    x = np.zeros(len(t))
    for n in notes:
        for detune in (-0.12, 0.0, 0.12):
            x += saw(hz(n + detune), t)
    x /= len(notes) * 3
    return lowpass(x, 700 + 1600 * bright) * env(len(t), 0.4, 0.3, 0.85, 0.6)


def bell(note: int, length: float = 1.6) -> np.ndarray:
    t = t_(length)
    f = hz(note)
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * d)
            for a, m, d in ((1, 1, 3), (0.5, 2.0, 5), (0.3, 3.01, 8), (0.15, 4.2, 11)))
    return x * env(len(t), 0.002, 0.05, 1, 0.3)


# ---------------------------------------------------------------- sound effects
def whoosh(length: float = 0.6, up: bool = True) -> np.ndarray:
    t = t_(length)
    p = t / length
    sweep = (300 + 5000 * p) if up else (5300 - 5000 * p)
    n = rng.standard_normal(len(t))
    x = lowpass(n, sweep) - lowpass(n, sweep * 0.25)
    return x * np.sin(np.pi * p) ** 1.5 * 1.4


def riser(length: float) -> np.ndarray:
    t = t_(length)
    p = t / length
    n = highpass(lowpass(rng.standard_normal(len(t)), 800 + 9000 * p ** 2), 400)
    tone = np.sin(2 * np.pi * np.cumsum(220 + 660 * p ** 2) / SR) * 0.25
    return (n * 0.7 + tone) * p ** 2


def impact() -> np.ndarray:
    t = t_(1.6)
    boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t * 12)) / SR) * np.exp(-t * 2.6)
    air = lowpass(rng.standard_normal(len(t)), 2500) * np.exp(-t * 5) * 0.4
    return np.tanh((boom + air) * 1.4)


def click() -> np.ndarray:
    t = t_(0.05)
    return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 160) + highpass(rng.standard_normal(len(t)), 3000)
            * np.exp(-t * 400) * 0.6)


def pop(pitch: float = 900) -> np.ndarray:
    t = t_(0.12)
    f = pitch * (1 + 0.8 * (1 - np.exp(-t * 40)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32)


def tick(pitch: float = 3200) -> np.ndarray:
    t = t_(0.03)
    return np.sin(2 * np.pi * pitch * t) * np.exp(-t * 220)


def key_tap() -> np.ndarray:
    t = t_(0.04)
    return lowpass(rng.standard_normal(len(t)), 4500) * np.exp(-t * 180)


def shimmer(root: int = 86) -> np.ndarray:
    """A soft, high glint for a section settling into place: three quiet bell notes a hair apart."""
    out = np.zeros(int(1.4 * SR))
    for i, n in enumerate((root, root + 4, root + 7)):
        b = bell(n, 1.1)
        out[int(i * 0.045 * SR):int(i * 0.045 * SR) + len(b)] += b * (0.8 - i * 0.15)
    return lowpass(out, 9000)


def air(length: float = 1.2) -> np.ndarray:
    """An airy, low whoosh for a page scrolling: filtered noise, no hiss."""
    t = t_(length)
    p = t / length
    n = rng.standard_normal(len(t))
    x = lowpass(n, 400 + 1800 * np.sin(np.pi * p)) - lowpass(n, 120)
    return x * np.sin(np.pi * p) ** 2 * 1.6


def soft_hit() -> np.ndarray:
    """A promo 'landing': a low thump with a little air, much gentler than impact()."""
    t = t_(1.0)
    thump = np.sin(2 * np.pi * np.cumsum(46 + 40 * np.exp(-t * 14)) / SR) * np.exp(-t * 5)
    return thump + lowpass(rng.standard_normal(len(t)), 900) * np.exp(-t * 9) * 0.15


def alert() -> np.ndarray:
    """The amber 'Careful' verdict: two soft notes, not an alarm."""
    a, b = bell(81, 0.9), bell(76, 1.3)
    out = np.zeros(int(1.5 * SR))
    out[:len(a)] += a
    out[int(0.16 * SR):int(0.16 * SR) + len(b)] += b
    return out


# ---------------------------------------------------------------- the score
D, A, Bm, G, Em = [50, 57, 62, 66], [45, 52, 57, 61], [47, 54, 59, 62], [43, 50, 55, 59], [40, 47, 52, 55]
ROOT = {id(D): 38, id(A): 33, id(Bm): 35, id(G): 31, id(Em): 28}


# Sections start exactly on the reel's scene cuts (the scenes' data-a). Each section gets its own beat, the nearest
# to 120 BPM that fits a whole number of beats, so every cut is also a downbeat (the change, at most a few per cent,
# is hidden by the cut). (start, end, section, chords, one per 4-beat bar)
CUTS = [0.0, 4.7, 7.5, 18.4, 24.3, 29.9, 33.55, 37.3]
SECTIONS = [(0.0, 4.7, "intro", [D, D]), (4.7, 7.5, "tension", [Bm, G]),
            (7.5, 18.4, "drive", [D, A, Bm, G]),          # the extension demo
            (18.4, 24.3, "drive", [D, A, Bm]),            # one check
            (24.3, 29.9, "soft", [G, D, A]),              # Eddy
            (29.9, 33.55, "drive", [D, A]),               # regulators and numbers
            (33.55, 35.55, "drive", [Bm]),                # wherever you shop
            (35.55, 37.3, "build", [G]), (37.3, DUR, "end", [D])]
BRIGHT = {"intro": 0.35, "tension": 0.25, "drive": 1.0, "soft": 0.45, "build": 0.7, "end": 1.2}


def beats(a: float, b: float) -> tuple[int, float]:
    n = max(2, round((b - a) / BEAT))
    return n, (b - a) / n


def onsets() -> list[float]:
    """Every beat time the music plays (for the sync report)."""
    out = []
    for a, b, section, _ in SECTIONS:
        if section in ("drive", "soft"):
            n, beat = beats(a, b)
            out += [a + k * beat for k in range(n)]
    return out


def music(tr: Track):
    for a, b, section, chords in SECTIONS:
        n, beat = beats(a, b)
        bars = [(a + k * beat, min(4, n - k)) for k in range(0, n, 4)]
        if section in ("intro", "tension", "build", "end"):  # one chord per even split, no grid needed
            bars = [(a + i * (b - a) / len(chords), 4) for i in range(len(chords))]
        for i, (bar, nb) in enumerate(bars):
            ch = chords[i % len(chords)]
            length = (b - a) / len(chords) if section in ("intro", "tension", "build", "end") else nb * beat
            tr.add(bar, pad(ch, length + 0.6, BRIGHT[section]), 0.15 if section == "drive" else 0.20)
            if section == "end":
                tr.add(bar, bell(74, 2.6), 0.22)
                tr.add(bar, bell(86, 2.2), 0.10, pan=0.3)
                tr.add(bar, bass(ROOT[id(ch)], 2.0), 0.35)
            if section == "intro":  # a low drone so the logo never sits in silence
                tr.add(bar, bass(ROOT[id(ch)], length) * env(int(length * SR), 0.8, 0.2, 0.9, 0.6), 0.16)
            if section == "tension":
                for k in range(int(length / 0.25)):  # a ticking clock under the ten tabs
                    tr.add(bar + k * 0.25, tick(2600 if k % 2 else 3400), 0.18)
            if section == "build":  # a clap roll that swells into the last chord, landing on the cut
                steps = max(4, round(length / (BEAT / 4)))
                for k in range(steps):
                    tr.add(bar + k * length / steps, clap(), 0.05 + 0.25 * (k / steps) ** 2)
            if section in ("drive", "soft"):
                per = 1 if section == "drive" else 2  # bass every beat, or every other beat
                for k in range(0, nb, per):
                    tr.add(bar + k * beat, bass(ROOT[id(ch)], beat * per * 0.9), 0.32 if section == "drive" else 0.22)
                sub = 4 if section == "drive" else 2  # arpeggio in 16ths or 8ths
                for k in range(nb * sub):
                    note = ch[[0, 1, 2, 3, 2, 1][k % 6]] + 12
                    tr.add(bar + k * beat / sub, pluck(note, 0.3), 0.09 if section == "drive" else 0.07,
                           pan=-0.35 if k % 2 else 0.35)
            if section == "drive":
                for k in range(nb):
                    t0 = bar + k * beat
                    tr.add(t0, kick(), 0.55)
                    if k % 2:
                        tr.add(t0, clap(), 0.22)
                    tr.add(t0 + beat / 2, hat(open_=k % 4 == 3), 0.10, pan=0.2)
                    tr.add(t0 + beat / 4, hat(), 0.05, pan=-0.2)
                    tr.add(t0 + 3 * beat / 4, hat(), 0.05, pan=-0.2)
            if section == "soft":
                tr.add(bar, kick(), 0.25)
                if nb > 2:
                    tr.add(bar + 2 * beat, kick(), 0.18)


def peak_at(tr: Track, center: float, sig: np.ndarray, gain: float, pan: float = 0.0):
    """Place a sound so its loudest point lands on `center` (a whoosh peaks mid-way, not at its start)."""
    tr.add(max(0.0, center - np.argmax(np.abs(sig)) / SR), sig, gain, pan)


def sfx(tr: Track):
    # 1 · logo and hero: the logo moves to the nav and the hero opens (fastest at 2.07 s, measured)
    tr.add(0.1, bell(74, 1.8), 0.16)
    tr.add(0.6, riser(1.45), 0.18)
    peak_at(tr, 1.75, whoosh(0.7), 0.30)
    peak_at(tr, 2.07, impact(), 0.26)
    for i, a in enumerate((2.95, 3.2, 3.28, 3.45)):  # the hero's chips and buttons
        tr.add(a, tick(2600 + i * 160), 0.10, pan=-0.4 + i * 0.25)
    # 2 · ten tabs scatter, fold into one check
    for i in range(10):
        tr.add(4.95 + i * 0.08, pop(700 + i * 60), 0.18, pan=-0.6 + i * 0.13)
    tr.add(5.2, riser(1.15), 0.22)
    peak_at(tr, 6.27, whoosh(0.6, up=False), 0.32)  # the fold (5.95-6.65), fastest at 6.27 s (measured)
    peak_at(tr, 6.95, pop(1100), 0.25)
    # 3 · the extension: camera moves (whoosh at each move's fastest point), the click, the verdict
    peak_at(tr, 7.5, impact(), 0.45)
    for mid, gain in ((8.12, 0.16), (9.25, 0.24), (10.65, 0.16), (12.22, 0.18), (15.2, 0.28)):
        peak_at(tr, mid, whoosh(0.8), gain)
    peak_at(tr, 9.97, click(), 0.55)
    tr.add(10.0, bell(86, 1.0), 0.16)  # the ripple
    peak_at(tr, 12.6, alert(), 0.30)  # the ring around "Careful"
    peak_at(tr, 17.5, whoosh(1.4), 0.10)  # the evidence card scrolls (16.0-18.2), fastest around 17.5 s
    for i, a in enumerate((16.3, 16.6, 16.9)):
        peak_at(tr, a + 0.1, pop(1000 + i * 180), 0.22, pan=(-0.3, 0, 0.3)[i])
    # scene exits: each scene rises away over its last 0.45 s, changing most just after it starts (measured)
    for b in (4.9, 18.6, 24.5, 30.1, 33.75):
        peak_at(tr, b - 0.38, whoosh(0.55), 0.24)
    # 5 · one check, the counters and bars
    peak_at(tr, 18.55, pop(1200), 0.22)
    for a in np.arange(19.3, 20.5, 0.06):
        tr.add(float(a), tick(3600), 0.06)
    for a in (20.1, 20.25, 20.4):
        peak_at(tr, a + 0.1, pop(1300), 0.14)
    # 6 · Eddy
    peak_at(tr, 24.55, pop(900), 0.22)
    for i in range(5):
        peak_at(tr, 25.3 + i * 0.22 + 0.15, pop(800 + i * 90), 0.10, pan=-0.4 + i * 0.2)
    tr.add(26.3, bell(81, 1.0), 0.14)
    tr.add(28.55, bell(78, 1.0), 0.10)
    # 7 · regulators and numbers
    peak_at(tr, 29.9, impact(), 0.30)
    for i, a in enumerate((31.2, 31.28, 31.36, 31.44, 31.52, 31.6, 31.68)):
        tr.add(a, tick(2800 + i * 150), 0.12, pan=-0.6 + i * 0.2)
    for a in np.arange(31.8, 33.0, 0.07):
        tr.add(float(a), tick(3800), 0.05)
    # 8 · wherever you shop
    peak_at(tr, 33.8, pop(1000), 0.20)
    for a in (34.3, 34.45):
        peak_at(tr, a + 0.1, pop(1150), 0.16)
    for a in np.arange(34.6, 35.15, 0.055):
        tr.add(float(a), key_tap(), 0.20, pan=0.2)
    # 9 · the end: the last scene blurs out fastest at 37.1 s (measured), the logo lands at 37.3 s
    tr.add(35.9, riser(1.4), 0.32)
    peak_at(tr, 37.1, whoosh(0.7), 0.24)
    peak_at(tr, 37.3, impact(), 0.40)
    peak_at(tr, 38.75, pop(1200), 0.18)


def sfx_site(tr: Track):
    """reel-site-40s.html: the same first 18.6 s, quieter, then the website scenes (page scrolls, sections settling)."""
    # 1 · logo and hero
    tr.add(0.1, bell(74, 1.8), 0.12)
    tr.add(0.6, riser(1.45), 0.10)
    peak_at(tr, 1.75, air(0.9), 0.20)
    peak_at(tr, 2.07, soft_hit(), 0.22)
    peak_at(tr, 2.1, shimmer(), 0.07)
    peak_at(tr, 2.7, tick(2900), 0.05)  # the headline's lines rising (fastest at 2.70 s, measured)
    # 2 · ten tabs, folded into one check
    for i in range(10):
        tr.add(4.95 + i * 0.08, pop(700 + i * 60), 0.08, pan=-0.6 + i * 0.13)
    tr.add(5.2, riser(1.15), 0.12)
    peak_at(tr, 6.27, air(0.7), 0.24)
    peak_at(tr, 6.95, shimmer(83), 0.08)
    # 3 · the extension
    peak_at(tr, 7.5, soft_hit(), 0.30)
    for mid, gain in ((8.12, 0.12), (9.25, 0.18), (10.65, 0.12), (12.22, 0.14), (15.2, 0.18)):
        peak_at(tr, mid, air(1.0), gain)
    peak_at(tr, 9.97, click(), 0.35)
    tr.add(10.0, bell(86, 1.0), 0.09)
    peak_at(tr, 12.6, alert(), 0.18)
    peak_at(tr, 17.5, air(1.6), 0.08)
    # scene exits
    for b in (4.9, 18.6, 24.5, 30.1, 33.75):
        peak_at(tr, b - 0.38, air(0.6), 0.16)
    # 5 · the website's grid: a soft tick as each card lands, the page scrolls to the second row
    for i in range(6):
        peak_at(tr, 19.0 + i * 0.14 + 0.25, tick(2200 + i * 140), 0.05, pan=-0.5 + (i % 3) * 0.5)
    peak_at(tr, 20.5, shimmer(), 0.07)
    peak_at(tr, 22.45, air(2.2), 0.14)
    # 6 · Eddy's answer and its evidence
    peak_at(tr, 25.2, air(0.8), 0.12)
    peak_at(tr, 26.0, shimmer(81), 0.07)
    # 7 · regulators
    peak_at(tr, 30.6, air(0.8), 0.12)
    peak_at(tr, 31.4, shimmer(83), 0.07)
    # 8 · on the record: reading down the page
    peak_at(tr, 34.0, air(0.8), 0.10)
    peak_at(tr, 35.9, air(2.4), 0.12)
    # 9 · the sky band opens, the logo line settles
    tr.add(36.1, riser(1.2), 0.14)
    peak_at(tr, 37.3, soft_hit(), 0.30)
    peak_at(tr, 37.7, air(0.9), 0.14)
    peak_at(tr, 38.6, shimmer(), 0.09)


REELS = {  # --reel name: (effects, video in, video out, wav)
    "product": (lambda tr: sfx(tr), "safeshelf-reel-40s.mp4", "safeshelf-reel-40s-music.mp4", "reel-40s-score.wav"),
    "site": (lambda tr: sfx_site(tr), "safeshelf-reel-site-40s.mp4", "safeshelf-reel-site-40s-music.mp4",
             "reel-site-40s-score.wav"),
}
REEL = sys.argv[sys.argv.index("--reel") + 1] if "--reel" in sys.argv else "product"


def render() -> Path:
    tr = Track()
    music(tr)
    REELS[REEL][0](tr)
    mix = tr.buf[: int(DUR * SR)]
    fade = np.ones(len(mix))
    fade[-int(1.8 * SR):] = np.linspace(1, 0, int(1.8 * SR)) ** 1.5  # out with the logo
    mix *= fade[:, None]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)  # gentle glue, never a hard clip
    mix *= 0.89 / max(np.abs(mix).max(), 1e-9)
    wav = HERE / "out" / REELS[REEL][3]
    wav.parent.mkdir(exist_ok=True)
    import wave
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    return wav


if __name__ == "__main__":
    wav = render()
    print(wav)
    if "--wav-only" not in sys.argv:
        video, out = HERE / "out" / REELS[REEL][1], HERE / "out" / REELS[REEL][2]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav), "-map", "0:v", "-map",
                        "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "256k",
                        "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)], check=True)
        print(out)
