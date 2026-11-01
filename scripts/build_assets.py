"""Builds the SVG images used in the profile README.

Run from the repo root:  python3 scripts/build_assets.py

The look follows barisparlakk.github.io: asphalt background, faint grid,
Archivo type and detection boxes in the Seyir colours. Fonts are embedded
as small subsets because GitHub serves README images without web fonts.
"""

import base64
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

BG = "#1a1f24"
ASPHALT = "#20262c"
INK = "#e9ecee"
DIM = "#9aa5af"
RED = "#ff4b4b"
YELLOW = "#f2c230"
BLUE = "#5cc8f0"
BODY = "#3d4751"
ROOF = "#4c5762"
LABEL_TEXT = "#20262c"


def font_face(name, file):
    data = base64.b64encode((ASSETS / "fonts" / file).read_bytes()).decode()
    return f"@font-face{{font-family:{name};src:url(data:font/woff2;base64,{data}) format('woff2');}}"


def load_metrics(file):
    font = TTFont(ASSETS / "fonts" / file)
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    return {chr(c): hmtx[g][0] / upm for c, g in cmap.items()}


METRICS = {"b": load_metrics("archivo-800-subset.woff2"), "m": load_metrics("archivo-500-subset.woff2")}


def text_width(s, size, cls="m"):
    return sum(METRICS[cls].get(ch, 0.6) for ch in s) * size


FONTS = font_face("A8", "archivo-800-subset.woff2") + font_face("A5", "archivo-500-subset.woff2")
BASE_CSS = (
    FONTS
    + ".b{font-family:A8,'Helvetica Neue',Arial,sans-serif;font-weight:800}"
    + ".m{font-family:A5,'Helvetica Neue',Arial,sans-serif;font-weight:500}"
    + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


def svg(w, h, body, css="", title=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" role="img">'
        f"<title>{escape(title)}</title><style>{BASE_CSS}{css}</style>{body}</svg>\n"
    )


def grid(pid, step=24):
    return (
        f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
        f'<path d="M{step} 0V{step}H0" stroke="{INK}" stroke-opacity=".05"/></pattern>'
    )


def text(x, y, s, size, cls="m", fill=INK, anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" {extra}>{escape(s)}</text>'
    )


def tag(x, y, s, color, size=11):
    """A filled detection label, bottom-left corner at (x, y)."""
    w = text_width(s, size, "b") + 10
    h = size + 5
    return (
        f'<rect x="{x}" y="{y - h}" width="{w:.0f}" height="{h}" fill="{color}"/>'
        + text(x + 5, y - 4.5, s, size, "b", LABEL_TEXT)
    )


def vehicle(x, y, w, h, color, label, body=BODY, roof=ROOF):
    """Top-down vehicle centred on (x, y) with its detection box and label."""
    left, top = x - w / 2, y - h / 2
    return (
        f'<rect x="{left}" y="{top}" width="{w}" height="{h}" rx="4" fill="{body}"/>'
        f'<rect x="{left + w * 0.3}" y="{top + 3}" width="{w * 0.4}" height="{h - 6}" rx="2" fill="{roof}"/>'
        f'<rect x="{left - 4}" y="{top - 4}" width="{w + 8}" height="{h + 8}" stroke="{color}" stroke-width="1.5"/>'
        + tag(left - 4.75, top - 4, label, color, 10)
    )


def arrow_icon(x, y):
    return (
        f'<path d="M{x} {y + 14}L{x + 14} {y}M{x + 3} {y}H{x + 14}V{y + 11}" '
        f'stroke="{DIM}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    )


# ---------------------------------------------------------------- header

def header():
    w, h = 1200, 420
    css = """
.lane{stroke-dasharray:28 22;animation:dash 1s linear infinite}
@keyframes dash{to{stroke-dashoffset:50}}
.path{stroke-dasharray:2 7;animation:path .9s linear infinite}
@keyframes path{to{stroke-dashoffset:-18}}
.ov{animation:ov 13s linear infinite}
@keyframes ov{from{transform:translateX(-200px)}to{transform:translateX(1400px)}}
.sl{animation:sl 20s linear infinite}
@keyframes sl{from{transform:translateX(1400px)}to{transform:translateX(-200px)}}
.op{animation:op 5.5s linear infinite}
@keyframes op{from{transform:translateX(1400px)}to{transform:translateX(-300px)}}
.jit{animation:jit 1.6s steps(1) infinite}
@keyframes jit{0%{transform:translate(0,0)}25%{transform:translate(3px,-2px)}50%{transform:translate(-2px,2px)}75%{transform:translate(1px,3px)}}
.c1,.c2,.c3{opacity:0;animation:conf 4.8s steps(1) infinite}
.c2{animation-delay:1.6s}.c3{animation-delay:3.2s}
@keyframes conf{0%{opacity:1}33.33%{opacity:0}}
.pulse{animation:pulse 2s ease-in-out infinite}
@keyframes pulse{50%{opacity:.25}}
"""
    road_top, road_bottom = 252, 412
    lanes = {"o1": 276, "o2": 312, "s1": 356, "s2": 392}

    def moving(cls, delay, inner):
        return f'<g class="{cls}" style="animation-delay:{delay}s">{inner}</g>'

    body = f"""
<defs>{grid("g")}<clipPath id="card"><rect width="{w}" height="{h}" rx="16"/></clipPath></defs>
<g clip-path="url(#card)">
<rect width="{w}" height="{h}" fill="{BG}"/>
<rect width="{w}" height="{h}" fill="url(#g)"/>
<rect y="{road_top}" width="{w}" height="{road_bottom - road_top}" fill="{ASPHALT}"/>
<rect y="{road_top}" width="{w}" height="{road_bottom - road_top}" fill="url(#g)"/>
<path d="M0 {road_top}H{w}" stroke="{INK}" stroke-opacity=".7" stroke-width="2"/>
<path d="M0 {road_bottom - 4}H{w}" stroke="{INK}" stroke-opacity=".7" stroke-width="2"/>
<path class="lane" d="M0 294H{w + 50}" stroke="{INK}" stroke-opacity=".5" stroke-width="2"/>
<path class="lane" d="M0 374H{w + 50}" stroke="{INK}" stroke-opacity=".5" stroke-width="2"/>
<path d="M0 332H{w}M0 336H{w}" stroke="{YELLOW}" stroke-width="2"/>

{moving("op", 0, vehicle(0, lanes["o1"], 46, 20, YELLOW, "car 0.95"))}
{moving("op", -2.4, vehicle(0, lanes["o2"], 60, 22, BLUE, "dolmuş 0.86"))}
{moving("op", -4.1, vehicle(0, lanes["o1"], 30, 12, BLUE, "motorcycle 0.71"))}
{moving("sl", -6, vehicle(0, lanes["s1"], 60, 22, BLUE, "dolmuş 0.96"))}
{moving("sl", -13, vehicle(0, lanes["s1"], 46, 20, YELLOW, "car 0.97"))}

<path class="path" d="M226 {lanes["s2"]}C300 {lanes["s2"]} 320 {lanes["s1"]} 420 {lanes["s1"]}H560" stroke="{RED}" stroke-width="2.5" stroke-linecap="round"/>
{vehicle(180, lanes["s2"], 50, 22, RED, "ego · mpc < 50 ms", body=INK, roof="#c9ced3")}

<text x="56" y="152" class="b" font-size="108" letter-spacing="-3" fill="{INK}">Barış Parlak</text>
<g class="jit">
  <rect x="46" y="58" width="310" height="110" stroke="{RED}" stroke-width="2.5"/>
  <g class="c1">{tag(44.75, 58, "person 0.41", RED, 13)}</g>
  <g class="c2">{tag(44.75, 58, "person 0.87", RED, 13)}</g>
  <g class="c3">{tag(44.75, 58, "person 0.96", RED, 13)}</g>
</g>
{text(58, 204, "AI developer and computer engineering student in Istanbul", 24, fill=INK)}
{text(58, 234, "PERCEPTION   ·   PLANNING   ·   LANGUAGE MODELS", 14, fill=DIM, extra='letter-spacing="2"')}

<circle class="pulse" cx="{w - 300}" cy="54" r="5" fill="{YELLOW}"/>
{text(w - 286, 59, "Open to roles in AI, autonomy and data", 15, fill=DIM)}
</g>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" stroke="{INK}" stroke-opacity=".12" stroke-width="2"/>
"""
    return svg(w, h, body, css, "Barış Parlak: AI developer and computer engineering student in Istanbul")


# ---------------------------------------------------------------- cards

CARD_W, CARD_H, PANEL_H = 600, 356, 180


def card(slug, title, chip, chip_color, lines, tags, panel, css=""):
    tag_x, tags_svg = 32, ""
    for t in tags:
        tw = text_width(t, 12.5) + 24
        tags_svg += (
            f'<rect x="{tag_x}" y="{CARD_H - 48}" width="{tw:.0f}" height="26" rx="13" '
            f'stroke="{INK}" stroke-opacity=".18"/>'
            + text(tag_x + tw / 2, CARD_H - 30.5, t, 12.5, fill=DIM, anchor="middle")
        )
        tag_x += tw + 8
    desc = "".join(text(32, 262 + i * 23, line, 16.5, fill=DIM) for i, line in enumerate(lines))
    body = f"""
<defs>{grid("g", 20)}<clipPath id="card"><rect width="{CARD_W}" height="{CARD_H}" rx="14"/></clipPath>
<clipPath id="panel"><rect width="{CARD_W}" height="{PANEL_H}"/></clipPath></defs>
<g clip-path="url(#card)">
<rect width="{CARD_W}" height="{CARD_H}" fill="{BG}"/>
<g clip-path="url(#panel)">
<rect width="{CARD_W}" height="{PANEL_H}" fill="{ASPHALT}"/>
<rect width="{CARD_W}" height="{PANEL_H}" fill="url(#g)"/>
{panel}
</g>
<path d="M0 {PANEL_H}H{CARD_W}" stroke="{INK}" stroke-opacity=".12"/>
{tag(20, 34, chip, chip_color, 11)}
{text(32, 228, title, 30, "b")}
{arrow_icon(CARD_W - 50, 208)}
{desc}
{tags_svg}
</g>
<rect x="1" y="1" width="{CARD_W - 2}" height="{CARD_H - 2}" rx="13" stroke="{INK}" stroke-opacity=".12" stroke-width="2"/>
"""
    (ASSETS / "cards" / f"{slug}.svg").write_text(svg(CARD_W, CARD_H, body, css, f"{title}: {' '.join(lines)}"))


def thermground():
    blobs = ""
    for i, (x, y, r) in enumerate([(132, 104, 15), (176, 122, 14), (472, 62, 26)]):
        blobs += f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r * (1.6 if i < 2 else 0.7)}" fill="url(#heat)"/>'
    panel = f"""
<defs>
<radialGradient id="heat"><stop offset="0" stop-color="#fff6c8"/><stop offset=".3" stop-color="#ffb347"/>
<stop offset=".65" stop-color="#d1386c" stop-opacity=".8"/><stop offset="1" stop-color="#4b1a6e" stop-opacity="0"/></radialGradient>
<linearGradient id="cold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#140a26"/><stop offset="1" stop-color="#2a0f40"/></linearGradient>
<filter id="noise"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/>
<feColorMatrix values="0 0 0 0 .6  0 0 0 0 .3  0 0 0 0 .8  0 0 0 .22 0"/></filter>
</defs>
<rect width="{CARD_W}" height="{PANEL_H}" fill="url(#cold)"/>
<path d="M0 150C120 128 260 160 380 136S560 118 600 126V180H0Z" fill="#3a1652" opacity=".7"/>
<rect width="{CARD_W}" height="{PANEL_H}" filter="url(#noise)"/>
{blobs}
<rect class="scan" y="0" width="{CARD_W}" height="2" fill="{INK}" opacity=".35"/>
<g class="box"><rect x="108" y="72" width="94" height="80" stroke="{RED}" stroke-width="1.5"/>{tag(107.25, 72, "person × 2", RED, 10)}</g>
<rect x="318" y="98" width="262" height="64" rx="8" fill="{BG}" fill-opacity=".9"/>
{text(332, 124, "Q", 14, "b", YELLOW)}{text(350, 124, "How many people by the river?", 13.5)}
{text(332, 148, "A", 14, "b", RED)}{text(350, 148, "Two, both on the left bank.", 13.5, fill=DIM)}
"""
    css = """.scan{animation:scan 3.5s linear infinite}@keyframes scan{from{transform:translateY(0)}to{transform:translateY(180px)}}
.box{animation:blink 3.5s steps(1) infinite}@keyframes blink{0%{opacity:0}30%{opacity:1}}"""
    card("thermground", "thermground", "NOW BUILDING", YELLOW,
         ["A small vision-language model for night search-and-rescue.",
          "Answers come from the thermal image, not language priors."],
         ["VLM", "Thermal UAV", "PyTorch"], panel, css)


def seyir():
    car_y, ego_y = 126, 158
    trajectories = "".join(
        f'<path class="tr" d="{d}" stroke="{YELLOW}" stroke-opacity="{o}" stroke-width="2" stroke-linecap="round"/>'
        for d, o in [
            (f"M330 {car_y}H520", 1),
            (f"M330 {car_y}C390 {car_y} 410 {ego_y} 500 {ego_y}", 0.55),
        ]
    )
    panel = f"""
<path d="M0 46H600M0 174H600" stroke="{INK}" stroke-opacity=".7" stroke-width="2"/>
<path class="lane" d="M0 78H650M0 142H650" stroke="{INK}" stroke-opacity=".5" stroke-width="2"/>
<path d="M0 108H600M0 112H600" stroke="{YELLOW}" stroke-width="2"/>
{trajectories}
{vehicle(300, car_y, 46, 20, YELLOW, "car 0.97")}
{vehicle(470, 62, 60, 22, BLUE, "dolmuş 0.86")}
{vehicle(140, ego_y, 50, 22, RED, "ego · mpc < 50 ms", body=INK, roof="#c9ced3")}
"""
    css = """.lane{stroke-dasharray:24 20;animation:dash 1s linear infinite}@keyframes dash{to{stroke-dashoffset:44}}
.tr{stroke-dasharray:2 7;animation:tr .9s linear infinite}@keyframes tr{to{stroke-dashoffset:-18}}"""
    card("seyir", "Seyir", "AUTONOMY", RED,
         ["End-to-end driving stack for Turkish traffic, in CARLA.",
          "Perception, prediction, planning and MPC control."],
         ["PyTorch", "CARLA", "C++", "MPC"], panel, css)


def skyguard():
    cars = [(60, 84, 0), (96, 84, 0), (150, 100, 0), (232, 84, 0), (270, 100, 0),
            (205, 34, 1), (220, 150, 1), (205, 132, 1)]
    people = [(40, 140), (52, 146), (290, 40), (300, 150)]
    objs = ""
    for i, (x, y, vertical) in enumerate(cars):
        w, h = (8, 14) if vertical else (14, 8)
        objs += (f'<g class="f" style="animation-delay:{-i * 0.37:.2f}s"><rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="1.5" fill="{ROOF}"/>'
                 f'<rect x="{x - w / 2 - 3}" y="{y - h / 2 - 3}" width="{w + 6}" height="{h + 6}" stroke="{YELLOW}" stroke-width="1.2"/></g>')
    for i, (x, y) in enumerate(people):
        objs += (f'<g class="f" style="animation-delay:{-i * 0.53:.2f}s"><circle cx="{x}" cy="{y}" r="2.5" fill="{INK}"/>'
                 f'<rect x="{x - 6}" y="{y - 6}" width="12" height="12" stroke="{RED}" stroke-width="1.2"/></g>')
    steps = ["PyTorch", "ONNX", "TensorRT FP16 / INT8"]
    pipe = ""
    for i, s in enumerate(steps):
        y = 46 + i * 46
        last = i == len(steps) - 1
        pipe += (f'<rect x="380" y="{y - 17}" width="{text_width(s, 14, "b" if last else "m") + 28:.0f}" height="30" rx="6" '
                 f'fill="{BLUE if last else BG}" stroke="{BLUE}" stroke-opacity="{1 if last else .5}"/>'
                 + text(394, y + 3, s, 14, "b" if last else "m", LABEL_TEXT if last else INK))
        if not last:
            pipe += f'<path d="M394 {y + 15}V{y + 27}" stroke="{BLUE}" stroke-width="2" stroke-dasharray="2 4"/>'
    panel = f"""
<rect x="0" y="72" width="340" height="40" fill="#2a3138"/>
<rect x="192" y="0" width="40" height="180" fill="#2a3138"/>
<path d="M0 92H192M232 92H340M212 0V72M212 112V180" stroke="{INK}" stroke-opacity=".35" stroke-dasharray="8 8"/>
{objs}
<path d="M340 0V180" stroke="{INK}" stroke-opacity=".12"/>
{pipe}
"""
    css = ".f{animation:f 2.4s steps(1) infinite}@keyframes f{0%{opacity:1}88%{opacity:.25}}"
    card("skyguard", "Skyguard", "EDGE VISION", BLUE,
         ["Aerial object detection with YOLOv8m on VisDrone,",
          "exported to TensorRT and benchmarked on an NVIDIA L4."],
         ["YOLOv8", "ONNX", "TensorRT"], panel, css)


def turkrag():
    cols = {
        "BM25": (34, ["Saklama §4", "KVKK md. 7", "Aydınlatma"]),
        "VECTOR": (204, ["KVKK md. 7", "Envanter", "Saklama §4"]),
        "FUSED": (414, ["KVKK md. 7", "Saklama §4", "Envanter"]),
    }
    hl = {"KVKK md. 7": YELLOW, "Saklama §4": BLUE}
    out, pos = "", {}
    for name, (x, docs) in cols.items():
        out += text(x, 48, name, 11, "b", DIM, extra='letter-spacing="1.5"')
        for i, d in enumerate(docs):
            y = 60 + i * 28
            pos[(name, d)] = (x, y)
            color = hl.get(d)
            out += (f'<rect x="{x}" y="{y}" width="132" height="22" rx="4" fill="{BODY}" '
                    f'stroke="{color or "none"}" stroke-width="1.5"/>'
                    + text(x + 10, y + 15.5, d, 12, fill=INK))
    links = ""
    for src in ("BM25", "VECTOR"):
        for d, color in hl.items():
            x1, y1 = pos[(src, d)]
            x2, y2 = pos[("FUSED", d)]
            x1 += 132
            links += (f'<path class="flow" d="M{x1} {y1 + 11}C{x1 + 60} {y1 + 11} {x2 - 60} {y2 + 11} {x2} {y2 + 11}" '
                      f'stroke="{color}" stroke-opacity=".75" stroke-width="1.5"/>')
    panel = f"""
{links}
{out}
<rect x="414" y="150" width="132" height="22" rx="11" fill="{YELLOW}"/>
{text(480, 165.5, "local LLM → answer", 12, "b", LABEL_TEXT, "middle")}
"""
    css = ".flow{stroke-dasharray:4 5;animation:flow 1.2s linear infinite}@keyframes flow{to{stroke-dashoffset:-18}}"
    card("turkrag", "TurkRAG", "LANGUAGE MODELS", YELLOW,
         ["On-premise question answering over Turkish documents.",
          "Hybrid retrieval and a local model, KVKK-friendly."],
         ["RAG", "BM25", "FastAPI", "Ollama"], panel, css)


def deepderm():
    lesions = [(88, 70, 7, "papule 0.88"), (190, 52, 5, None), (150, 118, 8, "pustule 0.74"),
               (246, 104, 5, None), (70, 140, 4, None), (262, 150, 6, None)]
    out = ""
    for i, (x, y, r, label) in enumerate(lesions):
        out += f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#lesion)"/>'
        b = r + 6
        out += (f'<g class="d" style="animation-delay:{i * 0.35:.2f}s"><rect x="{x - b}" y="{y - b}" width="{2 * b}" height="{2 * b}" '
                f'stroke="{RED}" stroke-width="1.3"/>' + (tag(x - b - 0.65, y - b, label, RED, 9.5) if label else "") + "</g>")
    grades = ["mild", "moderate", "severe", "very severe"]
    meter = ""
    for i, g in enumerate(grades):
        x = 368 + i * 52
        on = g == "moderate"
        meter += f'<rect x="{x}" y="112" width="48" height="10" rx="3" fill="{BLUE if i <= 1 else BODY}"/>'
        if on:
            meter += text(x + 24, 142, g, 12, "b", BLUE, "middle")
    panel = f"""
<defs>
<linearGradient id="skin" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#d8a588"/><stop offset="1" stop-color="#bf8768"/></linearGradient>
<radialGradient id="lesion"><stop offset="0" stop-color="#f4e3c8"/><stop offset=".45" stop-color="#c2554f"/><stop offset="1" stop-color="#b8665a" stop-opacity="0"/></radialGradient>
</defs>
<rect width="330" height="{PANEL_H}" fill="url(#skin)"/>
{out}
{text(368, 62, "6", 34, "b")}
{text(394, 62, "inflammatory lesions", 13, fill=DIM)}
{text(368, 98, "HAYASHI GRADE", 11, "b", DIM, extra='letter-spacing="1.5"')}
{meter}
"""
    css = ".d{animation:d 4s steps(1) infinite}@keyframes d{0%{opacity:0}12%{opacity:1}}"
    card("deepderm", "DeepDerm", "MEDICAL AI", BLUE,
         ["Acne lesion detection and severity grading with YOLOv11,",
          "plus a doctor panel and a patient mobile app."],
         ["YOLOv11", "Spring Boot", "React Native"], panel, css)


def notary():
    blocks = ""
    for i in range(4):
        x = 300 + i * 70
        last = i == 3
        blocks += (f'<rect class="blk" style="animation-delay:{i * 0.45:.2f}s" x="{x}" y="70" width="48" height="48" rx="6" '
                   f'fill="{YELLOW if last else BODY}" stroke="{YELLOW}" stroke-opacity="{1 if last else .4}"/>')
        if not last:
            blocks += f'<path d="M{x + 48} 94H{x + 70}" stroke="{YELLOW}" stroke-opacity=".6" stroke-width="2"/>'
    panel = f"""
<path d="M44 52H86L102 68V128H44Z" fill="{INK}"/>
<path d="M86 52V68H102" fill="#c9ced3"/>
<path d="M54 82H90M54 94H92M54 106H84M54 118H88" stroke="{BODY}" stroke-width="3" stroke-linecap="round"/>
<path class="flow" d="M112 94H138" stroke="{DIM}" stroke-width="2"/>
<rect x="144" y="80" width="134" height="28" rx="14" stroke="{YELLOW}" stroke-opacity=".7"/>
{text(211, 99, "sha256 · 3f9a…e1c2", 12.5, fill=INK, anchor="middle")}
<path class="flow" d="M278 94H300" stroke="{DIM}" stroke-width="2"/>
{blocks}
<path d="M526 94L532 100L543 88" stroke="{LABEL_TEXT}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
{text(300, 148, "Solana PDA  [\"proof\", signer, hash]", 12, fill=DIM)}
"""
    css = """.flow{stroke-dasharray:4 4;animation:flow .8s linear infinite}@keyframes flow{to{stroke-dashoffset:-16}}
.blk{animation:blk 1.8s ease-in-out infinite}@keyframes blk{50%{stroke-opacity:1}}"""
    card("notary", "Notary", "ON-CHAIN PROOF", YELLOW,
         ["Verifiable document proofs for people and AI agents.",
          "Anyone can verify on-chain, even if the API is down."],
         ["Solana", "Anchor", "Python", "React"], panel, css)


# ---------------------------------------------------------------- footer

def footer():
    w, h = 1200, 64
    css = """.lane{stroke-dasharray:28 22;animation:dash 1s linear infinite}@keyframes dash{to{stroke-dashoffset:50}}
.ego{animation:ego 9s ease-in-out infinite}@keyframes ego{0%{transform:translateX(-80px)}100%{transform:translateX(1300px)}}"""
    body = f"""
<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="12"/></clipPath></defs>
<g clip-path="url(#c)">
<rect width="{w}" height="{h}" fill="{ASPHALT}"/>
<path d="M0 6H{w}M0 58H{w}" stroke="{INK}" stroke-opacity=".5" stroke-width="2"/>
<path class="lane" d="M0 32H{w + 50}" stroke="{INK}" stroke-opacity=".4" stroke-width="2"/>
<g class="ego"><rect x="0" y="36" width="44" height="18" rx="4" fill="{INK}"/><rect x="13" y="39" width="18" height="12" rx="2" fill="#c9ced3"/></g>
</g>
"""
    return svg(w, h, body, css, "Road divider")


if __name__ == "__main__":
    (ASSETS / "header-road.svg").write_text(header())
    (ASSETS / "road-divider.svg").write_text(footer())
    for build in (thermground, seyir, skyguard, turkrag, deepderm, notary):
        build()
    for f in sorted(ASSETS.rglob("*.svg")):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size / 1024:.1f} KB")
