#!/usr/bin/env python3
"""Render the V1fresh2 front page for news-image-20261122.

Written fresh in this session for the V1fresh2 entry (BUILDER from zero).
Layout: giant date masthead, dark numbers ribbon, UTC strip with an
overnight band and a 24:00 end mark, one hero lead + two stacked leads,
eleven medium cards, a numbered-pin map beside a numbered list, DATE CHECK.
Deterministic: no clock, no randomness, no network. Stdlib + Pillow only.

Usage: python3 render.py [out.png]   (default: entry.png in this folder)
"""
import hashlib
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 24
GAP = 12
CONTENT_W = W - 2 * MARGIN  # 976

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

# ---------------------------------------------------------------- palette
PAPER = (247, 241, 227)      # cream paper
PAPER_DK = (238, 231, 214)   # slightly darker cream (card tint)
INK = (26, 26, 26)           # near-black ink
NAVY = (20, 38, 63)          # dark ribbon / map sea
NAVY_LT = (38, 62, 94)
BRICK = (176, 58, 46)        # red accent, reserved for the gravest
BRICK_DK = (140, 44, 34)
GREY = (90, 86, 76)
GREY_LT = (200, 192, 176)
WHITE = (255, 255, 255)
SKY_NIGHT = (16, 28, 52)
GOLD = (212, 160, 60)
ORANGE = (224, 122, 42)

# Region colours (white text on each must pass 4.5:1; asserted in main()).
REGION = {
    "EU": (47, 93, 138),     # blue
    "ME": (154, 74, 46),     # terracotta
    "AM": (46, 107, 79),     # green
    "AS": (122, 90, 30),     # ochre brown
    "AF": (110, 60, 96),     # plum
    "OC": (44, 110, 110),    # teal
    "WORLD": (70, 70, 78),   # slate
}
REGION_NAME = {
    "EU": "EUROPE", "ME": "MID. EAST", "AM": "AMERICAS", "AS": "ASIA",
    "AF": "AFRICA", "OC": "OCEANIA", "WORLD": "WORLD",
}

# ---------------------------------------------------------------- data
# (num, title, place, region, field, status, big, deck, archetype)
LEADS = [
    (1, "186 DRONES OVER UKRAINE", "KYIV", "EU", "CONFLICT", "CONFIRMED",
     "186",
     "Russia fires 186 drones overnight; defences down 161 by 06:00 UTC. "
     "One hits a block of flats near Kyiv; 3 killed.",
     "drones"),
    (2, "COP31 COLLAPSES", "ANTALYA", "WORLD", "CLIMATE", "CONFIRMED",
     "NO DEAL",
     "The EU rejects a pact with no mention of fossil fuels. The longest "
     "COP ever ends with no deal.",
     "cop"),
    (3, "IRAN STRIKES BAHRAIN", "MANAMA", "ME", "CONFLICT", "CONFIRMED",
     "2 HURT",
     "Bahrain says two were hurt. Iran's claim of hitting US radars "
     "is disputed.",
     "bahrain"),
]

# (num, title, place, region, field, status, big, summary, archetype)
MEDIUM = [
    (4, "UKRAINE SINKS RUSSIAN WARSHIP", "BENGHAZI", "AF", "CONFLICT",
     "CONFIRMED", "2,400 KM",
     "Sea drones sink the corvette Merkury at a Libyan naval base.",
     "ship"),
    (5, "MARQUEZ TAKES 8TH TITLE", "PORTIMÃO", "EU", "SPORT",
     "CONFIRMED", "8TH",
     "Bezzecchi wins the race; Marquez finishes 8th and takes the crown.",
     "moto"),
    (6, "DEMOCRATS WIN 258 SEATS", "WASHINGTON", "AM", "POLITICS",
     "CONFIRMED", "258",
     "Largest House majority since 1992; Hubbard wins by 330 votes.",
     "capitol"),
    (7, "BOAT CAPSIZES, 24 DEAD", "BAYELSA", "AF", "DISASTER",
     "CONFIRMED", "24 DEAD",
     "Boat carrying mourners capsizes; toll of 24 confirmed Sunday.",
     "boat"),
    (8, "TANKERS HIT NEAR HORMUZ", "HORMUZ", "ME", "ENERGY",
     "REPORTED", "2",
     "Iran says two supertankers hit mines; a separate incident in the Gulf of Oman.",
     "tanker"),
    (9, "STORM TOLL RISES TO 5", "TUPANCIRETÃ", "AM", "DISASTER",
     "CONFIRMED", "5 DEAD",
     "Supercell storm toll rises to 5 dead, 250+ hurt, 8,000 homes damaged.",
     "storm"),
    (10, "MINISTER QUITS OVER AI CHEATING", "SEOUL", "AS", "EDUCATION",
     "CONFIRMED", "111",
     "Education minister resigns after an AI cheating scandal at the entrance exam.",
     "exam"),
    (11, "RUSSIAN MISSILES IN POLAND", "LUBLIN", "EU", "SECURITY",
     "CONFIRMED", "3",
     "Prosecutors confirm all three fallen objects were Russian Kh-101 missiles.",
     "missile"),
    (12, "BEPICOLOMBO ORBITS MERCURY", "MERCURY", "WORLD", "SPACE",
     "CONFIRMED", "ORBIT",
     "Probe enters orbit around Mercury after an eight-year journey.",
     "space"),
    (13, "LIVERPOOL 4–0 MAN UTD", "LIVERPOOL", "EU", "SPORT",
     "CONFIRMED", "4–0",
     "Liverpool rout Manchester United 4–0 at Anfield.",
     "football"),
    (14, "FACTORY FIRE, 3 DEAD, 36 MISSING", "CIKANDE", "AS", "DISASTER",
     "CONFIRMED", "36",
     "Fire at a factory in Cikande; 3 dead, 36 people missing.",
     "factory"),
]

# (num, city, text, region, status) — one line each, numbered 15-41.
BRIEFS = [
    (15, "WEST BANK", "Settlers torch 12 vehicles", "ME", "CONFIRMED"),
    (16, "KHARTOUM", "Drone attack kills 4", "AF", "CONFIRMED"),
    (17, "KANSAS CITY", "Chiefs beat Cardinals 34–7", "AM", "CONFIRMED"),
    (18, "BARRANQUILLA", "Boca beat Atlético Mineiro 2–0", "AM", "CONFIRMED"),
    (19, "LAHORE", "Air quality passes 500 AQI", "AS", "CONFIRMED"),
    (20, "WELLINGTON", "India pile up 720/9 v New Zealand", "AS", "CONFIRMED"),
    (21, "GULF OF FINLAND", "Sparta II still smouldering", "EU", "REPORTED"),
    (22, "GAZA", "IDF strike leaves 1 critically hurt", "ME", "CONFIRMED"),
    (23, "QAA", "Lebanon arrests 3, seizes 264 kg of explosives", "ME", "CONFIRMED"),
    (24, "WARSAW", "Russia twice tried to kill a rapper, Poland says", "EU", "CONFIRMED"),
    (25, "RUATŌRIA", "House slips: 1 dead, 4 hurt", "OC", "CONFIRMED"),
    (26, "NFL", "Cowboys 51–30 Titans; Panthers 35–33 Ravens", "AM", "CONFIRMED"),
    (27, "VILLARREAL", "Barcelona come back 3–2 from 2–0 down", "EU", "CONFIRMED"),
    (28, "MELBOURNE", "Olympians reunite, 70 yrs on", "OC", "CONFIRMED"),
    (29, "RABIGH", "Houthis claim hit on Saudi refinery", "ME", "REPORTED"),
    (30, "LAS VEGAS", "Verstappen wins chaotic GP, 35 lead changes", "AM", "CONFIRMED"),
    (31, "SAN ANTONIO", "Wembanyama: 50 pts, 19 reb, Spurs win", "AM", "CONFIRMED"),
    (32, "WASHINGTON", "Kansas City Current win NWSL title 2–1", "AM", "CONFIRMED"),
    (33, "KYIV", "Zelensky: 2,700 drones in a week; wants Patriots", "EU", "CONFIRMED"),
    (34, "HERZLIYA", "Eisenkot–Likud unity talks end, no deal", "ME", "CONFIRMED"),
    (35, "RŪDNINKAI", "Germany tests kamikaze drones near Belarus", "EU", "CONFIRMED"),
    (36, "OYO", "Kenya and DR Congo restore full ties", "AF", "CONFIRMED"),
    (37, "HONG KONG", "Election poll: 856 vie for 723 seats, 98.79%", "AS", "CONFIRMED"),
    (38, "JOHANNESBURG", "ANC–ActionSA: Mashaba for mayor", "AF", "REPORTED"),
    (39, "TEHRAN", "Iran begins electricity rationing, cuts to 2 hrs", "ME", "CONFIRMED"),
    (40, "BEIRUT", "Aoun: Israel must withdraw; arms under the state", "ME", "REPORTED"),
    (41, "BRASÍLIA", "Bolsonaro in intensive care, bowel obstruction", "AM", "CONFIRMED"),
]

REGION_COUNTS = [("EU", 9), ("ME", 9), ("AM", 9), ("AS", 5), ("AF", 5),
                 ("OC", 2), ("WORLD", 2)]

# Numbers ribbon: (big, label, story num)
RIBBON = [
    ("186", "DRONES FIRED", 1),
    ("161", "SHOT DOWN", 1),
    ("258", "HOUSE SEATS", 6),
    ("2,400 KM", "TO BENGHAZI", 4),
    ("720/9", "INDIA'S INNINGS", 20),
    ("50", "WEMBANYAMA PTS", 31),
]

# UTC strip events: (hour float, label, story num or None)
# Verified: BepiColombo confirmation 00:56Z; 161 down by 06:00Z (08:00 Kyiv);
# HK polls close 10:00Z (18:00 HKT); Liverpool kick-off 16:30Z.
UTC_EVENTS = [
    (0.93, "BEPICOLOMBO CONFIRMED", 12),
    (6.0, "161 DRONES DOWN", 1),
    (10.0, "HK POLLS CLOSE", 37),
    (16.5, "LIVERPOOL KICK-OFF", 13),
]

DATE_CHECK = (
    "DATE CHECK — Nigeria boat capsized Friday; toll of 24 confirmed Sunday. "
    "Brazil storm was Friday; 5 dead is Sunday's update. Poland missiles fell "
    "Friday; identified Sunday. Bahrain strike was Saturday; 2 hurt announced "
    "Sunday. BepiColombo burned Saturday; ESA confirmed it Sunday. "
    "F1, NBA, NWSL finals: Sat. night in the US."
)
NOT_SHOWN = (
    "NOT SHOWN: ICJ Rohingya ruling (19 Nov) · UK–EU reset (20 Nov) · "
    "GTA VI $3.79bn (20 Nov) — not 22 November news."
)

# Map pins: story num -> (lon, lat, badge offset dx, dy in px from dot)
PINS = {
    1: (30.5, 50.4, 26, -22),    # Kyiv
    2: (30.7, 36.9, 30, 14),     # Antalya
    3: (50.6, 26.2, 24, -20),    # Manama
    4: (20.1, 32.1, -34, 12),    # Benghazi
    5: (-8.5, 37.1, -36, -6),    # Portimao
    6: (-77.0, 38.9, -8, -26),   # Washington
    7: (6.3, 4.9, -30, 16),      # Bayelsa
    8: (56.5, 27.0, 26, 10),     # Hormuz
    9: (-53.8, -29.0, -6, -26),  # Tupancireta
    10: (127.0, 37.5, 22, -22),  # Seoul
    11: (22.6, 51.2, -14, -24),  # Lublin (badge moved right: was -30,
    # it touched badge 13; keep clear of pin 13's dot and pin 1's badge)
    13: (-3.0, 53.4, -46, -20),  # Liverpool (badge moved left: was -34,
    # it touched badge 11)
    14: (106.1, -6.2, 24, 12),   # Cikande
}

# ---------------------------------------------------------------- fonts
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


F_SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)
F_SERIF = lambda s: font("DejaVuSerif.ttf", s)
F_SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)
F_SANS = lambda s: font("DejaVuSans.ttf", s)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def wrap(draw, s, f, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text(draw, xy, s, f, fill, anchor="la"):
    draw.text(xy, s, font=f, fill=fill, anchor=anchor)


def fit_size(draw, s, fname, start, max_w, min_size=8):
    """Largest font size (<= start) at which s fits max_w."""
    size = start
    while size > min_size:
        f = font(fname, size)
        if draw.textlength(s, font=f) <= max_w:
            return f, size
        size -= 1
    return font(fname, min_size), min_size


# ---------------------------------------------------------------- contrast
def _lum(rgb):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------- helpers
def rounded_rect(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline,
                           width=width)


def status_chip(draw, x, y, status):
    """Small status chip; returns width used."""
    f = F_SANS_B(9)
    label = {"CONFIRMED": "CONFIRMED", "REPORTED": "REPORTED",
             "CLAIM": "CLAIM"}[status]
    w = int(draw.textlength(label, font=f)) + 12
    fill = (46, 107, 79) if status == "CONFIRMED" else (154, 74, 46)
    rounded_rect(draw, [x, y, x + w, y + 14], 3, fill=fill)
    draw_text(draw, (x + 6, y + 2), label, f, WHITE)
    return w


def number_badge(draw, x, y, num, region, size=20):
    """Region-coloured square with the story number; returns size."""
    rounded_rect(draw, [x, y, x + size, y + size], 3, fill=REGION[region])
    f = F_SANS_B(12 if size >= 20 else 10)
    tw = draw.textlength(str(num), font=f)
    draw_text(draw, (x + (size - tw) / 2, y + (size - 13) / 2 + 1),
              str(num), f, WHITE)
    return size

# ---------------------------------------------------------------- illustrations
# Flat geometric scenes. Each bakes ONE number (its story's big figure).
# No humans are drawn anywhere. One bright accent per scene.

def _stars(draw, box, n, seed=7):
    x0, y0, x1, y1 = box
    # deterministic pseudo-random from a fixed seed sequence
    s = seed
    for _ in range(n):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        x = x0 + (s % (x1 - x0))
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        y = y0 + (s % (y1 - y0))
        r = 1 if s % 3 else 2
        draw.ellipse([x - r, y - r, x + r, y + r], fill=WHITE)


def _drone(draw, cx, cy, scale=1.0, body=(40, 40, 44)):
    """Small quadcopter silhouette: body + 4 rotor arms + rotor discs."""
    s = scale
    draw.ellipse([cx - 7 * s, cy - 4 * s, cx + 7 * s, cy + 4 * s], fill=body)
    for dx, dy in ((-11, -7), (11, -7), (-11, 7), (11, 7)):
        draw.line([cx, cy, cx + dx * s, cy + dy * s], fill=body, width=2)
        draw.ellipse([cx + dx * s - 5 * s, cy + dy * s - 2 * s,
                      cx + dx * s + 5 * s, cy + dy * s + 2 * s],
                     fill=(200, 200, 200))
    draw.ellipse([cx - 2 * s, cy - 2 * s, cx + 2 * s, cy + 2 * s],
                 fill=ORANGE)


def _burst(draw, cx, cy, r, colour=ORANGE):
    for k in range(8):
        ang = k * math.pi / 4
        x2 = cx + r * math.cos(ang)
        y2 = cy + r * math.sin(ang)
        draw.line([cx, cy, x2, y2], fill=colour, width=3)
    draw.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45],
                 fill=colour)
    draw.ellipse([cx - r * 0.2, cy - r * 0.2, cx + r * 0.2, cy + r * 0.2],
                 fill=(255, 214, 90))


def _skyline(draw, box, colour, heights):
    x0, y0, x1, y1 = box
    n = len(heights)
    w = (x1 - x0) / n
    for i, h in enumerate(heights):
        bx0 = x0 + i * w + 1
        bx1 = x0 + (i + 1) * w - 1
        draw.rectangle([bx0, y1 - h, bx1, y1], fill=colour)


def scene_drones(draw, box, big, hero=False):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=SKY_NIGHT)
    _stars(draw, [x0, y0, x1, y0 + (y1 - y0) * 0.6], 26 if hero else 12)
    # moon
    draw.ellipse([x1 - 52, y0 + 10, x1 - 22, y0 + 40], fill=(235, 225, 190))
    # drones with lit trails
    for (dx, dy, sc) in ((0.22, 0.30, 1.0), (0.45, 0.18, 0.8),
                         (0.68, 0.34, 1.1), (0.85, 0.22, 0.7)):
        cx = x0 + (x1 - x0) * dx
        cy = y0 + (y1 - y0) * dy
        _drone(draw, cx, cy, sc)
        draw.line([cx - 26 * sc, cy + 10, cx - 8 * sc, cy + 4],
                  fill=ORANGE, width=2)
    # explosions over the skyline
    _burst(draw, x0 + (x1 - x0) * 0.30, y0 + (y1 - y0) * 0.72, 13)
    _burst(draw, x0 + (x1 - x0) * 0.78, y0 + (y1 - y0) * 0.66, 10)
    _skyline(draw, [x0, y1 - 34, x1, y1], (10, 18, 36),
             [30, 18, 26, 12, 22, 30, 16, 24] if hero else [24, 14, 20, 12])
    # baked number
    f = F_SANS_B(44 if hero else 30)
    draw_text(draw, (x0 + 10, y0 + 8), big, f, WHITE)


def scene_cop(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(232, 222, 200))
    # big figure across the top, clear of everything else
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, BRICK_DK)
    # globe, small, bottom-left
    cx, cy, r = x0 + 24, y1 - 22, 15
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(47, 93, 138))
    draw.ellipse([cx - r + 5, cy - r + 4, cx - r + 12, cy - r + 10],
                 fill=(46, 107, 79))
    draw.ellipse([cx + 1, cy + 2, cx + 9, cy + 9], fill=(46, 107, 79))
    # cracked ground
    draw.line([x0, y1 - 8, x1, y1 - 8], fill=BRICK, width=2)
    # document with a red cross, bottom-right
    dx0, dy0 = x1 - 50, y1 - 50
    draw.rectangle([dx0, dy0, dx0 + 40, dy0 + 42], fill=WHITE,
                   outline=INK, width=2)
    for i in range(3):
        draw.line([dx0 + 5, dy0 + 8 + i * 9, dx0 + 35, dy0 + 8 + i * 9],
                  fill=GREY, width=2)
    draw.line([dx0 + 6, dy0 + 6, dx0 + 34, dy0 + 36], fill=BRICK, width=3)
    draw.line([dx0 + 34, dy0 + 6, dx0 + 6, dy0 + 36], fill=BRICK, width=3)


def scene_bahrain(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(24, 32, 56))
    _stars(draw, [x0, y0, x1, y0 + (y1 - y0) * 0.5], 10)
    # missile trails (dashed arcs) + one burst
    for (sx, ex) in ((0.15, 0.55), (0.45, 0.85)):
        px, py = x0 + (x1 - x0) * sx, y0 + (y1 - y0) * 0.15
        qx, qy = x0 + (x1 - x0) * ex, y0 + (y1 - y0) * 0.62
        for t in range(0, 11):
            if t % 2 == 0:
                tt = t / 10.0
                x = px + (qx - px) * tt
                y = py + (qy - py) * tt - 18 * math.sin(tt * math.pi)
                draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=ORANGE)
    _burst(draw, x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.66, 11)
    _skyline(draw, [x0, y1 - 30, x1, y1], (12, 20, 40),
             [26, 16, 22, 12, 20])
    # lit windows
    for (wx, wy) in ((0.12, 0.78), (0.38, 0.72), (0.7, 0.76)):
        draw.rectangle([x0 + (x1 - x0) * wx, y0 + (y1 - y0) * wy,
                        x0 + (x1 - x0) * wx + 6, y0 + (y1 - y0) * wy + 8],
                       fill=(255, 214, 90))
    f = F_SANS_B(24)
    draw_text(draw, (x0 + 8, y0 + 6), big, f, WHITE)


def scene_ship(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(214, 228, 236))
    # sea
    draw.rectangle([x0, y0 + (y1 - y0) * 0.62, x1, y1], fill=(47, 93, 138))
    for k in range(4):
        wx = x0 + 8 + k * 34
        wy = y0 + (y1 - y0) * (0.68 + 0.08 * (k % 2))
        draw.arc([wx, wy, wx + 26, wy + 10], 0, 180, fill=WHITE, width=2)
    # warship silhouette, kept low so the baked number stays clear
    hx0, hy = x0 + 22, y0 + (y1 - y0) * 0.66
    draw.polygon([(hx0, hy), (hx0 + 88, hy), (hx0 + 78, hy + 12),
                  (hx0 + 8, hy + 12)], fill=(40, 44, 52))
    draw.rectangle([hx0 + 32, hy - 10, hx0 + 54, hy], fill=(40, 44, 52))
    # (no mast: it would scratch through the baked number)
    # two small sea drones approaching, below the baked number
    for dx in (0.62, 0.78):
        _drone(draw, x0 + (x1 - x0) * dx, y0 + (y1 - y0) * 0.56, 0.55,
               body=(90, 40, 30))
    # baked number LAST, so it sits on top of the ship
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, INK)


def scene_moto(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(233, 226, 208))
    # track curve, kept low so its top edge stays below the baked number
    # (number zone ends ~y0+20; arc top edge ~y0+23) and its ends stay
    # out of the neighbouring cards' title lines
    draw.arc([x0 - 10, y0 + (y1 - y0) * 0.66, x1 - 2, y1 + 30], 200, 340,
             fill=(90, 86, 76), width=10)
    draw.arc([x0 - 10, y0 + (y1 - y0) * 0.66, x1 - 2, y1 + 30], 200, 340,
             fill=BRICK, width=3)
    # motorcycle, side profile, no rider: two wheels + body + tank.
    # Shifted right and shrunk so no part enters the baked-number zone
    # (x0+8..x0+52, y0+4..y0+20): left wheel starts at x0+56, all frame
    # lines start at x0+67 or further right.
    cx, cy = x0 + (x1 - x0) * 0.62, y0 + (y1 - y0) * 0.66
    for wx in (cx - 26, cx + 26):
        draw.ellipse([wx - 11, cy - 11, wx + 11, cy + 11], outline=INK,
                     width=5)
        draw.ellipse([wx - 4, cy - 4, wx + 4, cy + 4], fill=INK)
    draw.line([cx - 26, cy, cx + 26, cy], fill=INK, width=5)
    draw.line([cx - 8, cy, cx + 8, cy - 20], fill=BRICK, width=7)
    draw.line([cx + 8, cy - 20, cx + 26, cy - 6], fill=BRICK, width=6)
    draw.line([cx - 26, cy, cx - 6, cy - 18], fill=INK, width=4)
    # checkered flag
    fx, fy = x1 - 34, y0 + 8
    for r in range(2):
        for c in range(3):
            col = INK if (r + c) % 2 == 0 else WHITE
            draw.rectangle([fx + c * 8, fy + r * 8, fx + c * 8 + 8,
                            fy + r * 8 + 8], fill=col)
    draw.line([fx, fy, fx, fy + 26], fill=INK, width=2)
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, BRICK_DK)


def scene_capitol(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(222, 228, 232))
    cx = x0 + (x1 - x0) * 0.5
    base = y1 - 6
    # dome, small: fits inside a 48 px tall scene
    draw.rectangle([cx - 34, base - 20, cx + 34, base], fill=(90, 100, 112))
    draw.pieslice([cx - 25, base - 38, cx + 25, base - 8], 180, 360,
                  fill=(90, 100, 112))
    draw.rectangle([cx - 42, base - 5, cx + 42, base], fill=(70, 78, 90))
    # columns
    for dx in (-26, -9, 9, 26):
        draw.rectangle([cx + dx - 3, base - 18, cx + dx + 3, base - 5],
                       fill=WHITE)
    # ballot slips, top-right
    for k in range(2):
        draw.rectangle([x1 - 34 + k * 12, y0 + 8, x1 - 26 + k * 12, y0 + 22],
                       fill=WHITE, outline=INK, width=1)
    # baked number LAST, so it sits on top of the dome
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, NAVY)


def scene_boat(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(210, 224, 230))
    # waves
    for k in range(3):
        wy = y0 + (y1 - y0) * (0.55 + k * 0.14)
        for x in range(x0, x1, 26):
            draw.arc([x, wy, x + 24, wy + 12], 0, 180, fill=(47, 93, 138),
                     width=2)
    # capsized boat: hull upside down
    hx0, hy = x0 + (x1 - x0) * 0.3, y0 + (y1 - y0) * 0.52
    draw.polygon([(hx0, hy), (hx0 + 70, hy), (hx0 + 58, hy - 16),
                  (hx0 + 12, hy - 16)], fill=(120, 70, 40))
    draw.rectangle([hx0 + 28, hy - 22, hx0 + 42, hy - 16], fill=(120, 70, 40))
    # concentric ripples
    for r in (10, 18, 26):
        draw.ellipse([hx0 + 35 - r, hy + 2 - r // 2, hx0 + 35 + r,
                      hy + 2 + r // 2], outline=(47, 93, 138), width=2)
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, INK)


def scene_tanker(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(226, 220, 204))
    draw.rectangle([x0, y0 + (y1 - y0) * 0.66, x1, y1], fill=(47, 93, 138))
    # tanker, kept low so the baked number stays clear
    hx0, hy = x0 + 16, y0 + (y1 - y0) * 0.66
    draw.rectangle([hx0, hy, hx0 + 88, hy + 14], fill=(140, 44, 34))
    draw.rectangle([hx0 + 62, hy - 10, hx0 + 82, hy], fill=(140, 44, 34))
    draw.line([hx0 + 72, hy - 16, hx0 + 72, hy - 10], fill=(140, 44, 34),
              width=3)
    # mine: spiky circle
    mx, my = x0 + (x1 - x0) * 0.82, y0 + (y1 - y0) * 0.42
    for k in range(8):
        ang = k * math.pi / 4
        draw.line([mx, my, mx + 16 * math.cos(ang), my + 16 * math.sin(ang)],
                  fill=INK, width=2)
    draw.ellipse([mx - 9, my - 9, mx + 9, my + 9], fill=INK)
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, INK)


def scene_storm(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(200, 205, 212))
    # clouds, right half only so the baked number stays clear
    for (cx, cy, r) in ((0.68, 0.22, 18), (0.88, 0.32, 14)):
        draw.ellipse([x0 + (x1 - x0) * cx - r, y0 + (y1 - y0) * cy - r * 0.6,
                      x0 + (x1 - x0) * cx + r, y0 + (y1 - y0) * cy + r * 0.6],
                     fill=(70, 78, 90))
    # lightning, kept inside the 48 px scene
    lx, ly = x0 + (x1 - x0) * 0.55, y0 + (y1 - y0) * 0.35
    draw.polygon([(lx, ly), (lx - 6, ly + 14), (lx - 1, ly + 14),
                  (lx - 7, ly + 28), (lx + 4, ly + 13), (lx - 1, ly + 13)],
                 fill=(255, 214, 90))
    # house
    hx0, hy = x0 + (x1 - x0) * 0.14, y0 + (y1 - y0) * 0.68
    draw.rectangle([hx0, hy, hx0 + 34, hy + 20], fill=(154, 74, 46))
    draw.polygon([(hx0 - 4, hy), (hx0 + 17, hy - 14), (hx0 + 38, hy)],
                 fill=BRICK_DK)
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, INK)


def scene_exam(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(228, 226, 214))
    # baked number, top-left
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, BRICK_DK)
    # desk line across the bottom of the scene
    draw.rectangle([x0 + 8, y1 - 8, x1 - 8, y1 - 4], fill=(120, 90, 60))
    # exam paper, right of the number
    draw.rectangle([x0 + 54, y0 + 8, x0 + 96, y0 + 38], fill=WHITE,
                   outline=INK, width=2)
    for i in range(3):
        draw.line([x0 + 59, y0 + 14 + i * 8, x0 + 91, y0 + 14 + i * 8],
                  fill=GREY, width=2)
    # red stamp on the paper
    draw.ellipse([x0 + 72, y0 + 20, x0 + 90, y0 + 36], outline=BRICK,
                 width=2)
    # phone with AI, far right
    draw.rectangle([x1 - 36, y0 + 8, x1 - 12, y0 + 38], fill=INK)
    draw.rectangle([x1 - 32, y0 + 12, x1 - 16, y0 + 28],
                   fill=(120, 200, 120))
    f2 = F_SANS_B(8)
    draw_text(draw, (x1 - 30, y0 + 17), "AI", f2, INK)


def scene_missile(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(222, 226, 230))
    # sky + ground
    draw.rectangle([x0, y0 + (y1 - y0) * 0.7, x1, y1], fill=(150, 160, 140))
    # missile diagonal, right half only so the baked number stays clear
    mx, my = x0 + (x1 - x0) * 0.66, y0 + (y1 - y0) * 0.42
    draw.line([mx - 24, my + 18, mx + 24, my - 18], fill=(70, 78, 90),
              width=9)
    draw.polygon([(mx + 24, my - 18), (mx + 36, my - 10), (mx + 20, my - 4)],
                 fill=BRICK)
    draw.line([mx - 34, my + 26, mx - 24, my + 18], fill=ORANGE, width=4)
    draw.line([mx - 40, my + 28, mx - 34, my + 26], fill=(255, 214, 90),
              width=3)
    # impact marker
    ix, iy = x0 + (x1 - x0) * 0.8, y0 + (y1 - y0) * 0.74
    draw.ellipse([ix - 8, iy - 8, ix + 8, iy + 8], outline=BRICK, width=3)
    draw.ellipse([ix - 2, iy - 2, ix + 2, iy + 2], fill=BRICK)
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, INK)


def scene_space(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(14, 20, 38))
    # stars kept out of the baked-number zone (top-left, x0+8..x0+77,
    # y0+4..y0+20): the old full-box field could put a star on a glyph
    _stars(draw, [x0 + 80, y0, x1, y1], 9, seed=7)
    _stars(draw, [x0, y0 + 24, x0 + 80, y1], 7, seed=11)
    # Mercury: cratered orange disc, small enough for a 48 px scene
    cx, cy, r = x0 + (x1 - x0) * 0.68, y0 + (y1 - y0) * 0.56, 17
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(196, 120, 60))
    for (ox, oy, orr) in ((-7, -5, 4), (5, 3, 5), (-1, 7, 3), (7, -7, 3)):
        draw.ellipse([cx + ox - orr, cy + oy - orr, cx + ox + orr,
                      cy + oy + orr], fill=(160, 92, 44))
    # orbit arc + spacecraft, lower-left, below the baked number.
    # The old full-width arc (top y0+6) crossed the number "2ND"; this
    # arc stays in the lower-left (top y0+24, right end x0+80), clear of
    # both the number and the Mercury disc.
    draw.arc([x0 + 8, y0 + 24, x0 + 80, y1 - 2], 200, 340, fill=WHITE,
             width=2)
    sx, sy = x0 + 30, y0 + (y1 - y0) * 0.66
    draw.rectangle([sx - 8, sy - 6, sx + 8, sy + 6], fill=(200, 200, 200))
    draw.rectangle([sx - 26, sy - 3, sx - 8, sy + 3], fill=(47, 93, 138))
    draw.rectangle([sx + 8, sy - 3, sx + 26, sy + 3], fill=(47, 93, 138))
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, WHITE)


def scene_football(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(46, 107, 79))
    # pitch stripes
    for k in range(4):
        if k % 2 == 0:
            draw.rectangle([x0 + k * (x1 - x0) // 4, y0,
                            x0 + (k + 1) * (x1 - x0) // 4, y1],
                           fill=(56, 122, 90))
    # centre line + circle
    draw.line([x0 + (x1 - x0) // 2, y0, x0 + (x1 - x0) // 2, y1],
              fill=WHITE, width=2)
    draw.ellipse([x0 + (x1 - x0) // 2 - 16, y0 + (y1 - y0) // 2 - 16,
                  x0 + (x1 - x0) // 2 + 16, y0 + (y1 - y0) // 2 + 16],
                 outline=WHITE, width=2)
    # goal + ball
    gx0, gy = x1 - 40, y0 + (y1 - y0) * 0.3
    draw.rectangle([gx0, gy, gx0 + 30, gy + 34], outline=WHITE, width=3)
    bx, by = x0 + (x1 - x0) * 0.3, y0 + (y1 - y0) * 0.62
    draw.ellipse([bx - 11, by - 11, bx + 11, by + 11], fill=WHITE,
                 outline=INK, width=2)
    draw.polygon([(bx, by - 6), (bx + 5, by - 1), (bx + 3, by + 5),
                  (bx - 3, by + 5), (bx - 5, by - 1)], fill=INK)
    f = F_SANS_B(22)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, WHITE)


def scene_factory(draw, box, big):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(228, 222, 208))
    # factory block + chimney + smoke + flames
    fx0, fy = x0 + 16, y0 + (y1 - y0) * 0.55
    draw.rectangle([fx0, fy, fx0 + 74, y1 - 8], fill=(110, 100, 88))
    draw.polygon([(fx0, fy), (fx0 + 18, fy - 14), (fx0 + 56, fy - 14),
                  (fx0 + 74, fy)], fill=(90, 80, 70))
    draw.rectangle([fx0 + 78, fy - 22, fx0 + 90, y1 - 8], fill=(90, 80, 70))
    # smoke, kept fully inside the scene box: the old offsets
    # (fy-34-k*12) drew up to 58 px above the box and covered the text
    # of the card above; now the highest puff top is y0+2
    for k in range(3):
        sx = fx0 + 84 - k * 4
        sy = fy - 8 - k * 4
        draw.ellipse([sx - 7, sy - 5, sx + 7, sy + 5], fill=(160, 160, 160))
    # flames on the roof, kept below the baked number
    for (ox, oy, s) in ((0.35, 0.62, 9), (0.55, 0.58, 12), (0.75, 0.64, 8)):
        bx, by = x0 + (x1 - x0) * ox, y0 + (y1 - y0) * oy
        draw.polygon([(bx - s, by), (bx, by - s * 1.6), (bx + s, by)],
                     fill=ORANGE)
        draw.polygon([(bx - s * 0.5, by), (bx, by - s), (bx + s * 0.5, by)],
                     fill=(255, 214, 90))
    f = F_SANS_B(20)
    draw_text(draw, (x0 + 8, y0 + 4), big, f, INK)


SCENES = {
    "drones": scene_drones, "cop": scene_cop, "bahrain": scene_bahrain,
    "ship": scene_ship, "moto": scene_moto, "capitol": scene_capitol,
    "boat": scene_boat, "tanker": scene_tanker, "storm": scene_storm,
    "exam": scene_exam, "missile": scene_missile, "space": scene_space,
    "football": scene_football, "factory": scene_factory,
}

# Card background tints, cycled so no card shares a tint with a neighbour.
CARD_TINTS = [
    (255, 255, 255),
    (244, 238, 224),
    (238, 232, 214),
    (250, 246, 236),
]

# ---------------------------------------------------------------- world map
# Coarse continent polygons in (lon, lat). Simplified from memory; the map
# is a locator, not a survey chart. Antarctica omitted.
CONTINENTS = [
    # North America
    [(-168, 66), (-158, 71), (-140, 70), (-128, 71), (-110, 68), (-95, 69),
     (-85, 66), (-80, 73), (-70, 62), (-60, 55), (-55, 47), (-60, 42),
     (-70, 42), (-75, 35), (-80, 32), (-81, 26), (-84, 30), (-90, 29),
     (-97, 26), (-97, 16), (-94, 17), (-90, 14), (-83, 9), (-79, 9),
     (-83, 15), (-90, 21), (-97, 26), (-105, 20), (-110, 23), (-114, 28),
     (-117, 33), (-122, 37), (-124, 42), (-124, 48), (-130, 55), (-140, 60),
     (-152, 58), (-162, 55), (-168, 66)],
    # South America
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-74, -50),
     (-68, -55), (-66, -55), (-65, -45), (-62, -39), (-57, -35),
     (-52, -33), (-48, -28), (-41, -23), (-35, -9), (-35, -6),
     (-44, -3), (-50, 0), (-52, 5), (-58, 6), (-62, 9), (-68, 11),
     (-72, 12), (-77, 8), (-79, 9)],
    # Africa
    [(-17, 15), (-16, 20), (-10, 31), (-6, 35), (10, 37), (11, 34),
     (20, 32), (30, 31), (32, 31), (35, 28), (39, 21), (43, 12),
     (51, 11), (51, 2), (46, -2), (40, -10), (40, -18), (36, -26),
     (32, -29), (28, -33), (20, -35), (17, -32), (14, -22), (12, -17),
     (13, -10), (9, -1), (9, 4), (-8, 4), (-13, 8), (-17, 15)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-1, 50),
     (2, 51), (4, 53), (8, 57), (10, 59), (5, 60), (10, 62), (13, 66),
     (18, 69), (25, 71), (31, 70), (40, 68), (44, 68), (50, 69),
     (55, 68), (60, 69), (68, 73), (75, 73), (80, 73), (85, 75),
     (95, 76), (105, 77), (110, 74), (115, 73), (120, 73), (130, 72),
     (140, 72), (150, 70), (160, 70), (170, 67), (178, 65), (178, 62),
     (170, 60), (162, 60), (158, 53), (150, 59), (142, 59), (140, 53),
     (135, 43), (130, 42), (127, 40), (122, 38), (120, 34), (112, 32),
     (108, 35), (105, 38), (100, 40), (95, 40), (90, 42), (85, 42),
     (80, 43), (75, 45), (70, 46), (65, 46), (60, 47), (55, 47),
     (50, 46), (45, 44), (40, 42), (35, 42), (33, 41), (30, 41),
     (28, 41), (26, 40), (23, 36), (22, 37), (19, 40), (16, 38),
     (15, 38), (12, 44), (10, 44), (8, 44), (6, 43), (3, 42),
     (0, 38), (-2, 37), (-6, 36), (-9, 37), (-10, 36)],
    # Asia (simplified, Eurasia split from Europe at the Urals/Caucasus)
    [(-10, 36), (-9, 37), (-6, 36), (-2, 37), (0, 38), (3, 42), (6, 43),
     (8, 44), (10, 44), (12, 44), (15, 38), (16, 38), (19, 40), (22, 37),
     (23, 36), (26, 40), (28, 41), (30, 41), (33, 41), (35, 42),
     (40, 42), (45, 44), (50, 46), (55, 47), (60, 47), (65, 46),
     (70, 46), (75, 45), (80, 43), (85, 42), (90, 42), (95, 40),
     (100, 40), (105, 38), (108, 35), (112, 32), (120, 34), (122, 38),
     (127, 40), (130, 42), (135, 43), (140, 53), (142, 59), (150, 59),
     (158, 53), (162, 60), (170, 60), (178, 62), (178, 65), (170, 67),
     (160, 70), (150, 70), (140, 72), (130, 72), (120, 73), (110, 74),
     (105, 77), (95, 76), (85, 75), (80, 73), (75, 73), (68, 73),
     (60, 69), (55, 68), (50, 69), (44, 68), (40, 68), (31, 70),
     (25, 71), (18, 69), (13, 66), (10, 62), (5, 60), (10, 59),
     (8, 57), (4, 53), (2, 51), (-1, 50), (-4, 48), (-1, 46),
     (-2, 44), (-9, 43), (-10, 36)],
    # Australia
    [(114, -22), (114, -30), (115, -35), (120, -34), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -27), (153, -24), (146, -19),
     (142, -11), (142, -15), (137, -12), (135, -15), (132, -11),
     (130, -13), (126, -14), (122, -17), (118, -20), (114, -22)],
]


def project(lon, lat, box):
    x0, y0, x1, y1 = box
    # equirectangular, lon -170..190, lat 75..-58
    fx = (lon + 170) / 360.0
    fy = (75 - lat) / 133.0
    return (x0 + fx * (x1 - x0), y0 + fy * (y1 - y0))


def draw_map(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(214, 228, 236))
    # continents (draw Asia+Europe as one landmass via the combined list:
    # index 3 Europe and 4 Asia overlap; draw both, same colour)
    for poly in CONTINENTS:
        pts = [project(lon, lat, box) for lon, lat in poly]
        draw.polygon(pts, fill=(196, 188, 164), outline=(140, 132, 114))
    # graticule
    for lon in (-120, -60, 0, 60, 120):
        gx, _ = project(lon, 75, box)
        draw.line([gx, y0, gx, y1], fill=(190, 200, 208), width=1)
    # Mercury note (story 12 is not on Earth): bottom-left ocean
    draw_text(draw, (x0 + 6, y1 - 13), "12 · MERCURY — NOT ON THIS MAP",
              F_SANS_B(8), GREY)


def draw_pins(draw, box):
    """Numbered pins with leader lines to offset badges."""
    for num in sorted(PINS):
        lon, lat, dx, dy = PINS[num]
        px, py = project(lon, lat, box)
        region = {1: "EU", 2: "WORLD", 3: "ME", 4: "AF", 5: "EU", 6: "AM",
                  7: "AF", 8: "ME", 9: "AM", 10: "AS", 11: "EU",
                  13: "EU", 14: "AS"}[num]
        bx, by = px + dx, py + dy
        # clamp badge inside the map box
        bx = max(box[0] + 8, min(box[2] - 18, bx))
        by = max(box[1] + 16, min(box[3] - 18, by))
        draw.line([px, py, bx + 7, by + 7], fill=INK, width=1)
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=BRICK,
                     outline=WHITE, width=1)
        rounded_rect(draw, [bx, by, bx + 15, by + 15], 3,
                     fill=REGION[region], outline=WHITE, width=1)
        f = F_SANS_B(10)
        tw = draw.textlength(str(num), font=f)
        draw_text(draw, (bx + (15 - tw) / 2, by + 2), str(num), f, WHITE)


# ---------------------------------------------------------------- sections
def draw_masthead(draw):
    y = 8
    # kicker
    draw_text(draw, (MARGIN, y), "THE WORLD, CHECKED", F_SANS_B(15), BRICK)
    # date: largest text on the page
    f_date, _ = fit_size(draw, "SUNDAY 22 NOVEMBER 2026",
                         "DejaVuSerif-Bold.ttf", 66, CONTENT_W)
    draw_text(draw, (MARGIN, y + 20), "SUNDAY 22 NOVEMBER 2026", f_date,
              INK)
    # rule + count line
    ry = 100
    draw.line([MARGIN, ry, W - MARGIN, ry], fill=INK, width=2)
    draw_text(draw, (MARGIN, ry + 6),
              "41 STORIES  ·  7 REGIONS  ·  EVERY ONE DATED SUNDAY",
              F_SANS_B(13), INK)
    # region chips, right aligned
    cx = W - MARGIN
    f_chip = F_SANS_B(11)
    for code, n in reversed(REGION_COUNTS):
        label = "%s %d" % (code, n)
        w = int(draw.textlength(label, font=f_chip)) + 8
        cx -= w
        rounded_rect(draw, [cx, ry + 4, cx + w, ry + 20], 3,
                     fill=REGION[code])
        draw_text(draw, (cx + 4, ry + 6), label, f_chip, WHITE)
        cx -= 6
    return 122


def draw_ribbon(draw, y):
    """Dark numbers ribbon, full width; each number tags its story."""
    h = 60
    draw.rectangle([MARGIN, y, W - MARGIN, y + h], fill=NAVY)
    cell_w = CONTENT_W / len(RIBBON)
    f_big = F_SANS_B(30)
    f_lab = F_SANS_B(9)
    for i, (big, label, num) in enumerate(RIBBON):
        cx = MARGIN + i * cell_w
        if i:
            draw.line([cx, y + 8, cx, y + h - 8], fill=NAVY_LT, width=1)
        # shrink the big number if it is wide
        fb, _ = fit_size(draw, big, "DejaVuSans-Bold.ttf", 30,
                         cell_w - 34)
        draw_text(draw, (cx + 16, y + 8), big, fb, WHITE)
        draw_text(draw, (cx + 16, y + 40), label, f_lab, (200, 205, 215))
        # story tag on the label row (never over the number)
        tag = "#%d" % num
        tw = draw.textlength(tag, font=f_lab)
        draw_text(draw, (cx + cell_w - tw - 10, y + 40), tag, f_lab, GOLD)
    return y + h


def draw_utc_strip(draw, y):
    """THE DAY IN UTC: 00:00-24:00, overnight band, verified ticks, 24:00 end."""
    h = 38
    draw_text(draw, (MARGIN, y + 2), "THE DAY IN UTC", F_SANS_B(11), INK)
    lx0, lx1 = MARGIN + 118, W - MARGIN - 8
    ly = y + 26
    # overnight band 00:00-06:00
    band_x1 = lx0 + (lx1 - lx0) * 6.0 / 24.0
    draw.rectangle([lx0, y + 12, band_x1, ly + 4], fill=(232, 214, 200))
    draw_text(draw, (lx0 + 4, y + 12), "OVERNIGHT BARRAGE", F_SANS_B(8),
              BRICK_DK)
    # hour ticks
    for hr in (0, 4, 8, 12, 16, 20, 24):
        x = lx0 + (lx1 - lx0) * hr / 24.0
        draw.line([x, ly - 4, x, ly + 4], fill=INK, width=1)
        lab = "%02d:00" % hr
        f = F_SANS_B(8)
        tw = draw.textlength(lab, font=f)
        draw_text(draw, (x - tw / 2, ly + 6), lab, f, GREY)
    draw.line([lx0, ly, lx1, ly], fill=INK, width=2)
    # event ticks (labels above the line, alternating side by story)
    f_ev = F_SANS_B(8)
    for hr, label, num in UTC_EVENTS:
        x = lx0 + (lx1 - lx0) * hr / 24.0
        draw.line([x, ly - 9, x, ly + 1], fill=BRICK, width=2)
        draw.ellipse([x - 3, ly - 12, x + 3, ly - 6], fill=BRICK)
        tw = draw.textlength(label, font=f_ev)
        lx = min(max(x - tw / 2, lx0), lx1 - tw)
        draw_text(draw, (lx, y + 1), label, f_ev, BRICK_DK)
    # end mark: the day ends at 24:00
    draw_text(draw, (lx1 - 62, y + 1), "DAY ENDS", F_SANS_B(8), INK)
    return y + h

def draw_lead_hero(draw, box):
    """Lead #1: big hero, illustration on top, headline + deck below."""
    num, title, place, region, field, status, big, deck, kind = LEADS[0]
    x0, y0, x1, y1 = box
    rounded_rect(draw, [x0, y0, x1, y1], 4, fill=WHITE, outline=GREY_LT,
                 width=1)
    # illustration: night sky, top 150 px
    ill_h = 150
    scene_drones(draw, [x0 + 1, y0 + 1, x1 - 1, y0 + ill_h], big, hero=True)
    # number badge + status chip over the illustration's bottom edge
    number_badge(draw, x0 + 10, y0 + ill_h - 10, num, region, size=22)
    status_chip(draw, x0 + 40, y0 + ill_h - 8, status)
    # place/field label, fully inside the illustration: the old y
    # (ill_h-8) put the lower half of the text below the illustration
    # edge, on the white card, so white-on-white cut it in half
    draw_text(draw, (x1 - 118, y0 + ill_h - 18),
              "%s · %s" % (place, field), F_SANS_B(10), WHITE)
    # headline + deck
    ty = y0 + ill_h + 14
    f_t, _ = fit_size(draw, title, "DejaVuSans-Bold.ttf", 27, x1 - x0 - 20)
    draw_text(draw, (x0 + 10, ty), title, f_t, INK)
    f_d = F_SANS(13)
    for i, line in enumerate(wrap(draw, deck, f_d, x1 - x0 - 20)):
        draw_text(draw, (x0 + 10, ty + 34 + i * 17), line, f_d, (50, 48, 44))
    return


def draw_lead_stack(draw, box, lead):
    """Leads #2/#3: illustration left, text right."""
    num, title, place, region, field, status, big, deck, kind = lead
    x0, y0, x1, y1 = box
    rounded_rect(draw, [x0, y0, x1, y1], 4, fill=WHITE, outline=GREY_LT,
                 width=1)
    ill_w = 132
    SCENES[kind](draw, [x0 + 1, y0 + 1, x0 + ill_w, y1 - 1], big)
    tx = x0 + ill_w + 10
    tw = x1 - tx - 10
    number_badge(draw, tx, y0 + 8, num, region, size=20)
    status_chip(draw, tx + 26, y0 + 10, status)
    draw_text(draw, (tx, y0 + 32), "%s · %s" % (place, field),
              F_SANS_B(10), GREY)
    f_t, _ = fit_size(draw, title, "DejaVuSans-Bold.ttf", 18, tw)
    draw_text(draw, (tx, y0 + 48), title, f_t, INK)
    f_d = F_SANS(11)
    lines = wrap(draw, deck, f_d, tw)
    for i, line in enumerate(lines[:3]):
        draw_text(draw, (tx, y0 + 72 + i * 14), line, f_d, (50, 48, 44))
    return


def draw_medium_card(draw, box, card, tint):
    """One medium card: illustration top, title, one-line summary, labels."""
    num, title, place, region, field, status, big, summ, kind = card
    x0, y0, x1, y1 = box
    rounded_rect(draw, [x0, y0, x1, y1], 4, fill=tint, outline=GREY_LT,
                 width=1)
    ill_h = 44
    SCENES[kind](draw, [x0 + 1, y0 + 1, x1 - 1, y0 + ill_h], big)
    number_badge(draw, x0 + 6, y0 + ill_h - 22, num, region, size=18)
    # title (2 lines max) + summary (1 line, trimmed) + place/field
    ty = y0 + ill_h + 6
    f_t = F_SANS_B(13)
    lines = wrap(draw, title, f_t, x1 - x0 - 12)
    for i, line in enumerate(lines[:2]):
        draw_text(draw, (x0 + 6, ty + i * 16), line, f_t, INK)
    sy = ty + min(len(lines), 2) * 16 + 2
    f_s = F_SANS(10)
    slines = wrap(draw, summ, f_s, x1 - x0 - 12)
    if slines and sy + 10 <= y1 - 12:
        draw_text(draw, (x0 + 6, sy), slines[0], f_s, (60, 58, 54))
    # bottom label row: place + field; REPORTED rides along as text
    # (a chip here would collide with the label on narrow cards, and the
    # full "place · field · REPORTED" overflows the card, so a REPORTED
    # card shows place + REPORTED only)
    if status == "REPORTED":
        lab = "%s · REPORTED" % place
    else:
        lab = "%s · %s" % (place, field)
    draw_text(draw, (x0 + 6, y1 - 13), lab, F_SANS_B(9), REGION[region])
    return


def draw_legend_box(draw, box):
    """The 12th grid slot: how to read the page (content, not decoration)."""
    x0, y0, x1, y1 = box
    rounded_rect(draw, [x0, y0, x1, y1], 4, fill=NAVY)
    draw_text(draw, (x0 + 8, y0 + 8), "HOW TO READ", F_SANS_B(11), GOLD)
    f = F_SANS(10)
    lines = [
        "Numbers point at stories:",
        "card = pin = list number.",
        "Dark ribbon = the day's",
        "six biggest figures.",
    ]
    for i, line in enumerate(lines):
        draw_text(draw, (x0 + 8, y0 + 26 + i * 13), line, f, WHITE)
    draw_text(draw, (x0 + 8, y1 - 28), "REPORTED = claimed,",
              F_SANS_B(8), (200, 205, 215))
    draw_text(draw, (x0 + 8, y1 - 17), "not confirmed.",
              F_SANS_B(8), (200, 205, 215))


def draw_list(draw, box):
    """ALSO ON SUNDAY: 27 numbered briefs in two columns."""
    x0, y0, x1, y1 = box
    draw_text(draw, (x0, y0), "ALSO ON SUNDAY — 27 MORE STORIES",
              F_SANS_B(13), INK)
    draw.line([x0, y0 + 18, x1, y0 + 18], fill=INK, width=1)
    col_w = (x1 - x0 - 16) // 2
    row_h = (y1 - (y0 + 24)) / 14.0
    f_num = F_SANS_B(10)
    f_city = F_SANS_B(10)
    f_txt = F_SANS(10)
    for i, (num, city, text, region, status) in enumerate(BRIEFS):
        col = 0 if i < 14 else 1
        row = i if i < 14 else i - 14
        bx = x0 + col * (col_w + 16)
        by = y0 + 24 + row * row_h
        # number in region colour
        tw = draw.textlength(str(num), font=f_num)
        rounded_rect(draw, [bx, by, bx + 18, by + 13], 2, fill=REGION[region])
        draw_text(draw, (bx + (18 - tw) / 2, by + 1), str(num), f_num, WHITE)
        # city in red bold + text; trim text to fit
        cx = bx + 22
        draw_text(draw, (cx, by + 1), city, f_city, BRICK_DK)
        cw = draw.textlength(city + " ", font=f_city)
        avail = col_w - 22 - cw - 4
        t = text
        while draw.textlength(t, font=f_txt) > avail and len(t) > 8:
            t = t[:-4] + "…"
        draw_text(draw, (cx + cw, by + 1), t, f_txt, INK)
    return


def draw_footer(draw, y):
    """DATE CHECK box + NOT SHOWN + sources line."""
    h = 66
    draw.line([MARGIN, y, W - MARGIN, y], fill=INK, width=2)
    f = F_SANS(11)
    lines = wrap(draw, DATE_CHECK, f, CONTENT_W - 8)
    for i, line in enumerate(lines[:2]):
        draw_text(draw, (MARGIN + 4, y + 6 + i * 14), line, f, INK)
    draw_text(draw, (MARGIN + 4, y + 36), NOT_SHOWN, F_SANS_B(10), GREY)
    draw_text(draw, (MARGIN + 4, y + 52),
              "SOURCES: REUTERS · AP · AFP · AL JAZEERA · BBC · CNN · THE GUARDIAN · "
              "UKRAINIAN AIR FORCE · ESA · MOTOGP.COM · PREMIER LEAGUE · INFO.GOV.HK",
              F_SANS(8), GREY)
    # legend
    lx = W - MARGIN - 210
    draw_text(draw, (lx, y + 52), "● CONFIRMED   ● REPORTED",
              F_SANS_B(8), GREY)
    return y + h


# ---------------------------------------------------------------- main
def build():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # --- contrast assertions (Set A floor 4.5:1) ---
    pairs = [("WHITE on region", WHITE, REGION["EU"]),
             ("WHITE on region", WHITE, REGION["ME"]),
             ("WHITE on region", WHITE, REGION["AM"]),
             ("WHITE on region", WHITE, REGION["AS"]),
             ("WHITE on region", WHITE, REGION["AF"]),
             ("WHITE on region", WHITE, REGION["OC"]),
             ("WHITE on region", WHITE, REGION["WORLD"]),
             ("INK on PAPER", INK, PAPER),
             ("BRICK on PAPER", BRICK, PAPER),
             ("WHITE on NAVY", WHITE, NAVY),
             ("GOLD on NAVY", GOLD, NAVY),
             ("BRICK_DK on PAPER", BRICK_DK, PAPER),
             ("GREY on PAPER", GREY, PAPER)]
    for name, fg, bg in pairs:
        c = contrast(fg, bg)
        assert c >= 4.5, "%s contrast %.2f < 4.5" % (name, c)

    y = draw_masthead(draw)
    y = draw_ribbon(draw, y + 8)
    y = draw_utc_strip(draw, y + 8)

    # --- leads: hero + two stacked ---
    ly0 = y + 8
    lead_h = 250
    draw_lead_hero(draw, [MARGIN, ly0, MARGIN + 612, ly0 + lead_h])
    rx0 = MARGIN + 612 + GAP
    stack_h = (lead_h - GAP) // 2
    draw_lead_stack(draw, [rx0, ly0, W - MARGIN, ly0 + stack_h], LEADS[1])
    draw_lead_stack(draw, [rx0, ly0 + stack_h + GAP, W - MARGIN,
                           ly0 + lead_h], LEADS[2])
    y = ly0 + lead_h

    # --- medium grid: 6 columns x 2 rows (11 cards + legend box) ---
    gy0 = y + 10
    cols = 6
    card_w = (CONTENT_W - (cols - 1) * GAP) // cols
    rows = 2
    card_h = 112
    grid_h = rows * card_h + (rows - 1) * GAP
    for i, card in enumerate(MEDIUM):
        r, c = divmod(i, cols)
        x0 = MARGIN + c * (card_w + GAP)
        y0 = gy0 + r * (card_h + GAP)
        tint = CARD_TINTS[(r + c) % len(CARD_TINTS)]
        draw_medium_card(draw, [x0, y0, x0 + card_w, y0 + card_h], card,
                         tint)
    # 12th slot: legend box
    lx0 = MARGIN + 5 * (card_w + GAP)
    ly1 = gy0 + 1 * (card_h + GAP)
    draw_legend_box(draw, [lx0, ly1, lx0 + card_w, ly1 + card_h])
    y = gy0 + grid_h

    # --- map + list ---
    my0 = y + 10
    map_h = 198
    map_w = 300
    draw_text(draw, (MARGIN, my0), "WHERE IT HAPPENED", F_SANS_B(13), INK)
    draw_map(draw, [MARGIN, my0 + 20, MARGIN + map_w, my0 + map_h])
    draw_pins(draw, [MARGIN, my0 + 20, MARGIN + map_w, my0 + map_h])
    draw_list(draw, [MARGIN + map_w + 16, my0,
                     W - MARGIN, my0 + map_h])
    y = my0 + map_h

    # --- footer ---
    draw_footer(draw, y + 8)
    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    img = build()
    assert img.size == (1024, 1024), img.size
    img.save(out, format="PNG", compress_level=9, optimize=True)
    data = open(out, "rb").read()
    print("wrote %s %d bytes sha256=%s" % (
        out, len(data), hashlib.sha256(data).hexdigest()))
    assert len(data) <= 1048576, "over 1 MiB: %d" % len(data)
    # fixed file mode for the grader (G15)
    os.chmod(out, 0o644)


if __name__ == "__main__":
    main()
