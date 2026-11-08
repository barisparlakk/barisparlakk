"""Builds the SVG images used in the profile README.

Run from the repo root:  python3 scripts/build_assets.py

The look follows barisparlak.com: near-black panels, one red accent,
Geist and Geist Mono, and "VIEW 0x" panels like the ones on the site.
Fonts are embedded as small subsets because GitHub serves README images
without web fonts.
"""

import base64
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

BG = "#0a0b0c"
PANEL = "#101214"
RULE = "#1f2327"
CELL = "#2a2f34"
INK = "#e7e8e9"
SOFT = "#a9aeb3"
MUTED = "#878d93"
ACCENT = "#ff4438"

FONT_FILES = {
    "sans": ("geist-400-subset.woff2", 400),
    "bold": ("geist-700-subset.woff2", 700),
    "mono": ("geist-mono-400-subset.woff2", 400),
    "monob": ("geist-mono-500-subset.woff2", 500),
}
FAMILY = {
    "sans": "S4,Geist,system-ui,sans-serif",
    "bold": "S7,Geist,system-ui,sans-serif",
    "mono": "M4,'Geist Mono',ui-monospace,monospace",
    "monob": "M5,'Geist Mono',ui-monospace,monospace",
}
ALIAS = {"sans": "S4", "bold": "S7", "mono": "M4", "monob": "M5"}


def load_metrics(file):
    font = TTFont(ASSETS / "fonts" / file)
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    return {chr(c): hmtx[g][0] / upm for c, g in cmap.items()}


METRICS = {key: load_metrics(file) for key, (file, _) in FONT_FILES.items()}


def text_width(s, size, font="sans"):
    return sum(METRICS[font].get(ch, 0.6) for ch in s) * size


def wrap(s, size, font, max_width):
    lines, line = [], ""
    for word in s.split(" "):
        trial = f"{line} {word}".strip()
        if line and text_width(trial, size, font) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def font_css(fonts):
    css = ""
    for key in fonts:
        file, weight = FONT_FILES[key]
        data = base64.b64encode((ASSETS / "fonts" / file).read_bytes()).decode()
        css += (f"@font-face{{font-family:{ALIAS[key]};font-weight:{weight};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")
        css += f".{key}{{font-family:{FAMILY[key]};font-weight:{weight}}}"
    return css


def svg(w, h, body, css="", title="", fonts=("sans", "bold", "mono", "monob")):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" role="img">'
        f"<title>{escape(title)}</title><style>{font_css(fonts)}{css}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>"
        f"{body}</svg>\n"
    )


def text(x, y, s, size, font="sans", fill=INK, anchor="start", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{font}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def label(x, y, s, size=11):
    """Red detection label with its bottom-left corner at (x, y)."""
    w, h = text_width(s, size, "monob") + 10, size + 6
    return (f'<rect x="{x:.1f}" y="{y - h:.1f}" width="{w:.1f}" height="{h}" fill="{ACCENT}"/>'
            + text(x + 5, y - 4.5, s, size, "monob", INK))


def frame(w, h, inner, rx=10):
    return (f'<defs><clipPath id="frame"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath></defs>'
            f'<g clip-path="url(#frame)"><rect width="{w}" height="{h}" fill="{BG}"/>{inner}</g>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" stroke="{RULE}"/>')


def write(name, content):
    path = ASSETS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---------------------------------------------------------------- header

def cuboid(x, y, w, h, vp, depth, rng, points=160):
    """Wireframe box whose back face recedes toward the vanishing point."""
    dx = (vp[0] - (x + w / 2)) * depth
    dy = (vp[1] - (y + h / 2)) * depth
    front = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    back = [(px + dx, py + dy) for px, py in front]
    edges = "".join(f"M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" for a, b in zip(front, back))
    poly = lambda pts: "M" + "L".join(f"{px:.1f} {py:.1f}" for px, py in pts) + "Z"
    cloud = ""
    for _ in range(points):
        t = rng.random()
        px = x + rng.random() * w + dx * t
        py = y + rng.random() * h + dy * t
        cloud += f'<circle cx="{px:.1f}" cy="{py:.1f}" r=".9"/>'
    return (f'<g fill="{INK}" fill-opacity=".45" class="pc">{cloud}</g>'
            f'<path d="{poly(back)}{edges}" stroke="{ACCENT}" stroke-opacity=".7" stroke-width="1.3"/>'
            f'<path d="{poly(front)}" stroke="{ACCENT}" stroke-width="1.8"/>'), (min(x, x + dx), min(y, y + dy))


def header():
    w, h = 1200, 480
    vp = (800, 30)
    rng = random.Random(7)
    floor = ""
    for bx in (-600, -150, 250, 560, 1040, 1350, 1750):
        floor += f'<path class="ray" d="M{bx} {h + 40}L{vp[0]} {vp[1]}" stroke="{SOFT}" stroke-opacity=".55" stroke-width="1.3"/>'
    for i, r in enumerate(range(140, 1700, 120)):
        floor += (f'<ellipse class="ring" cx="{vp[0]}" cy="{h + 60}" rx="{r}" ry="{r * 0.3:.0f}" '
                  f'stroke="{SOFT}" stroke-opacity="{0.6 - i * 0.03:.3f}" stroke-width="1.3"/>')
    tracks = ""
    for x, y, bw, bh, depth, name in [
        (520, 150, 130, 90, 0.16, "car 0.92  #03"),
        (760, 128, 86, 60, 0.14, "car 0.93  #07"),
        (930, 92, 62, 46, 0.12, "van 0.90  #12"),
    ]:
        shape, (lx, ly) = cuboid(x, y, bw, bh, vp, depth, rng)
        tracks += f'<g class="trk">{shape}{label(lx - 0.9, ly - 1, name)}</g>'
    person, (px, py) = cuboid(1046, 84, 18, 36, vp, 0.1, rng, 50)
    tracks += f'<g class="ped">{person}{label(px - 0.9, py - 1, "person 0.87  #21")}</g>'

    frames = "".join(
        f'<g class="fr" style="animation-delay:{i * 0.1:.1f}s">{text(56, 78, f"frame {4900 + i:06d} · 10 Hz", 13, "mono", SOFT)}</g>'
        for i in range(10)
    )
    css = """
.ring{stroke-dasharray:1.4 8;stroke-linecap:round;animation:ring 2.4s linear infinite}
@keyframes ring{to{stroke-dashoffset:-37.6}}
.ray{stroke-dasharray:1.4 9;stroke-linecap:round;animation:ray 1.6s linear infinite}
@keyframes ray{to{stroke-dashoffset:20.8}}
.trk{animation:trk 1.8s steps(1) infinite}
@keyframes trk{0%{transform:translate(0,0)}33%{transform:translate(1.5px,-1px)}66%{transform:translate(-1px,1px)}}
.ped,.t4{opacity:0;animation:ped 6s steps(1) infinite}.t3{animation:t3 6s steps(1) infinite}
@keyframes ped{0%{opacity:0}45%{opacity:1}85%{opacity:0}}
@keyframes t3{0%{opacity:1}45%{opacity:0}85%{opacity:1}}
.fr{opacity:0;animation:fr 1s steps(1) infinite}
@keyframes fr{0%{opacity:1}10%{opacity:0}}
.blink{animation:blink 1.2s steps(1) infinite}@keyframes blink{50%{opacity:.2}}
"""
    tagline = ["I build perception, planning and language systems: a self-driving stack for",
               "Turkish traffic, a skin lesion detector, and a Turkish RAG pipeline that never leaves the machine."]
    body = frame(w, h, f"""
<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
<stop offset=".45" stop-color="{BG}" stop-opacity="0"/><stop offset=".68" stop-color="{BG}" stop-opacity=".92"/></linearGradient></defs>
{floor}
{tracks}
<rect width="{w}" height="{h}" fill="url(#fade)"/>
<circle class="blink" cx="60" cy="52" r="3.5" fill="{ACCENT}"/>
{text(72, 56.5, "seyir / lidar_top", 13, "mono", SOFT)}
{frames}
<g class="t3">{text(56, 100, "tracks 3", 13, "mono", SOFT)}</g>
<g class="t4">{text(56, 100, "tracks 4", 13, "mono", SOFT)}</g>
<rect x="56" y="321" width="9" height="9" fill="{ACCENT}"/>
{text(76, 330, "AI developer · computer engineering student · Istanbul", 14, "mono", MUTED)}
{text(52, 404, "Barış Parlak", 88, "bold", INK, extra='letter-spacing="-3.5"')}
{text(56, 436, tagline[0], 17, "sans", SOFT)}
{text(56, 459, tagline[1], 17, "sans", SOFT)}
{text(w - 48, 459, "barisparlak.com ↗", 14, "mono", MUTED, "end")}
""", 14)
    return svg(w, h, body, css, "Barış Parlak: AI developer and computer engineering student in Istanbul")


# ---------------------------------------------------------------- cards

CARD_W, CARD_H = 600, 380
BAR_H, PANEL_TOP, PANEL_H = 36, 36, 168


def card(slug, view, path, status, title, subtitle, lines, tags, panel, css=""):
    tag_x, tags_svg = 28, ""
    for t in tags:
        tw = text_width(t, 11.5, "mono") + 20
        tags_svg += (f'<rect x="{tag_x:.1f}" y="{CARD_H - 44}" width="{tw:.1f}" height="24" rx="3" stroke="{RULE}" fill="{PANEL}"/>'
                     + text(tag_x + 10, CARD_H - 28, t, 11.5, "mono", SOFT))
        tag_x += tw + 6
    desc = "".join(text(28, 306 + i * 22, line, 15, "sans", SOFT) for i, line in enumerate(lines))
    status_w = text_width(status, 11.5, "mono")
    inner = f"""
<rect y="{PANEL_TOP}" width="{CARD_W}" height="{PANEL_H}" fill="{PANEL}"/>
<svg x="0" y="{PANEL_TOP}" width="{CARD_W}" height="{PANEL_H}" viewBox="0 0 {CARD_W} {PANEL_H}" overflow="hidden">{panel}</svg>
{text(20, 23, view, 11.5, "monob", INK)}
{text(20 + text_width(view + " ", 11.5, "monob"), 23, "· " + path, 11.5, "mono", MUTED)}
<circle class="blink" cx="{CARD_W - 28 - status_w:.1f}" cy="19" r="3" fill="{ACCENT}"/>
{text(CARD_W - 20, 23, status, 11.5, "mono", MUTED, "end")}
<path d="M0 {BAR_H}.5H{CARD_W}M0 {PANEL_TOP + PANEL_H}.5H{CARD_W}" stroke="{RULE}"/>
{text(28, 250, title, 28, "bold", INK, extra='letter-spacing="-.6"')}
{text(28, 274, subtitle, 12, "mono", MUTED)}
<path d="M{CARD_W - 44} 244L{CARD_W - 30} 230M{CARD_W - 41} 230H{CARD_W - 30}V241" stroke="{MUTED}" stroke-width="1.6"/>
{desc}
{tags_svg}
"""
    css += ".blink{animation:blink 1.2s steps(1) infinite}@keyframes blink{50%{opacity:.2}}"
    write(f"cards/{slug}-view.svg",
          svg(CARD_W, CARD_H, frame(CARD_W, CARD_H, inner), css, f"{title}: {' '.join(lines)}"))


def halftone(width, height, blobs, spacing=7, gain=2.9, base=0.35):
    out = []
    for row, y in enumerate(range(4, height, spacing)):
        offset = spacing / 2 if row % 2 else 0
        for x in range(4, width + spacing, spacing):
            cx = x + offset
            v = sum(a * math.exp(-(((cx - bx) / sx) ** 2 + ((y - by) / sy) ** 2)) for bx, by, sx, sy, a in blobs)
            r = base + gain * min(v, 1)
            if r > 0.45:
                out.append(f'<circle cx="{cx:.0f}" cy="{y}" r="{r:.1f}"/>')
    return "".join(out)


def seyir():
    cell, cols, rows = 12, 50, 14
    rng = random.Random(3)
    top = [2, 2, 3, 3, 2, 1, 1, 2, 2, 3, 3, 3, 2, 2, 1]
    bottom = [3, 3, 2, 2, 2, 3, 3, 3, 2, 1, 1, 2, 2, 3, 3]
    grid = ""
    for c in range(cols):
        t = top[c * len(top) // cols]
        b = bottom[c * len(bottom) // cols]
        for r in range(rows):
            filled = r < t or r >= rows - b
            fill = CELL if filled else "#14171a"
            if filled and rng.random() < 0.15:
                fill = "#3a4046"
            grid += f'<rect x="{c * cell}" y="{r * cell}" width="{cell - 1}" height="{cell - 1}" fill="{fill}"/>'
    mid = rows * cell / 2
    obstacles = [(150, mid - 26, 34, 16), (290, mid + 8, 34, 16), (450, mid - 22, 34, 16)]
    obs = "".join(f'<rect x="{x - 5}" y="{y - 5}" width="{w + 10}" height="{h + 10}" fill="{CELL}"/>'
                  f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{INK}"/>' for x, y, w, h in obstacles)
    route = f"M70 {mid}C120 {mid} 130 {mid + 14} 200 {mid + 14}S260 {mid - 24} 340 {mid - 24}S410 {mid + 16} 490 {mid + 16}S560 {mid} 620 {mid}"
    horizon = [(70 + i * 11, mid + 14 * (1 - math.cos(min(i / 9, 1) * math.pi)) / 2) for i in range(10)]
    dots = "".join(f'<circle class="hz" style="animation-delay:{i * 0.08:.2f}s" cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="{ACCENT}"/>'
                   for i, (x, y) in enumerate(horizon))
    hpath = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in horizon)
    panel = f"""
<g transform="translate(0 2)">{grid}</g>
<path d="M0 {mid + 2}H600" stroke="{MUTED}" stroke-opacity=".5" stroke-dasharray="8 8"/>
{obs}
<path class="route" d="{route}" stroke="{SOFT}" stroke-opacity=".8" stroke-width="1.4"/>
<path d="{hpath}" stroke="{ACCENT}" stroke-width="2"/>
{dots}
<rect x="30" y="{mid - 7}" width="30" height="16" stroke="{ACCENT}" stroke-width="2"/>
{text(30, mid - 13, "ego", 11, "monob", ACCENT)}
<rect x="8" y="{PANEL_H - 24}" width="232" height="18" fill="{PANEL}" fill-opacity=".9"/>
{text(14, PANEL_H - 11, "100 × 100 occupancy · A* route · MPC horizon 14", 10, "mono", MUTED)}
"""
    css = (".route{stroke-dasharray:3 5;animation:route 1.2s linear infinite}@keyframes route{to{stroke-dashoffset:-16}}"
           ".hz{animation:hz 1.4s ease-in-out infinite}@keyframes hz{50%{opacity:.35}}")
    card("seyir", "VIEW 01", "seyir/occupancy_grid", "live", "Seyir", "01 · Autonomous driving",
         ["An autonomous driving stack for Turkish traffic, built from",
          "scratch in CARLA: perception, prediction, A*/PPO and MPC."],
         ["CARLA 0.9.15", "YOLOv11n", "SocialTransformer", "MPC ≤ 50 ms"], panel, css)


def deepderm():
    blobs = [(90, 50, 70, 40, .7), (250, 110, 90, 45, .8), (420, 40, 80, 35, .6), (540, 130, 70, 50, .7),
             (330, 20, 60, 25, .4), (160, 150, 60, 30, .5)]
    dots = halftone(CARD_W, PANEL_H, blobs, spacing=7, gain=3.1, base=0.3)
    panel = f"""
<g fill="{INK}" fill-opacity=".8">{dots}</g>
<g class="hit"><rect x="226" y="88" width="44" height="40" stroke="{ACCENT}" stroke-width="1.8"/>{label(225.1, 88, "lesion 0.88")}</g>
<g class="scan"><rect width="{CARD_W}" height="14" fill="{ACCENT}" fill-opacity=".12"/><rect y="13" width="{CARD_W}" height="1.6" fill="{ACCENT}"/></g>
<rect x="8" y="{PANEL_H - 24}" width="128" height="18" fill="{PANEL}" fill-opacity=".92"/>
{text(14, PANEL_H - 11, "scanning… 1 found", 10.5, "mono", SOFT)}
"""
    css = (".scan{animation:scan 3s linear infinite}@keyframes scan{from{transform:translateY(-16px)}to{transform:translateY(170px)}}"
           ".hit{animation:hit 3s steps(1) infinite}@keyframes hit{0%{opacity:0}62%{opacity:1}}")
    card("deepderm", "VIEW 02", "deepderm/inference", "live", "DeepDerm", "02 · Medical computer vision",
         ["Real-time acne detection and remote treatment tracking:",
          "YOLOv11 lesion grading, a doctor panel and a patient app."],
         ["YOLOv11", "Hayashi scale", "Spring Boot", "React Native"], panel, css)


def turkrag():
    cols = [("BM25 · WORDS", ["Saklama politikası §4", "KVKK madde 7", "Aydınlatma metni"]),
            ("FAISS · MEANING", ["KVKK madde 7", "Veri envanteri rehberi", "Saklama politikası §4"]),
            ("FUSED → LOCAL LLM", ["KVKK madde 7", "Saklama politikası §4", "Veri envanteri rehberi"])]
    x0, col_w, gap, row_y, row_h = 20, 176, 16, 50, 26
    out, pos = "", {}
    for ci, (head, docs) in enumerate(cols):
        x = x0 + ci * (col_w + gap)
        out += text(x, 40, head, 10, "mono", MUTED, extra='letter-spacing=".8"')
        for ri, d in enumerate(docs):
            y = row_y + ri * row_h
            pos[(ci, d)] = (x, y)
            hl = d == "KVKK madde 7"
            out += (f'<rect x="{x}" y="{y}" width="{col_w}" height="21" rx="2" fill="#16191c" '
                    f'stroke="{ACCENT if hl else RULE}"/>'
                    + text(x + 8, y + 14.5, str(ri + 1), 10.5, "mono", MUTED)
                    + text(x + 22, y + 14.5, d, 11.5, "sans", INK if hl else SOFT))
    links = ""
    for src, dst in ((0, 1), (1, 2)):
        x1, y1 = pos[(src, "KVKK madde 7")]
        x2, y2 = pos[(dst, "KVKK madde 7")]
        x1, y1, y2 = x1 + col_w, y1 + 10.5, y2 + 10.5
        mx = (x1 + x2) / 2
        links += (f'<path class="flow" d="M{x1} {y1}C{mx} {y1} {mx} {y2} {x2} {y2}" '
                  f'stroke="{ACCENT}" stroke-width="1.4"/>')
    panel = f"""
{text(20, 20, "query  KVKK'ya göre kişisel veriler ne kadar süre saklanabilir?", 10.5, "mono", SOFT)}
{links}
{out}
{text(20, PANEL_H - 10, "reciprocal rank fusion · generation via Ollama, offline", 10, "mono", MUTED)}
"""
    css = ".flow{stroke-dasharray:3 4;animation:flow 1s linear infinite}@keyframes flow{to{stroke-dashoffset:-14}}"
    card("turkrag", "VIEW 03", "turkrag/retrieval", "top-k = 3", "TurkRAG", "03 · Language systems",
         ["Question answering over Turkish documents with no cloud",
          "dependency, so sensitive files stay on your own hardware."],
         ["BM25 + FAISS", "Ollama", "LangChain", "FastAPI"], panel, css)


def thermground():
    blobs = [(130, 92, 9, 20, 1), (166, 108, 9, 19, 1), (420, 48, 40, 14, .9), (300, 150, 220, 18, .25),
             (60, 30, 80, 30, .15)]
    dots = halftone(CARD_W, PANEL_H, blobs, spacing=6, gain=2.3, base=0.55)
    panel = f"""
<g fill="{INK}" fill-opacity=".7">{dots}</g>
<g class="box"><rect x="110" y="62" width="76" height="72" stroke="{ACCENT}" stroke-width="1.8"/>{label(109.1, 62, "person ×2")}</g>
<rect x="318" y="92" width="262" height="58" rx="3" fill="{BG}" fill-opacity=".92" stroke="{RULE}"/>
{text(332, 115, "Q", 12, "monob", MUTED)}{text(350, 115, "how many people by the river?", 12, "mono", INK)}
{text(332, 137, "A", 12, "monob", ACCENT)}{text(350, 137, "two, both on the left bank", 12, "mono", SOFT)}
"""
    css = ".box{animation:box 3.2s steps(1) infinite}@keyframes box{0%{opacity:0}30%{opacity:1}}"
    card("thermground", "VIEW 04", "thermground/thermal_vqa", "building", "thermground", "04 · Vision-language",
         ["A small VLM that answers questions about thermal drone images",
          "for night search-and-rescue, grounded in what it sees."],
         ["VLM", "thermal UAV", "PyTorch"], panel, css)


def skyguard():
    road = "#1a1d21"
    cars = [(40, 74, 0), (76, 92, 0), (128, 74, 0), (236, 92, 0), (282, 74, 0), (198, 30, 1), (182, 140, 1), (198, 118, 1)]
    objs = ""
    for i, (x, y, vertical) in enumerate(cars):
        w, h = (8, 15) if vertical else (15, 8)
        objs += (f'<g class="f" style="animation-delay:{-i * 0.31:.2f}s"><rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="1.5" fill="{SOFT}"/>'
                 f'<rect x="{x - w / 2 - 3.5}" y="{y - h / 2 - 3.5}" width="{w + 7}" height="{h + 7}" stroke="{ACCENT}" stroke-width="1.2"/></g>')
    steps = [("pytorch", "fp32"), ("onnx", "opset 17"), ("tensorrt", "fp16 / int8")]
    pipe = ""
    for i, (name, detail) in enumerate(steps):
        y = 26 + i * 46
        last = i == len(steps) - 1
        width = text_width(f"{name}  {detail}", 12, "mono") + 26
        pipe += (f'<rect x="364" y="{y}" width="{width:.1f}" height="28" rx="3" fill="{ACCENT if last else BG}" stroke="{ACCENT if last else RULE}"/>'
                 + text(377, y + 18.5, name, 12, "monob", INK) + text(377 + text_width(name + "  ", 12, "monob"), y + 18.5, detail, 12, "mono", INK if last else MUTED))
        if not last:
            pipe += f'<path d="M378 {y + 29}V{y + 45}" stroke="{MUTED}" stroke-dasharray="2 3"/>'
    panel = f"""
<rect x="0" y="62" width="330" height="42" fill="{road}"/>
<rect x="176" y="0" width="42" height="{PANEL_H}" fill="{road}"/>
<path d="M0 83H176M218 83H330M197 0V62M197 104V{PANEL_H}" stroke="{MUTED}" stroke-opacity=".5" stroke-dasharray="6 6"/>
{objs}
<path d="M330.5 0V{PANEL_H}" stroke="{RULE}"/>
{pipe}
"""
    css = ".f{animation:f 2.4s steps(1) infinite}@keyframes f{0%{opacity:1}88%{opacity:.3}}"
    card("skyguard", "VIEW 05", "skyguard/edge_engine", "L4", "Skyguard", "05 · Edge vision",
         ["Aerial object detection with YOLOv8m on VisDrone, exported",
          "through ONNX to TensorRT and benchmarked on an NVIDIA L4."],
         ["YOLOv8m", "ONNX", "TensorRT", "VisDrone"], panel, css)


def notary():
    blocks = ""
    for i in range(4):
        x = 316 + i * 62
        last = i == 3
        blocks += (f'<rect class="blk" style="animation-delay:{i * 0.4:.1f}s" x="{x}" y="58" width="44" height="44" rx="3" '
                   f'fill="{ACCENT if last else "#16191c"}" stroke="{ACCENT if last else RULE}"/>')
        if not last:
            blocks += f'<path d="M{x + 44} 80H{x + 62}" stroke="{MUTED}"/>'
    hash_w = text_width("sha256 3f9a…e1c2", 11.5, "mono") + 22
    panel = f"""
<path d="M40 44H78L94 60V116H40Z" fill="{INK}"/>
<path d="M78 44V60H94" fill="{SOFT}"/>
<path d="M50 72H82M50 84H84M50 96H76M50 108H80" stroke="{CELL}" stroke-width="3"/>
<path class="flow" d="M104 80H128" stroke="{MUTED}"/>
<rect x="134" y="66" width="{hash_w:.1f}" height="28" rx="14" stroke="{RULE}" fill="#16191c"/>
{text(145, 84.5, "sha256 3f9a…e1c2", 11.5, "mono", INK)}
<path class="flow" d="M{134 + hash_w + 6:.1f} 80H310" stroke="{MUTED}"/>
{blocks}
<path d="M514 81L520 87L531 75" stroke="{INK}" stroke-width="2.4"/>
{text(524, 122, "VERIFIED", 11, "monob", ACCENT, "middle")}
{text(316, 146, 'PDA ["proof", signer, hash]', 11, "mono", MUTED)}
"""
    css = (".flow{stroke-dasharray:3 3;animation:flow .8s linear infinite}@keyframes flow{to{stroke-dashoffset:-12}}"
           ".blk{animation:blk 1.6s ease-in-out infinite}@keyframes blk{50%{opacity:.6}}")
    card("notary", "VIEW 06", "notary/proof", "devnet", "Notary", "06 · On-chain proof",
         ["Verifiable document proofs for people and AI agents on Solana.",
          "Anyone can check a proof on-chain, even if the API is down."],
         ["Solana", "Anchor", "Python", "React"], panel, css)


# ---------------------------------------------------------------- sections

def section(number, name):
    w, h = 1200, 44
    name_x = 20 + text_width(number + "  ", 13, "monob")
    line_x = name_x + text_width(name, 13, "mono") + 20
    body = (f'<rect width="{w}" height="{h}" fill="{BG}" rx="6"/>'
            + text(20, 27, number, 13, "monob", ACCENT)
            + text(name_x, 27, name, 13, "mono", INK, extra='letter-spacing="1.5"')
            + f'<path d="M{line_x + 12:.1f} 22.5H{w - 20}" stroke="{RULE}"/>')
    write(f"section-{name.lower()}.svg", svg(w, h, body, title=f"{number} {name}", fonts=("mono", "monob")))


def experience():
    w = 1200
    roles = [
        ("Apr – May 2026", "AI developer · Caladrius",
         "LoRA fine-tuning pipeline for MedGemma 27B that classifies oral epithelial dysplasia with structured WHO 2022 findings."),
        ("Feb – Oct 2025", "Machine learning developer · Unidev Software Turkey",
         "Geospatial analysis with Folium, the MyUni MySQL database behind Django REST APIs, and a recommender that raised engagement by 40%."),
        ("2024 – 2025", "Computer Society chair · IEEE İnönü Student Branch",
         "Formed cross-disciplinary project teams and ran regular algorithm workshops."),
    ]
    schools = [
        ("2024 – now", "Computer Engineering", "İnönü University"),
        ("2025 – 2026", "Computer Science", "Military University of Technology, Warsaw (Erasmus+)"),
        ("2022 – 2024", "Computer Engineering", "Malatya Turgut Özal University"),
    ]
    left_text, left_w = 176, 520
    right_x, right_text = 760, 870
    out = text(32, 44, "EXPERIENCE", 11, "mono", MUTED, extra='letter-spacing="1.5"')
    out += text(right_x, 44, "EDUCATION", 11, "mono", MUTED, extra='letter-spacing="1.5"')
    y = 62
    for date, role, desc in roles:
        out += f'<path d="M32 {y}.5H{right_x - 40}" stroke="{RULE}"/>'
        out += text(32, y + 28, date, 12.5, "mono", MUTED)
        out += text(left_text, y + 28, role, 16, "bold", INK)
        lines = wrap(desc, 14, "sans", left_w)
        for i, line in enumerate(lines):
            out += text(left_text, y + 52 + i * 20, line, 14, "sans", SOFT)
        y += 52 + len(lines) * 20 + 12
    height = y + 24
    ry = 62
    for date, degree, school in schools:
        out += f'<path d="M{right_x} {ry}.5H{w - 32}" stroke="{RULE}"/>'
        out += text(right_x, ry + 28, date, 12.5, "mono", MUTED)
        out += text(right_text, ry + 28, degree, 15, "bold", INK)
        lines = wrap(school, 13.5, "sans", w - 32 - right_text)
        for i, line in enumerate(lines):
            out += text(right_text, ry + 50 + i * 19, line, 13.5, "sans", SOFT)
        ry += 50 + len(lines) * 19 + 14
    height = max(height, ry + 24)
    write("experience.svg", svg(w, height, frame(w, height, out),
                                title="Experience: Caladrius, Unidev Software Turkey, IEEE İnönü. Education: İnönü University, MUT Warsaw, Malatya Turgut Özal University"))


def toolkit():
    w = 1200
    rows = [
        ("AUTONOMY AND VISION", "A*, MPC with CasADi/IPOPT, behaviour state machines, PPO, sensor fusion, YOLOv11, lane and depth estimation, PyTorch, LSTM, SocialTransformer"),
        ("LANGUAGE MODELS", "LoRA fine-tuning, MedGemma 27B, Hugging Face, LangChain, FAISS, BM25, Ollama"),
        ("PROGRAMMING", "Python, C++ and SQL daily; R and Java when needed"),
        ("BACKEND AND DATA", "FastAPI, Django, Spring Boot, PostgreSQL, MySQL, Docker, Git, Pandas, NumPy, Folium, React, React Native"),
        ("SPOKEN LANGUAGES", "Turkish (native), English (C1), Polish (B1), German (A2), Indonesian (A1)"),
    ]
    value_x, y, out = 300, 20, ""
    for i, (key, value) in enumerate(rows):
        if i:
            out += f'<path d="M32 {y}.5H{w - 32}" stroke="{RULE}"/>'
        out += text(32, y + 30, key, 11.5, "mono", MUTED, extra='letter-spacing="1.2"')
        lines = wrap(value, 15, "sans", w - 32 - value_x)
        for j, line in enumerate(lines):
            out += text(value_x, y + 30 + j * 22, line, 15, "sans", INK if j == 0 and i < 4 else SOFT)
        y += 30 + (len(lines) - 1) * 22 + 20
    height = y + 4
    write("toolkit.svg", svg(w, height, frame(w, height, out), title="Toolkit: " + "; ".join(v for _, v in rows),
                             fonts=("sans", "mono")))


if __name__ == "__main__":
    write("header-lidar.svg", header())
    for build in (seyir, deepderm, turkrag, thermground, skyguard, notary):
        build()
    for number, name in (("01", "WORK"), ("02", "EXPERIENCE"), ("03", "TOOLKIT"), ("04", "ACTIVITY")):
        section(number, name)
    experience()
    toolkit()
    for f in sorted(ASSETS.rglob("*.svg")):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size / 1024:.1f} KB")
