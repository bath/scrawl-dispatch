# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow"]
# ///
"""Draws the mock demo of the scrawl-dispatch workflow: demo.mp4 and demo.gif beside this file.

    uv run demo/make-demo.py        (needs ffmpeg and the macOS system fonts)

Everything on screen is drawn here. It is an illustration, not a screen recording.
"""

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, S, FPS, SECONDS = 1280, 720, 2, 20, 18.5
OUT = Path(__file__).parent

BG = (15, 17, 21)
PANEL = (27, 30, 37)
EDGE = (52, 57, 68)
TEXT = (232, 234, 240)
DIM = (140, 147, 162)
RED = (255, 69, 58)
GREEN = (62, 207, 142)
AMBER = (240, 180, 70)
CLAY = (217, 119, 87)
PAGE = (246, 244, 239)
INK = (40, 42, 48)

_fonts = {}


def font(size, mono=False):
    key = (size, mono)
    if key not in _fonts:
        path = "/System/Library/Fonts/Menlo.ttc" if mono else "/System/Library/Fonts/SFNS.ttf"
        _fonts[key] = ImageFont.truetype(path, size * S)
    return _fonts[key]


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def span(t, start, end):
    """0 before start, 1 after end, eased between."""
    return ease((t - start) / (end - start))


def mix(a, b, k):
    return tuple(round(x + (y - x) * k) for x, y in zip(a, b))


class Canvas:
    def __init__(self):
        self.image = Image.new("RGB", (W * S, H * S), BG)
        self.d = ImageDraw.Draw(self.image)

    def box(self, x, y, w, h, fill, radius=10, outline=None, width=1):
        self.d.rounded_rectangle(
            [x * S, y * S, (x + w) * S, (y + h) * S],
            radius=radius * S,
            fill=fill,
            outline=outline,
            width=width * S,
        )

    def dot(self, x, y, r, fill):
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=fill)

    def line(self, points, fill, width=2):
        self.d.line([(x * S, y * S) for x, y in points], fill=fill, width=round(width * S), joint="curve")

    def text(self, x, y, s, size=14, fill=TEXT, mono=False, anchor="la"):
        self.d.text((x * S, y * S), s, font=font(size, mono), fill=fill, anchor=anchor)

    def width(self, s, size=14, mono=False):
        return self.d.textlength(s, font=font(size, mono)) / S

    def check(self, x, y, size, fill):
        self.line([(x, y + size * 0.5), (x + size * 0.38, y + size * 0.9), (x + size, y)], fill, 2.2)


# Layout: the Mac on the left, the code box on the right.
MAC = (40, 96, 580, 440)
BOX = (660, 96, 580, 440)
FINISH = 6.0  # the moment the recording is finished
ARRIVE = 10.4  # the agent's tab opens


def window(c, rect, title):
    x, y, w, h = rect
    c.box(x, y, w, h, PANEL, 12, EDGE)
    for i, colour in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        c.dot(x + 18 + i * 16, y + 17, 5, colour)
    c.text(x + w / 2, y + 17, title, 12, DIM, anchor="mm")
    c.line([(x, y + 34), (x + w, y + 34)], EDGE, 1)


def mac(c, t):
    x, y, w, h = MAC
    window(c, MAC, "Chrome · Projects")
    c.box(x + 14, y + 46, w - 28, h - 60, PAGE, 6)
    c.text(x + 34, y + 66, "Elm Street remodel", 17, INK)
    c.box(x + 34, y + 96, 54, 20, (222, 238, 226), 10)
    c.text(x + 61, y + 106, "Open", 11, (40, 120, 70), anchor="mm")
    c.box(x + 34, y + 134, w - 68, 6, (60, 62, 70), 3)
    for i, (label, value) in enumerate([("Done", "100%"), ("Billed so far", "$0"), ("Budget", "$4,200")]):
        cx = x + 34 + i * 172
        c.box(cx, y + 196, 150, 86, (255, 255, 255), 8, (225, 222, 214))
        c.text(cx + 14, y + 212, label, 11, (120, 122, 130))
        c.text(cx + 14, y + 236, value, 21, INK)
    for i in range(3):
        c.box(x + 34, y + 308 + i * 30, w - 68 - i * 90, 12, (228, 225, 217), 6)

    # The red mark, drawn while recording, and the pointer that draws it.
    cx, cy = x + 281 - 46, y + 239  # centred on the "Billed so far" card
    drawn = span(t, 2.6, 4.4)
    if drawn > 0 and t < FINISH + 0.5:
        steps = max(2, int(70 * drawn))
        points = []
        for i in range(steps + 1):
            a = -2.4 + (i / 70) * 6.9
            wobble = 1 + 0.05 * math.sin(a * 3)
            points.append((cx + 46 + 92 * wobble * math.cos(a), cy + 56 * wobble * math.sin(a)))
        c.line(points, RED, 3.5)
        px, py = points[-1]
    else:
        k = span(t, 1.2, 2.6)
        px, py = x + 120 + (cx + 46 - 92 * 0.74 - x - 120) * k, y + 330 + (cy - 38 - y - 330) * k
    if t < FINISH + 0.5:
        c.d.polygon(
            [(px * S, py * S), (px * S, (py + 17) * S), ((px + 5) * S, (py + 13) * S), ((px + 12) * S, (py + 12) * S)],
            fill=(20, 20, 24),
            outline=(255, 255, 255),
        )

    # What is said while recording.
    said = "“This total is wrong after I close the project.”"
    shown = said[: int(len(said) * span(t, 2.2, 5.2))]
    if shown and t < FINISH + 0.5:
        c.box(x + 34, y + h - 54, w - 68, 30, (32, 34, 40), 15)
        c.text(x + 52, y + h - 39, shown, 13, TEXT, anchor="lm")

    capsule(c, t)
    if t > ARRIVE - 0.2:
        k = span(t, ARRIVE - 0.2, ARRIVE + 0.3)
        nx = x + w - 236 + (1 - k) * 60
        c.box(nx, y + 90, 222, 50, mix(PAGE, (36, 38, 46), k), 12, EDGE)
        c.text(nx + 14, y + 106, "Scrawl sent to code-box", 12, mix(PAGE, TEXT, k), anchor="lm")
        c.text(nx + 14, y + 124, "A new tab is working on it", 11, mix(PAGE, DIM, k), anchor="lm")


def capsule(c, t):
    x, y, w, _ = MAC
    if t < 1.0:
        return
    if t < FINISH:
        seconds = int((t - 1.0) * 2.4)
        label, colour = f"REC 0:{seconds:02d}", RED
    elif t < FINISH + 0.9:
        label, colour = "Processing…", AMBER
    else:
        label, colour = "Copied", GREEN
    width = c.width(label, 13) + 46
    cx = x + w / 2
    grow = span(t, 1.0, 1.3)
    c.box(cx - width / 2 * grow, y + 50, width * grow, 30, (0, 0, 0), 15)
    if grow < 1:
        return
    if colour == GREEN:
        c.check(cx - width / 2 + 13, y + 59, 11, GREEN)
    else:
        pulse = 0.55 + 0.45 * math.sin(t * 7) if colour == RED else 1
        c.dot(cx - width / 2 + 18, y + 65, 5, mix((0, 0, 0), colour, pulse))
    c.text(cx - width / 2 + 32, y + 65, label, 13, TEXT, anchor="lm")


TERMINAL = [
    (0.0, "Claude Code · Opus · medium effort", DIM),
    (0.5, "> [scrawl 0:12 · Chrome “Projects”]", TEXT),
    (0.9, "  #1 (0:04) “This total is wrong after I", TEXT),
    (1.1, "  close the project.”", TEXT),
    (2.0, "* Read contact-sheet.png", GREEN),
    (2.9, "* Read frames/frame-01.png", GREEN),
    (3.9, "* Searching the code for the total…", CLAY),
]


def code_box(c, t):
    x, y, w, h = BOX
    window(c, BOX, "Herdr · code-box")
    side = 138
    c.line([(x + side, y + 34), (x + side, y + h)], EDGE, 1)
    c.text(x + 16, y + 56, "Spaces", 11, DIM)
    c.box(x + 10, y + 70, side - 20, 26, (40, 44, 54), 6)
    c.text(x + 22, y + 83, "code-box", 12, TEXT, anchor="lm")
    c.text(x + 16, y + 124, "Agents", 11, DIM)
    agents = [("fix flaky test", DIM), ("review PR 212", DIM)]
    opened = span(t, ARRIVE, ARRIVE + 0.4)
    if opened > 0:
        agents.append(("scrawl capture", mix(PANEL, TEXT, opened)))
    for i, (name, colour) in enumerate(agents):
        c.dot(x + 22, y + 150 + i * 24, 3.5, CLAY if i == 2 else EDGE)
        c.text(x + 34, y + 150 + i * 24, name, 12, colour, anchor="lm")

    # Tabs: two that exist, and the new one.
    tx = x + side + 12
    for i in range(3):
        if i == 2 and opened == 0:
            break
        active = (i == 2) if opened > 0 else (i == 1)
        tw = 62 * (opened if i == 2 else 1)
        c.box(tx, y + 42, tw, 26, (44, 48, 60) if active else PANEL, 6, CLAY if (i == 2 and t < ARRIVE + 1.6) else EDGE)
        if tw > 40:
            c.dot(tx + 16, y + 55, 4, CLAY)
            c.text(tx + 30, y + 55, str(i + 1), 12, TEXT if active else DIM, anchor="lm")
        tx += tw + 6

    # The terminal of the active tab.
    c.box(x + side + 12, y + 76, w - side - 24, h - 88, (18, 20, 25), 8, EDGE)
    lx, ly = x + side + 26, y + 96
    if opened == 0:
        c.text(lx, ly, "$ pnpm test --watch", 12, DIM, mono=True)
        c.text(lx, ly + 20, "  412 passed", 12, (70, 110, 85), mono=True)
        return
    for start, line, colour in TERMINAL:
        since = t - ARRIVE - 0.4 - start
        if since <= 0:
            break
        c.text(lx, ly, line[: int(since * 60)], 12, colour, mono=True)
        ly += 21


def transfer(c, t):
    """The capture travelling from the Mac to the code box, and the time since finish."""
    y = 560
    c.line([(MAC[0] + MAC[2] / 2, y), (BOX[0] + BOX[2] / 2, y)], EDGE, 2)
    c.dot(MAC[0] + MAC[2] / 2, y, 5, EDGE)
    c.dot(BOX[0] + BOX[2] / 2, y, 5, EDGE)
    c.text(W / 2, y - 14, "SSH", 11, DIM, anchor="mm")
    if FINISH + 0.9 < t < ARRIVE + 0.2:
        k = span(t, FINISH + 1.1, ARRIVE - 0.5)
        px = MAC[0] + MAC[2] / 2 + (BOX[0] + BOX[2] / 2 - MAC[0] - MAC[2] / 2) * k
        label = "contact sheet · frames · summary"
        width = c.width(label, 12) + 28
        c.box(px - width / 2, y - 14, width, 28, (44, 48, 60), 14, CLAY)
        c.text(px, y, label, 12, TEXT, anchor="mm")
    if t >= FINISH:
        # The 4.4 seconds shown here stand for the 4.9 measured in the real test.
        elapsed = min(t, ARRIVE) - FINISH
        shown = elapsed / (ARRIVE - FINISH) * 4.9
        done = t >= ARRIVE
        c.text(W / 2, y + 22, f"{shown:.1f} s since finish", 13, GREEN if done else AMBER, anchor="mm")


STEPS = [
    (1.0, "1", "Record a Scrawl: talk, point, mark up."),
    (FINISH, "2", "Finish. Scrawl writes the capture, and scrawl-dispatch sees it."),
    (FINISH + 1.0, "3", "The frames and the summary go to the code box."),
    (ARRIVE, "4", "Claude Code starts on it in a new Herdr tab. No paste step."),
]


def frame(t):
    c = Canvas()
    c.text(40, 44, "scrawl-dispatch", 22, TEXT, anchor="lm")
    c.text(40 + c.width("scrawl-dispatch", 22) + 14, 46, "mock demo: an illustration, not a screen recording", 13, DIM, anchor="lm")
    c.text(MAC[0], MAC[1] - 14, "YOUR MAC", 11, DIM, anchor="lm")
    c.text(BOX[0], BOX[1] - 14, "YOUR CODE BOX", 11, DIM, anchor="lm")
    mac(c, t)
    code_box(c, t)
    transfer(c, t)

    current = max((i for i, step in enumerate(STEPS) if t >= step[0]), default=-1)
    if current >= 0:
        _, number, caption = STEPS[current]
        fade = span(t, STEPS[current][0], STEPS[current][0] + 0.3)
        width = c.width(caption, 17) + 58
        c.box(W / 2 - width / 2, 628, width, 44, PANEL, 22, EDGE)
        c.dot(W / 2 - width / 2 + 24, 650, 12, CLAY)
        c.text(W / 2 - width / 2 + 24, 650, number, 13, (20, 20, 24), anchor="mm")
        c.text(W / 2 - width / 2 + 46, 650, caption, 17, mix(PANEL, TEXT, fade), anchor="lm")
    else:
        c.text(W / 2, 650, "Something in the app looks wrong.", 17, DIM, anchor="mm")
    for i in range(len(STEPS)):
        c.dot(W / 2 - 27 + i * 18, 694, 3.5, CLAY if i <= current else EDGE)
    return c.image.resize((W, H), Image.LANCZOS)


def main():
    total = int(SECONDS * FPS)
    mp4, gif = OUT / "demo.mp4", OUT / "demo.gif"
    encode = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-crf", "20", "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE,
    )
    for i in range(total):
        encode.stdin.write(frame(i / FPS).tobytes())
    encode.stdin.close()
    if encode.wait() != 0:
        sys.exit("ffmpeg failed")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
         "fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
         str(gif)],
        check=True,
    )
    print(mp4, gif)


if __name__ == "__main__":
    main()
