#!/usr/bin/env python3
"""news-image-20261123: Monday 23 November 2026 in one image.

A cream broadsheet front page, drawn from scratch with the Python standard
library only (no Pillow). Writes /output/entry.png deterministically:
1024x1024 PNG, under 1 MiB. Honours $MAKEFUN_OUTPUT_DIR / --output.
Every line of this file was typed fresh in the build session from the
research brief; no earlier edition's code was read, opened or copied.
"""
import argparse
import binascii
import os
import struct
import sys
import zlib

W, H = 1024, 1024
CREAM = (247, 241, 222)
INK = (26, 26, 26)
RED = (193, 39, 45)
GREY = (107, 114, 128)
LIGHT = (232, 224, 200)
WHITE = (255, 255, 255)

REGIONS = {
    "EUROPE": (31, 79, 163),
    "MIDDLE EAST": (217, 123, 30),
    "ASIA": (122, 63, 160),
    "AFRICA": (46, 139, 87),
    "AMERICAS": (193, 39, 45),
    "OCEANIA": (15, 139, 141),
    "GLOBAL": (107, 114, 128),
}

# ---------------------------------------------------------------- font: 5x7
# All-caps broadsheet font. Each glyph is 7 rows of 5 cells, '#' = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "·": ("00000", "00000", "00000", "00000", "01100", "01100", "00000"),
    "—": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "×": ("00000", "10001", "01010", "00100", "01010", "10001", "00000"),
    "€": ("01110", "10001", "10000", "11110", "10000", "10001", "01110"),
}


def normalise(text):
    """Fold characters the 5x7 font cannot draw into ones it can."""
    return (text.replace("’", "'").replace("‘", "'").replace("“", '"')
            .replace("”", '"').replace("–", "-").replace("—", "—")
            .replace("…", "...").upper())


def text_width(text, scale):
    return len(normalise(text)) * 6 * scale - scale


def wrap(text, max_w, scale):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    text = normalise(text)
    words, lines, cur = text.split(" "), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(colour)

    def rect(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            self.px[base:base + (x1 - x0) * 3] = bytes(colour) * (x1 - x0)

    def hline(self, x, y, w, colour, t=1):
        self.rect(x, y, w, t, colour)

    def vline(self, x, y, h, colour, t=1):
        self.rect(x, y, t, h, colour)

    def line(self, x0, y0, x1, y1, colour, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, colour)

    def ring(self, cx, cy, r, colour, t=1):
        for a in range(360):
            import math
            x = cx + int(r * math.cos(math.radians(a)))
            y = cy + int(r * math.sin(math.radians(a)))
            self.rect(x, y, t, t, colour)

    def triangle(self, x0, y0, x1, y1, x2, y2, colour):
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
                c = 1 - a - b
                if a >= 0 and b >= 0 and c >= 0:
                    self.put(xx, yy, colour)

    def text(self, x, y, s, scale, colour):
        s = normalise(s)
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, colour)
            cx += 6 * scale
        return cx

    def text_centre(self, cx, y, s, scale, colour):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, colour)

    def text_right(self, x, y, s, scale, colour):
        self.text(x - text_width(s, scale), y, s, scale, colour)


# --------------------------------------------------------------------- png
def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------- scene illustrations
# Each scene draws one small flat-shape picture inside a card's band.
SKY = (196, 222, 235)
SEA = (64, 120, 170)
SAND = (232, 214, 170)
DARK = (43, 54, 74)
ORANGE = (232, 120, 30)
FLAME = (245, 158, 40)
GREY2 = (120, 124, 128)
GREEN2 = (90, 140, 80)


def scene_cop(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.circle(x + w - 16, y + 14, 9, (250, 200, 80))
    bx = x + w // 2 - 52
    cv.rect(bx, y + h - 26, 104, 26, (240, 236, 220))
    cv.triangle(bx - 6, y + h - 26, x + w // 2, y + h - 52, bx + 110,
                y + h - 26, (120, 60, 60))
    for i in range(4):
        cv.rect(bx + 8 + i * 24, y + h - 22, 6, 18, DARK)
    for i, c in enumerate(((193, 39, 45), (31, 79, 163), (46, 139, 87))):
        cv.vline(x + w - 30 + i * 10, y + 8, 22, DARK, 1)
        cv.rect(x + w - 30 + i * 10, y + 8, 8, 5, c)


def scene_ship(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.rect(x, y + h - 22, w, 22, SEA)
    cv.rect(x + 16, y + h - 34, w - 56, 12, (90, 60, 50))
    cv.triangle(x + w - 40, y + h - 34, x + w - 16, y + h - 34,
                x + w - 16, y + h - 22, (90, 60, 50))
    cv.rect(x + 20, y + h - 48, 16, 14, (200, 80, 60))
    cv.rect(x + 38, y + h - 48, 16, 14, (60, 120, 90))
    cv.rect(x + 56, y + h - 48, 16, 14, (200, 160, 60))
    cv.triangle(x + 24, y + h - 48, x + 36, y + h - 48, x + 30, y + h - 64,
                ORANGE)
    cv.triangle(x + 42, y + h - 48, x + 54, y + h - 48, x + 48, y + h - 62,
                FLAME)
    cv.circle(x + 30, y + h - 70, 7, (200, 200, 200))
    cv.circle(x + 44, y + h - 76, 5, (220, 220, 220))
    cv.rect(x, y + h - 20, w, 2, WHITE)
    cv.rect(x + 20, y + h - 14, w - 40, 2, WHITE)


def scene_court(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    bx = x + w // 2 - 52
    cv.rect(bx, y + h - 30, 104, 30, (240, 236, 220))
    cv.triangle(bx - 6, y + h - 30, x + w // 2, y + h - 54, bx + 110,
                y + h - 30, (120, 100, 80))
    for i in range(4):
        cv.rect(bx + 8 + i * 24, y + h - 28, 6, 24, DARK)
    cv.vline(x + w - 18, y + 8, 26, DARK, 2)
    cv.hline(x + w - 30, y + 10, 24, DARK, 2)
    cv.triangle(x + w - 30, y + 10, x + w - 22, y + 10, x + w - 26,
                y + 22, (193, 39, 45))
    cv.triangle(x + w - 14, y + 10, x + w - 6, y + 10, x + w - 10,
                y + 22, (193, 39, 45))


def scene_missile(cv, x, y, w, h):
    cv.rect(x, y, w, h, (60, 70, 95))
    cv.circle(x + 14, y + 12, 7, (250, 220, 130))
    cv.line(x + 12, y + h - 8, x + w - 14, y + 10, (255, 220, 120), 2)
    cv.line(x + 14, y + h - 12, x + w - 10, y + 16, ORANGE, 2)
    cv.triangle(x + w - 16, y + 8, x + w - 6, y + 18, x + w - 22, y + 20,
                (220, 220, 220))
    for i in range(3):
        cv.circle(x + 20 + i * 12, y + h - 10 - i * 3, 3, (250, 200, 80))
    cv.rect(x, y + h - 6, w, 6, (40, 44, 54))


def scene_building(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.rect(x + 12, y + 12, w - 24, h - 12, (150, 140, 125))
    for r in range(3):
        for c in range(4):
            cv.rect(x + 18 + c * 14, y + 18 + r * 14, 8, 9, (60, 70, 95))
    cv.rect(x + 18, y + 18, 8, 9, (30, 30, 30))
    cv.rect(x + 32, y + 32, 8, 9, (30, 30, 30))
    cv.line(x + 40, y + 12, x + 48, y + 30, DARK, 2)
    cv.line(x + 48, y + 30, x + 42, y + 48, DARK, 2)
    cv.circle(x + w - 16, y + 14, 8, (200, 200, 200))
    cv.circle(x + w - 26, y + 8, 6, (220, 220, 220))
    cv.rect(x, y + h - 8, w, 8, (90, 85, 75))


def scene_tanker(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.circle(x + 14, y + 12, 8, (250, 200, 80))
    cv.rect(x, y + h - 24, w, 24, SEA)
    cv.rect(x + 8, y + h - 36, w - 16, 12, (120, 40, 40))
    cv.rect(x + 14, y + h - 48, 10, 12, (200, 200, 200))
    cv.line(x + w - 22, y + 6, x + w - 12, y + h - 26, DARK, 2)
    cv.line(x + w - 12, y + 6, x + w - 22, y + h - 26, DARK, 2)
    cv.rect(x + 16, y + h - 18, w - 32, 2, WHITE)


def scene_village(cv, x, y, w, h):
    cv.rect(x, y, w, h, SAND)
    for i in range(3):
        bx = x + 8 + i * 24
        cv.rect(bx, y + h - 26, 20, 18, (240, 236, 220))
        cv.triangle(bx - 2, y + h - 26, bx + 10, y + h - 40, bx + 22,
                    y + h - 26, (150, 70, 50))
    cv.triangle(x + w - 18, y + h - 52, x + w - 8, y + h - 52, x + w - 13,
                y + h - 68, ORANGE)
    cv.triangle(x + w - 26, y + h - 48, x + w - 14, y + h - 48, x + w - 20,
                y + h - 62, FLAME)
    cv.circle(x + 12, y + 12, 8, GREEN2)
    cv.rect(x + 11, y + 18, 2, 10, (90, 60, 40))


def scene_factory(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.rect(x + 8, y + h - 30, w - 16, 30, (140, 130, 115))
    cv.triangle(x + 8, y + h - 30, x + 20, y + h - 44, x + 32, y + h - 30,
                (120, 110, 95))
    cv.triangle(x + 32, y + h - 30, x + 44, y + h - 44, x + 56, y + h - 30,
                (120, 110, 95))
    cv.rect(x + w - 22, y + 8, 8, h - 34, (100, 95, 85))
    cv.circle(x + w - 18, y + 6, 7, (190, 190, 190))
    cv.circle(x + w - 28, y + 2, 5, (210, 210, 210))
    cv.triangle(x + 14, y + h - 44, x + 26, y + h - 44, x + 20, y + h - 60,
                ORANGE)
    for i in range(3):
        cv.rect(x + 14 + i * 14, y + h - 24, 8, 8, (250, 220, 130))


def scene_badge(cv, x, y, w, h):
    cv.rect(x, y, w, h, (220, 225, 235))
    cx, cy = x + w // 2, y + h // 2
    cv.circle(cx, cy, 24, (193, 39, 45))
    cv.circle(cx, cy, 18, (240, 200, 60))
    cv.circle(cx, cy, 9, (193, 39, 45))
    cv.text(cx - 3, cy - 3, "*", 1, WHITE)
    cv.circle(x + 12, y + h - 12, 6, GREY2)
    cv.circle(x + w - 12, y + h - 12, 6, GREY2)
    cv.line(x + 12, y + h - 12, x + w - 12, y + h - 12, GREY2, 2)


def scene_hospital(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.rect(x + 10, y + 10, w - 20, h - 10, (240, 236, 220))
    cv.rect(x + w // 2 - 8, y + 14, 16, 16, RED)
    cv.rect(x + w // 2 - 3, y + 16, 6, 12, WHITE)
    cv.rect(x + w // 2 - 6, y + 19, 12, 6, WHITE)
    for r in range(2):
        for c in range(3):
            cv.rect(x + 16 + c * 16, y + 36 + r * 14, 9, 9, (120, 170, 200))
    cv.rect(x + 12, y + h - 14, w - 24, 6, (90, 130, 90))
    cv.rect(x + 14, y + h - 22, 22, 8, WHITE)
    cv.circle(x + 18, y + h - 24, 4, (200, 170, 130))


def scene_plane(cv, x, y, w, h):
    cv.rect(x, y, w, h, SKY)
    cv.circle(x + 12, y + 10, 6, WHITE)
    cv.circle(x + 24, y + 14, 8, WHITE)
    cv.circle(x + w - 14, y + 8, 6, WHITE)
    cv.rect(x + 8, y + h // 2 - 4, w - 30, 10, (240, 240, 240))
    cv.triangle(x + w - 22, y + h // 2 - 4, x + w - 8, y + h // 2 - 4,
                x + w - 22, y + h // 2 - 16, (200, 60, 60))
    cv.triangle(x + w // 2 - 6, y + h // 2 - 4, x + w // 2 + 14,
                y + h // 2 - 4, x + w // 2 + 4, y + h // 2 - 18, (200, 60, 60))
    cv.circle(x + w - 26, y + h // 2 + 1, 3, (60, 70, 95))
    cv.rect(x, y + h - 8, w, 8, (120, 130, 120))
    cv.line(x + 10, y + h - 8, x + w - 10, y + h - 8, RED, 2)


def scene_chart(cv, x, y, w, h):
    cv.rect(x, y, w, h, (240, 236, 220))
    cv.vline(x + 8, y + 8, h - 16, DARK, 2)
    cv.hline(x + 8, y + h - 8, w - 16, DARK, 2)
    pts = [(x + 12, y + 14), (x + 24, y + 20), (x + 36, y + 18),
           (x + 48, y + 30), (x + 60, y + 34), (x + 72, y + h - 14)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED, 3)
    cv.triangle(pts[-1][0], pts[-1][1], pts[-1][0] - 10, pts[-1][1] - 2,
                pts[-1][0] - 2, pts[-1][1] - 10, RED)
    for i, bh in enumerate((10, 16, 12, 8)):
        cv.rect(x + 14 + i * 12, y + h - 8 - bh, 7, bh, (120, 140, 180))


def scene_chalk(cv, x, y, w, h):
    cv.rect(x, y, w, h, (38, 52, 58))
    cv.rect(x + 6, y + 6, w - 12, h - 12, (44, 60, 66))
    cv.text(x + 10, y + 12, "Z(S) = 0", 2, WHITE)
    cv.text(x + 10, y + 34, "PROOF?", 2, (250, 220, 130))
    cv.line(x + 10, y + h - 12, x + w - 10, y + h - 12, (200, 200, 200), 1)


SCENES = {
    "cop": scene_cop, "ship": scene_ship, "court": scene_court,
    "missile": scene_missile, "building": scene_building,
    "tanker": scene_tanker, "village": scene_village,
    "factory": scene_factory, "badge": scene_badge,
    "hospital": scene_hospital, "plane": scene_plane,
    "chart": scene_chart, "chalk": scene_chalk,
}


# ------------------------------------------------------------- world map
# Coarse land mask, 64 columns x 28 rows (lon -180..180, lat 80..-55).
LAND_ROWS = [
    [21, 27],
    [3, 6, 8, 12, 21, 27, 42, 56],
    [2, 7, 8, 20, 21, 27, 38, 58],
    [2, 8, 9, 21, 22, 27, 37, 60],
    [3, 9, 10, 21, 22, 26, 37, 60],
    [5, 10, 11, 21, 30, 60],
    [6, 20, 29, 58],
    [7, 20, 29, 56],
    [8, 20, 28, 38, 44, 55],
    [9, 16, 28, 38, 42, 58],
    [10, 16, 29, 40, 42, 53],
    [11, 16, 29, 40, 43, 48, 49, 52],
    [12, 16, 29, 40, 43, 47, 49, 51],
    [13, 17, 30, 40, 44, 47, 49, 51],
    [14, 18, 30, 40, 44, 46, 49, 52, 55, 57],
    [15, 19, 30, 39, 44, 45, 50, 53],
    [15, 21, 31, 39, 50, 58],
    [16, 22, 31, 38, 51, 59],
    [16, 22, 32, 38, 51, 59],
    [16, 21, 32, 37, 52, 59],
    [17, 21, 33, 36, 52, 58],
    [17, 20, 33, 35, 53, 58, 61, 62],
    [17, 19, 53, 57, 61, 62],
    [18, 19, 54, 56],
    [18, 19],
    [18, 19],
    [18, 18],
    [],
    [],
]


def draw_map(cv, x, y, w, h, pins):
    """Dotted world map; pins is a list of (px, py, number, colour)."""
    cv.rect(x, y, w, h, (238, 232, 210))
    cw, ch = w / 64.0, h / 28.0
    for row in range(28):
        ranges = LAND_ROWS[row]
        for i in range(0, len(ranges), 2):
            for col in range(ranges[i], ranges[i + 1] + 1):
                cv.circle(int(x + (col + 0.5) * cw), int(y + (row + 0.5) * ch),
                          2, (150, 140, 115))
    for px, py, num, colour in pins:
        cv.circle(px, py, 8, colour)
        cv.ring(px, py, 8, INK, 1)
        label = str(num)
        cv.text(px - text_width(label, 1) // 2, py - 3, label, 1, WHITE)


# ---------------------------------------------------------------- stories
# (num, region, kicker, headline, body, source, scene, lon, lat)
# All verified against wire sources by the parent; the builder re-checked
# the three lead stories live. Riemann is a CLAIM, never settled fact.
CARDS = [
    (1, "EUROPE", "ANTALYA · CLIMATE", "COP31 COLLAPSES WITH NO DEAL",
     "EU, PANAMA AND ISLAND STATES REJECT THE FOSSIL-FUEL-FREE ANTALYA "
     "PACT AFTER A RECORD 44 HOURS OF OVERTIME. GUTERRES: DEEPLY "
     "DISAPPOINTING.", "REUTERS", "cop", 30.7, 36.9),
    (2, "EUROPE", "GULF OF FINLAND · WAR AT SEA",
     "SANCTIONED RUSSIAN SHIP STILL BURNING",
     "DRONES HIT THE SPARTA II OFF FINLAND; THE CREW OF 16 WAS EVACUATED. "
     "SWEDISH JETS SCRAMBLED; A RUSSIAN HELICOPTER IS SUSPECTED OF "
     "ENTERING FINNISH AIRSPACE.", "REUTERS", "ship", 27.0, 59.5),
    (3, "ASIA", "THE HAGUE · JUSTICE",
     "WORLD COURT: MYANMAR COMMITTED GENOCIDE",
     "THE UN COURT RULES THE 2017 CAMPAIGN AGAINST THE ROHINGYA WAS "
     "GENOCIDE. MORE THAN 700,000 FLED TO BANGLADESH.",
     "UN / REUTERS", "court", 4.3, 52.1),
    (4, "EUROPE", "POLAND · PROVOCATION",
     "MISSILES AND A DRONE CRASH IN POLAND",
     "TWO SUSPECTED RUSSIAN MISSILES AND A DRONE CAME DOWN IN THE "
     "SOUTH-EAST DURING A HUGE STRIKE ON UKRAINE. NATO JETS SCRAMBLED; "
     "TUSK DENOUNCES MOSCOW.", "REUTERS", "missile", 22.0, 50.0),
    (5, "EUROPE", "KYIV REGION · WAR", "14 MISSING AFTER DRONE HITS FLATS",
     "A RUSSIAN DRONE STRUCK AN APARTMENT BLOCK; AT LEAST 14 PEOPLE ARE "
     "FEARED TRAPPED IN THE RUBBLE, ZELENSKIY SAYS.",
     "REUTERS", "building", 30.5, 50.4),
    (6, "MIDDLE EAST", "GULF · WAR COST", "US WAR COST PUT AT $48.3 BILLION",
     "THE PENTAGON PUTS THE COST SINCE FEBRUARY AT $48.3BN. TRUMP DELAYS "
     "ANY DECISION ON NEW IRAN STRIKES UNTIL AFTER 1 JANUARY.",
     "REUTERS", "tanker", 56.5, 26.5),
    (7, "MIDDLE EAST", "WEST BANK · SETTLER VIOLENCE",
     "SETTLERS TORCH FOUR VILLAGES",
     "ARSON AND GRAFFITI HIT DEIR AS-SUDAN, DEIR ABU MASHA'AL, KAFR MALIK "
     "AND AT-TUWANI. EISENKOT CALLS IT JEWISH TERRORISM.",
     "REUTERS", "village", 35.2, 31.9),
    (8, "ASIA", "CIKANDE · FACTORY FIRE",
     "FACTORY FIRE: 3 DEAD, 36 MISSING",
     "A CANDY FACTORY BLAZE IN BANTEN LEFT 3 DEAD AND 36 MISSING, "
     "RESCUERS SAY. ABOUT 50 ARE UNACCOUNTED FOR.",
     "REUTERS / AP", "factory", 106.2, -6.3),
    (9, "AMERICAS", "SINALOA · CARTELS",
     "MEXICO CAPTURES FBI TOP-10 FUGITIVE",
     "FAUSTO ISIDRO MEZA FLORES, 'EL CHAPO ISIDRO', IS SEIZED IN GUASAVE. "
     "HOURS OF VIOLENCE FOLLOW; 11 DEAD.", "REUTERS", "badge", -108.5, 25.6),
    (10, "AMERICAS", "BRASILIA · HEALTH", "BOLSONARO IN INTENSIVE CARE",
     "THE EX-PRESIDENT, 71, SERVING 27 YEARS FOR A COUP ATTEMPT HE DENIES, "
     "IS IN HOSPITAL WITH AN ACUTE BOWEL OBSTRUCTION. STABLE, A TUBE "
     "FITTED.", "REUTERS / AFP", "hospital", -47.9, -15.8),
    (11, "AMERICAS", "ATLANTA · AVIATION",
     "DELTA'S WEIGHT SYSTEM FAILS; 1,600+ FLIGHTS LATE",
     "THE ALIS LOAD SYSTEM WENT DOWN; THE FAA BRIEFLY GROUND-STOPPED "
     "ATLANTA FLIGHTS. CREWS COUNTED BAGS BY HAND DAYS BEFORE "
     "THANKSGIVING.", "REUTERS", "plane", -84.4, 33.6),
    (12, "AMERICAS", "NEW YORK · MARKETS", "S&P 500 DOWN 11.6% IN CORRECTION",
     "STOCKS FELL FOR A SEVENTH STRAIGHT SESSION. TRUMP BLAMES DEMOCRATS; "
     "BESSENT SOFTENS ON NVIDIA AS HUANG'S RETURN IS WEIGHED.",
     "REUTERS", "chart", -74.0, 40.7),
    (13, "GLOBAL", "MATHS · CLAIM", "CLAIM: RIEMANN PROOF FOUND WITH CLAUDE",
     "AN ANTHROPIC MATHEMATICIAN SAYS HE PROVED THE 167-YEAR-OLD "
     "HYPOTHESIS. LEAN CODE IS CERTIFIED; MATHEMATICIANS STILL TO VERIFY. "
     "CLAIM ONLY.", "NATURE", "chalk", None, None),
]

# (num, region, one-line summary) — continues the count after the cards.
ALSO = [
    (14, "EUROPE", "UK-EU RESET DEAL — FOOD, CARBON, YOUTH"),
    (15, "EUROPE", "LISBON MARCH — THOUSANDS PROTEST COSTS"),
    (16, "EUROPE", "UK BARS CRYPTO EXCHANGES FROM SELF-DEALING"),
    (17, "EUROPE", "FRANCE: SIXTH WEEKEND OF AUSTERITY PROTESTS"),
    (18, "MIDDLE EAST", "HOUTHIS SAY THEY HIT SAUDI REFINERY"),
    (19, "MIDDLE EAST", "EISENKOT TAPPED TO FORM ISRAEL GOVERNMENT"),
    (20, "MIDDLE EAST", "ISRAEL GROUND OP IN GAZA; WCK TRUCK HIT"),
    (21, "MIDDLE EAST", "QATAR PLEDGES €15BN IN DOHA DEAL WITH MERZ"),
    (22, "ASIA", "SEOUL MINISTER QUITS IN EXAM-CHEATING ROW"),
    (23, "ASIA", "CHINA WARNS JAPAN OVER TAIWAN REMARKS"),
    (24, "ASIA", "NEPAL PM SHAH ON STATE VISIT TO INDIA"),
    (25, "ASIA", "INDIA 720/9 — RECORD INNINGS IN WELLINGTON"),
    (26, "ASIA", "BANGLADESH PROTESTS OVER EXILED EX-LEADER"),
    (27, "OCEANIA", "AIR NIUGINI JET LANDS AFTER ENGINE FIRE"),
    (28, "OCEANIA", "AUSTRALIA SETS PARLIAMENT SWEARING RECORD"),
    (29, "AMERICAS", "WAYMO PULLS DRIVERLESS TAXIS OFF US FREEWAYS"),
    (30, "AMERICAS", "PERU: 6.8 QUAKE SHAKES LIMA, NO TSUNAMI"),
    (31, "AMERICAS", "HAITI TO BUILD 3 PRISONS WITH EL SALVADOR"),
    (32, "AMERICAS", "ICE ARRESTS AT SEATTLE AIRPORT CONDEMNED"),
    (33, "AFRICA", "MLAMBO-NGCUKA, 71, MOURNED IN SOUTH AFRICA"),
    (34, "AFRICA", "SENEGAL BOAT CAPSIZES: 4 DEAD, MANY MISSING"),
    (35, "AFRICA", "17 KILLED IN SOUTH AFRICA MASS SHOOTINGS"),
    (36, "AFRICA", "SOUTH SUDAN VOTE DELAYED TO FEBRUARY 2027"),
    (37, "AFRICA", "DRC EBOLA OUTBREAK HAMPERS AID DELIVERY"),
    (38, "GLOBAL", "UN: NEW RULES ON KILLER ROBOTS IN 2 YEARS"),
    (39, "GLOBAL", "IEA: AI DATA-CENTRE EMISSIONS UP 70% BY 2030"),
    (40, "GLOBAL", "EU BACKS ANTALYA COMPACT ON BUILDINGS"),
]

KPIS = [
    ("0", "DEALS AT COP31", RED),
    ("-11.6%", "S&P 500 IN CORRECTION", RED),
    ("1,600+", "DELTA FLIGHTS DELAYED", INK),
    ("3 · 36", "DEAD · MISSING, JAVA FIRE", INK),
    ("700,000+", "ROHINGYA FLED IN 2017", INK),
    ("121 M", "SPARTA II, STILL BURNING", INK),
]

REGION_ORDER = ["EUROPE", "MIDDLE EAST", "ASIA", "AMERICAS", "AFRICA",
                "OCEANIA", "GLOBAL"]
REGION_LABEL = {"EUROPE": "EUROPE 8", "MIDDLE EAST": "MIDDLE EAST 6",
                "ASIA": "ASIA 7", "AMERICAS": "AMERICAS 8",
                "AFRICA": "AFRICA 5", "OCEANIA": "OCE 2", "GLOBAL": "GLOBAL 4"}
REGION_COUNT = {"EUROPE": 8, "MIDDLE EAST": 6, "ASIA": 7, "AMERICAS": 8,
                "AFRICA": 5, "OCEANIA": 2, "GLOBAL": 4}


def region_badge(cv, x, y, num, region):
    """Numbered circle badge in the story's region colour."""
    colour = REGIONS[region]
    cv.circle(x + 8, y + 8, 8, colour)
    cv.ring(x + 8, y + 8, 8, INK, 1)
    label = str(num)
    cv.text(x + 8 - text_width(label, 1) // 2, y + 5, label, 1, WHITE)


def draw_card(cv, x, y, w, h, story, large):
    num, region, kicker, headline, body, source, scene, _lon, _lat = story
    colour = REGIONS[region]
    cv.rect(x, y, w, h, WHITE)
    cv.rect(x, y, w, 2, colour)
    cv.rect(x, y, 2, h, colour)
    cv.rect(x + w - 2, y, 2, h, colour)
    cv.rect(x, y + h - 2, w, 2, colour)
    band = 78 if large else 54
    SCENES[scene](cv, x + 4, y + 4, w - 8, band)
    region_badge(cv, x + 4, y + 4, num, region)
    ky = y + band + 8
    cv.text(x + 6, ky, kicker, 1, colour)
    hy = ky + 12
    head_lines = wrap(headline, w - 12, 2)[:3]
    for i, line in enumerate(head_lines):
        cv.text(x + 6, hy + i * 15, line, 2, INK)
    by = hy + len(head_lines) * 15 + 3
    body_lines = wrap(body, w - 12, 1)[:4 if not large else 3]
    for i, line in enumerate(body_lines):
        cv.text(x + 6, by + i * 10, line, 1, INK)
    cv.text_right(x + w - 6, y + h - 12, source, 1, GREY)


# ------------------------------------------------------------------ layout
def build():
    cv = Canvas(W, H, CREAM)
    mx = 22  # side margin
    cw = W - 2 * mx  # 980 content width

    # Utility line
    cv.text(mx, 12, "THE WORLD IN ONE DAY", 1, RED)
    cv.text_right(mx + cw, 12, "40 STORIES · 7 REGIONS · ALL FROM THIS ONE DAY",
                  1, GREY)

    # Masthead
    cv.text_centre(W // 2, 28, "MONDAY 23 NOVEMBER 2026", 6, INK)
    cv.hline(mx, 78, cw, INK, 3)

    # Kicker line under the masthead
    cv.text_centre(W // 2, 86,
                   "COP31 COLLAPSES · ICJ: MYANMAR GENOCIDE · SPARTA II "
                   "STILL BURNING", 2, RED)

    # Region bar: segments proportional to story counts
    bx, by, bh = mx, 106, 18
    total = sum(REGION_COUNT.values())
    cx = bx
    for region in REGION_ORDER:
        seg = int(round(REGION_COUNT[region] / total * cw))
        colour = REGIONS[region]
        cv.rect(cx, by, seg, bh, colour)
        label = REGION_LABEL[region]
        if text_width(label, 1) <= seg - 6:
            cv.text(cx + 4, by + 6, label, 1, WHITE)
        cx += seg
    cv.rect(bx, by, cw, 1, INK)
    cv.rect(bx, by + bh - 1, cw, 1, INK)

    # KPI strip: six stats
    kx, ky, kw, kh = mx, 132, cw // 6, 46
    for i, (big, label, colour) in enumerate(KPIS):
        cell_x = kx + i * kw
        if i > 0:
            cv.vline(cell_x, ky + 4, kh - 8, LIGHT, 1)
        cv.text(cell_x + 6, ky + 2, big, 3, colour)
        for j, line in enumerate(wrap(label, kw - 12, 1)[:2]):
            cv.text(cell_x + 6, ky + 26 + j * 10, line, 1, GREY)
    cv.hline(mx, ky + kh, cw, INK, 1)

    # Large cards: 3 across
    gap = 10
    lw = (cw - 2 * gap) // 3
    ly, lh = 188, 192
    for i, story in enumerate(CARDS[:3]):
        draw_card(cv, mx + i * (lw + gap), ly, lw, lh, story, large=True)

    # Small cards: 5 + 5
    sw = (cw - 4 * gap) // 5
    for row, y0 in enumerate((388, 572)):
        for i, story in enumerate(CARDS[3 + row * 5:8 + row * 5]):
            draw_card(cv, mx + i * (sw + gap), y0, sw, 176, story,
                      large=False)

    # Map + ALSO list
    my = 756
    cv.text(mx, my, "WHERE IT HAPPENED", 2, INK)
    cv.text(mx + 414, my, "ALSO ON MONDAY 23 NOVEMBER", 2, RED)
    map_x, map_y, map_w, map_h = mx, my + 20, 398, 138
    # Nudges so the crowded Europe pins (and the two US pins) do not touch.
    PIN_ADJUST = {1: (0, 10), 2: (6, -14), 3: (-8, -6), 4: (-4, -10),
                  5: (8, -8), 6: (8, 4), 7: (14, 8), 11: (-8, 6),
                  12: (6, -6)}
    pins = []
    for num, region, _k, _h, _b, _s, _sc, lon, lat in CARDS:
        if lon is None:
            continue
        dx, dy = PIN_ADJUST.get(num, (0, 0))
        px = int(map_x + (lon + 180.0) / 360.0 * map_w) + dx
        py = int(map_y + (80.0 - lat) / 140.0 * map_h) + dy
        pins.append((px, py, num, REGIONS[region]))
    draw_map(cv, map_x, map_y, map_w, map_h, pins)
    cv.text(mx, map_y + map_h + 4,
            "PINS: STORIES 1–12 · POSITIONS APPROXIMATE", 1, GREY)
    cv.text(mx, map_y + map_h + 15,
            "13 · RIEMANN — OFF THE MAP, IN THE CLOUD", 1, GREY)

    ax, ay = mx + 414, my + 20
    col_w = (cw - 414) // 2  # two columns of ALSO items
    for idx, (num, region, line) in enumerate(ALSO):
        col = idx // 14
        row = idx % 14
        ix = ax + col * col_w
        iy = ay + row * 13
        colour = REGIONS[region]
        cv.rect(ix, iy - 1, 13, 11, colour)
        label = str(num)
        cv.text(ix + 7 - text_width(label, 1) // 2, iy + 1, label, 1, WHITE)
        text = line
        if text_width(text, 1) > col_w - 20:
            # shorten to fit the column
            while text and text_width(text + "...", 1) > col_w - 20:
                text = text[:-1]
            text += "..."
        cv.text(ix + 17, iy + 1, text, 1, INK)

    # DATE CHECK box
    dy = 956
    cv.rect(mx, dy, cw, 1, RED)
    cv.rect(mx, dy + 44, cw, 1, RED)
    cv.vline(mx, dy, 45, RED, 1)
    cv.vline(mx + cw - 1, dy, 45, RED, 1)
    cv.text(mx + 6, dy + 5,
            "DATE CHECK  LEFT OUT ON PURPOSE: HUANG'S NVIDIA RESIGNATION, "
            "12 NOV · THE FAA NATIONWIDE GROUND STOP, 13 NOV · UNITED'S "
            "OUTAGE, 16 NOV.", 1, RED)
    cv.text(mx + 6, dy + 17,
            "ALL 40 STORIES HAPPENED, OR WERE FIRST REPORTED, ON MONDAY 23 "
            "NOVEMBER 2026. CONTESTED CLAIMS ARE ATTRIBUTED.", 1, INK)
    cv.text(mx + 6, dy + 29,
            "HOW SURE ARE WE?  REPORTED = WIRE-CONFIRMED · CLAIM = "
            "ATTRIBUTED, NOT SETTLED.", 1, GREY)

    # Footer
    cv.text(mx, 1008, "SOURCES: REUTERS · AP · AFP · BBC · UN", 1, GREY)
    cv.text_right(mx + cw, 1008,
                  "ORIGINAL DRAWINGS, DRAWN IN CODE · 2026-11-23", 1, GREY)
    return cv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    out_dir = args.output or os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
