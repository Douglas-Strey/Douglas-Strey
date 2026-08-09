#!/usr/bin/env python3
"""Authored SVG assets for the Douglas-Strey profile README.

Run:  python3 .github/scripts/gen.py

Regenerates assets/{banner,stack}-{dark,light}{,-sm}.svg. The signal panel is
generated separately by signal.mjs, because its numbers change daily while these
only change when the content does.

Four variants per asset: {dark,light} x {wide,narrow}, paired in the README
through <picture> sources that combine prefers-color-scheme with max-width.
Grounds match GitHub's own canvas so the assets read as page, not as pasted box.
GeistMono (OFL) is subset to the used glyphs and embedded, so lettering is
identical on every machine instead of falling back to the visitor's system mono.
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")
os.makedirs(OUT, exist_ok=True)
_HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {w: open(os.path.join(_HERE, "fonts", "%s.b64" % w)).read().strip()
         for w in ("regular", "medium", "semibold")}

DARK = dict(
    bg="#0D1117", panel="#11181F", line="#212C38", line2="#2B3946",
    text="#D8E0E9", dim="#93A3B2", dimmer="#74838F",
    mint="#3DDC97", sweep="#3DDC97", sweepop=".26", tickbase=".26", edgeop=".38",
)
LIGHT = dict(
    bg="#FFFFFF", panel="#F7F9FB", line="#DEE6EE", line2="#A9BAC9",
    text="#131E29", dim="#4B5D6B", dimmer="#5F6D79",
    mint="#0A7E57", sweep="#0A7E57", sweepop=".13", tickbase=".34", edgeop=".22",
)

CONTRACT = """
  THESIS: a profile that reads as an operations console for the systems Douglas
  actually runs, refusing the neon terminal-window trope of developer READMEs.
  OWN-WORLD: GitHub-canvas ground, 1px hairline panels, embedded GeistMono
  subset, one mint signal accent, telemetry ticks as the only ornament.
  STORY: visitor sees a senior engineer with named production systems, reads the
  stack in a single pass, and leaves knowing how to reach him.
  FIRST VIEWPORT: name at display scale left, in-production readout right, a
  telemetry strip spanning the full width beneath both, crossed by one scan.
  FORM: monitoring console; pinned by the user, no roll.
  FINISH: unreviewed and undocumented is unfinished; this build ends with the
  finish review, the verdict, and DESIGN.md.
"""

FONT_CSS = "".join(
    "@font-face{font-family:GM;font-style:normal;font-weight:%d;"
    "src:url(data:font/woff2;base64,%s) format('woff2')}" % (wg, FONTS[w])
    for w, wg in (("regular", 400), ("medium", 500), ("semibold", 600))
)


def head(w, h, p, css, desc):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-label="{desc}" font-kerning="none">'
        f"<!--{CONTRACT}--><title>{desc}</title><style>{FONT_CSS}"
        "text{font-family:GM,ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}"
        f".t{{fill:{p['text']}}}.d{{fill:{p['dim']}}}.dd{{fill:{p['dimmer']}}}.m{{fill:{p['mint']}}}"
        f"{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>"
    )


def noise(i):  # readable, deterministic
    x = (i * 2654435761) & 0xFFFFFFFF
    x ^= (x >> 15)
    x = (x * 2246822519) & 0xFFFFFFFF
    x ^= (x >> 13)
    return (x % 10000) / 10000.0


ROWS = [
    ("quimerax", "threat intelligence"),
    ("fiscaliza", "field inspection"),
    ("acolher", "social outreach"),
    ("sigri", "institutional relations"),
]
STACK = [
    ("backend", "PHP · Laravel · Python · Go · REST &amp; GraphQL APIs"),
    ("frontend", "Vue · Nuxt · TypeScript · JavaScript · SCSS"),
    ("mobile", "React Native · Expo · Swift"),
    ("data", "MySQL · PostgreSQL · Redis · queues &amp; workers"),
    ("platform", "Docker · GitHub Actions · AWS · DigitalOcean · Sentry"),
    ("practice", "code review · testing (Pest, PHPUnit) · mentoring · architecture"),
]
DESC_B = "Douglas Strey — Tech Lead and Senior Software Engineer, Santa Catarina Brazil, shipping QuimeraX (threat intelligence), Fiscaliza (field inspection), Acolher (social outreach) and SIGRI (institutional relations)"
DESC_S = "Stack — backend PHP Laravel Python Go; frontend Vue Nuxt TypeScript; mobile React Native Expo Swift; data MySQL PostgreSQL Redis; platform Docker GitHub Actions AWS"

CYCLE = 7.0
PEAK = 0.03  # keyframe fraction at which a tick reaches full brightness


def wrap(value, avail_px, size):
    """Greedy wrap on ' · ', measured in monospace advance widths."""
    limit = int(avail_px / (size * 0.6))
    words, lines, cur = value.split(" · "), [], ""
    for w in words:
        trial = w if not cur else cur + " · " + w
        if len(trial.replace("&amp;", "&")) <= limit or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def telemetry(p, x0, x1, base_y, pitch, tall_h, short_h, sweep_w, width):
    """One authored motion: a scan crossing the strip, ticks lighting under its head.

    Each tick's delay is derived from when the scan's leading line reaches that
    tick, so the highlight peaks beneath the line and decays behind it. Deriving
    it from the group's left edge instead put the highlight 302px in arrears.
    PEAK is shared with the keyframes below; the two must not drift apart again.
    """
    out = [f'<line x1="{x0}" y1="{base_y + .5}" x2="{x1}" y2="{base_y + .5}" stroke="{p["line"]}"/>']
    n = int((x1 - x0) / pitch)
    speed = (width + sweep_w) / CYCLE  # px per second the scan travels
    for i in range(n):
        x = x0 + i * pitch
        v = noise(i)
        tall = v > 0.86
        h = 3 + v * (tall_h if tall else short_h)
        t = (x + 0.625) / speed - PEAK * CYCLE
        out.append(
            f'<rect class="tk" x="{x:.1f}" y="{base_y - h:.1f}" width="{pitch * .38:.1f}" '
            f'height="{h:.1f}" fill="{p["mint"] if tall else p["line2"]}" '
            f'style="animation-delay:{t - CYCLE:.2f}s"/>'
        )
    return "".join(out)


def sweep_defs(p, w, h, sweep_w):
    return (
        f'<defs><linearGradient id="sw" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{p["sweep"]}" stop-opacity="0"/>'
        f'<stop offset=".62" stop-color="{p["sweep"]}" stop-opacity="{float(p["sweepop"]) * .42:.3f}"/>'
        f'<stop offset="1" stop-color="{p["sweep"]}" stop-opacity="{p["sweepop"]}"/></linearGradient>'
        f'<filter id="bl" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feGaussianBlur stdDeviation="13"/></filter></defs>'
    )


def sweep_g(p, h, sweep_w):
    return (
        f'<g id="sc"><rect x="0" y="0" width="{sweep_w}" height="{h}" fill="url(#sw)" filter="url(#bl)"/>'
        f'<rect x="{sweep_w - 1.25}" y="0" width="1.25" height="{h}" fill="{p["sweep"]}" opacity="{p['edgeop']}"/></g>'
    )


def motion_css(p, w, sweep_w):
    return (
        f".tk{{animation:pulse {CYCLE}s linear infinite}}"
        f"@keyframes pulse{{0%{{opacity:{p['tickbase']}}}{PEAK * 100:g}%{{opacity:1}}"
        f"13%{{opacity:{p['tickbase']}}}100%{{opacity:{p['tickbase']}}}}}"
        f"#sc{{animation:travel {CYCLE}s linear infinite}}"
        f"@keyframes travel{{from{{transform:translateX({-sweep_w}px)}}to{{transform:translateX({w}px)}}}}"
    )


# ------------------------------------------------------------------ banner
def banner_wide(p):
    W, H, PAD, SW = 1200, 300, 1, 260
    css = (
        ".nm{font-weight:600;font-size:62px;letter-spacing:-.035em}"
        ".rl{font-weight:500;font-size:19px;letter-spacing:-.012em}"
        ".mt{font-weight:400;font-size:14.5px}"
        ".pl{font-weight:400;font-size:12.5px}"
        ".pk{font-weight:500;font-size:14px}.pv{font-weight:400;font-size:14px}"
        + motion_css(p, W, SW)
    )
    s = [head(W, H, p, css, DESC_B), sweep_defs(p, W, H, SW),
         f'<rect width="{W}" height="{H}" fill="{p["bg"]}"/>']
    s.append(telemetry(p, PAD, W - PAD, 268, 7.2, 30, 17, SW, W))
    px, py, ph = 690, 44, 176
    pw = W - PAD - px
    s.append(f'<rect x="{px}.5" y="{py}.5" width="{pw - 1}" height="{ph - 1}" rx="4" fill="{p["panel"]}" stroke="{p["line"]}"/>')
    s.append(sweep_g(p, H, SW))
    s.append(f'<text class="nm t" x="{PAD}" y="122">Douglas Strey</text>')
    s.append(f'<text class="rl m" x="{PAD}" y="158">Tech Lead  ·  Senior Software Engineer</text>')
    s.append(f'<text class="mt d" x="{PAD}" y="190">Santa Catarina, Brazil   —   Hisoft &amp; Podtech</text>')
    s.append(f'<text class="pl dd" x="{px + 22}" y="{py + 29}">in production</text>')
    y = py + 60
    for i, (k, v) in enumerate(ROWS):
        s.append(f'<rect x="{px + 22}" y="{y - 7.5}" width="3" height="3" fill="{p["mint"]}"/>')
        s.append(f'<text class="pk t" x="{px + 38}" y="{y}">{k}</text>')
        s.append(f'<text class="pv d" x="{px + 150}" y="{y}">{v}</text>')
        if i < 3:
            s.append(f'<line x1="{px + 22}" y1="{y + 13.5}" x2="{px + pw - 22}" y2="{y + 13.5}" stroke="{p["line"]}"/>')
        y += 29
    return "".join(s) + "</svg>"


def banner_narrow(p):
    W, H, PAD, SW = 360, 320, 1, 96
    css = (
        ".nm{font-weight:600;font-size:34px;letter-spacing:-.035em}"
        ".rl{font-weight:500;font-size:13.5px;letter-spacing:-.015em}"
        ".mt{font-weight:400;font-size:11.5px}"
        ".pl{font-weight:400;font-size:11px}"
        ".pk{font-weight:500;font-size:12.5px}.pv{font-weight:400;font-size:12.5px}"
        + motion_css(p, W, SW)
    )
    s = [head(W, H, p, css, DESC_B), sweep_defs(p, W, H, SW),
         f'<rect width="{W}" height="{H}" fill="{p["bg"]}"/>']
    s.append(telemetry(p, PAD, W - PAD, 302, 4.6, 17, 10, SW, W))
    py, ph = 140, 134
    pw = W - PAD * 2
    s.append(f'<rect x="{PAD}.5" y="{py}.5" width="{pw - 1}" height="{ph - 1}" rx="4" fill="{p["panel"]}" stroke="{p["line"]}"/>')
    s.append(sweep_g(p, H, SW))
    s.append(f'<text class="nm t" x="{PAD}" y="52">Douglas Strey</text>')
    s.append(f'<text class="rl m" x="{PAD}" y="78">Tech Lead · Senior Software Engineer</text>')
    s.append(f'<text class="mt d" x="{PAD}" y="100">Santa Catarina, Brazil — Hisoft &amp; Podtech</text>')
    s.append(f'<text class="pl dd" x="{PAD + 14}" y="{py + 22}">in production</text>')
    y = py + 46
    for i, (k, v) in enumerate(ROWS):
        s.append(f'<rect x="{PAD + 14}" y="{y - 6.5}" width="2.5" height="2.5" fill="{p["mint"]}"/>')
        s.append(f'<text class="pk t" x="{PAD + 26}" y="{y}">{k}</text>')
        s.append(f'<text class="pv d" x="{PAD + 104}" y="{y}">{v}</text>')
        if i < 3:
            s.append(f'<line x1="{PAD + 14}" y1="{y + 11}" x2="{W - PAD - 14}" y2="{y + 11}" stroke="{p["line"]}"/>')
        y += 23
    return "".join(s) + "</svg>"


# ------------------------------------------------------------------- stack
def stack_wide(p):
    W, PAD, step, top = 1200, 1, 38, 26
    H = top * 2 + step * len(STACK)
    css = (".k{font-weight:500;font-size:14.5px;letter-spacing:.02em}"
           ".v{font-weight:400;font-size:14.5px;letter-spacing:-.005em}")
    s = [head(W, H, p, css, DESC_S), f'<rect width="{W}" height="{H}" fill="{p["bg"]}"/>']
    s.append(f'<rect x="{PAD}.5" y="8.5" width="{W - PAD * 2 - 1}" height="{H - 18}" rx="4" fill="{p["panel"]}" stroke="{p["line"]}"/>')
    colx, valx = PAD + 30, PAD + 168
    s.append(f'<line x1="{valx - 26}" y1="24" x2="{valx - 26}" y2="{H - 24}" stroke="{p["line"]}"/>')
    y = top + 26
    for i, (k, v) in enumerate(STACK):
        s.append(f'<text class="k m" x="{colx}" y="{y}">{k}</text>')
        s.append(f'<text class="v t" x="{valx}" y="{y}">{v}</text>')
        if i < len(STACK) - 1:
            s.append(f'<line x1="{colx}" y1="{y + 12.5}" x2="{W - PAD - 30}" y2="{y + 12.5}" stroke="{p["line"]}" opacity=".7"/>')
        y += step
    return "".join(s) + "</svg>"


def stack_narrow(p):
    W, PAD, step, top = 360, 1, 0, 14
    H = top * 2 + step * len(STACK) - 8
    size, x = 11.5, PAD + 14
    avail = W - PAD * 2 - 28
    lines = [(k, wrap(v, avail, size)) for k, v in STACK]
    H = top * 2 + sum(20 + 16 * len(w) for _, w in lines)
    css = (".k{font-weight:500;font-size:%gpx;letter-spacing:.02em}"
           ".v{font-weight:400;font-size:%gpx;letter-spacing:-.005em}" % (size, size))
    s = [head(W, H, p, css, DESC_S), f'<rect width="{W}" height="{H}" fill="{p["bg"]}"/>']
    s.append(f'<rect x="{PAD}.5" y="4.5" width="{W - PAD * 2 - 1}" height="{H - 10}" rx="4" fill="{p["panel"]}" stroke="{p["line"]}"/>')
    y = top + 12
    for i, (k, parts) in enumerate(lines):
        s.append(f'<text class="k m" x="{x}" y="{y}">{k}</text>')
        for j, part in enumerate(parts):
            s.append(f'<text class="v t" x="{x}" y="{y + 17 + j * 16}">{part}</text>')
        y += 20 + 16 * len(parts)
        if i < len(STACK) - 1:
            s.append(f'<line x1="{x}" y1="{y - 9.5}" x2="{W - PAD - 14}" y2="{y - 9.5}" stroke="{p["line"]}" opacity=".7"/>')
    return "".join(s) + "</svg>"


BUILD = (("banner", banner_wide, banner_narrow), ("stack", stack_wide, stack_narrow))
for name, wide, narrow in BUILD:
    for theme, pal in (("dark", DARK), ("light", LIGHT)):
        for kind, fn in (("", wide), ("-sm", narrow)):
            path = "%s/%s-%s%s.svg" % (OUT, name, theme, kind)
            open(path, "w").write(fn(pal))
            print("%-40s %3d KB" % (path, os.path.getsize(path) // 1024))
