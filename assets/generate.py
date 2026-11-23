#!/usr/bin/env python3
"""
Generate every static SVG asset used by the profile README.

Why generate instead of hand-writing: all type is converted to outlines using the
real Inter metrics. That means (a) pill widths are measured, never guessed, and
(b) the picture is byte-identical in every browser — no font substitution, no
overflow when a viewer's system lacks Inter.

Outputs (committed, so the README needs no build step):
    assets/banner-{dark,light}.svg
    assets/stack-{dark,light}.svg
    assets/divider.svg

Author-side requirements:
    pip install fonttools brotli
    # Inter binaries: https://github.com/rsms/inter  (or npm pack @fontsource/inter)

Run:
    python3 assets/generate.py --inter-regular inter400.ttf --inter-bold inter700.ttf
"""
from __future__ import annotations

import argparse
import json
import pathlib
import xml.sax.saxutils as su

ASSETS = pathlib.Path(__file__).parent
PATHS = json.loads((ASSETS / "icon-paths.json").read_text())


class Outliner:
    """Turn strings into SVG path data using real font metrics."""

    def __init__(self, path: str):
        from fontTools.ttLib import TTFont
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen

        self.font = TTFont(path)
        self.upem = self.font["head"].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.hmtx = self.font["hmtx"]
        self._SVGPathPen = SVGPathPen
        self._TransformPen = TransformPen

    def adv(self, ch: str) -> int:
        name = self.cmap.get(ord(ch))
        return self.hmtx[name][0] if name else 0

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        w = sum(self.adv(c) for c in text) * size / self.upem
        return w + tracking * max(len(text) - 1, 0)

    def _glyph(self, ch: str, x: float, baseline: float, size: float) -> str:
        name = self.cmap.get(ord(ch))
        if name is None:
            return ""
        scale = size / self.upem
        pen = self._SVGPathPen(self.glyphs)
        self.glyphs[name].draw(self._TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
        return pen.getCommands()

    def path(self, text: str, x: float, baseline: float, size: float, tracking: float = 0.0) -> str:
        scale = size / self.upem
        cursor = x
        out = []
        for ch in text:
            d = self._glyph(ch, cursor, baseline, size)
            if d:
                out.append(d)
            cursor += self.adv(ch) * scale + tracking
        return " ".join(out)


# ─── marks ───────────────────────────────────────────────────────────────────
def candles(x: float, y: float, c: str, size: float = 15) -> str:
    """Two candlesticks — stand-in for tools with no public logo (MQL, MetaTrader)."""
    s = size / 15
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.4f})" '
        f'stroke="{c}" stroke-width="1.35" stroke-linecap="round" fill="none">'
        f'<path d="M4.4 1v13"/><path d="M11 3v9"/>'
        f'<rect x="2.1" y="4.2" width="4.6" height="6" rx="1" fill="{c}" stroke="none"/>'
        f'<rect x="8.7" y="5.4" width="4.6" height="5" rx="1"/>'
        f"</g>"
    )


def check(x: float, y: float, c: str, size: float = 15) -> str:
    """Check inside a ring — for QA work."""
    s = size / 15
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.4f})" fill="none" '
        f'stroke="{c}" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">'
        f'<circle cx="7.5" cy="7.5" r="6.2"/>'
        f'<path d="M4.8 7.7l1.9 1.9 3.6-3.9"/>'
        f"</g>"
    )


def icon(slug: str, x: float, y: float, c: str, size: float = 15) -> str:
    s = size / 24
    return (f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.4f})">'
            f'<path d="{PATHS[slug]}" fill="{c}"/></g>')


# ─── design tokens ───────────────────────────────────────────────────────────
BANNER = {
    "dark": dict(
        top="#4EE1C0", mid="#78C8FF", tail="#F5C451",
        grid="#ffffff", grid_op=0.045,
        glass="#ffffff", glass_op=0.035, edge="#ffffff", edge_op=0.12,
        name="#F4F8FF", tag="#A9BED4", eyebrow="#6FE3C8", sub="#8FA6C0",
        mark_a="#4EE1C0", mark_b="#F5C451", glow_a="#4EE1C0", glow_b="#F5C451",
        chips=[("#4EE1C0", "#A8EFDC"), ("#78C8FF", "#BCDDFF"),
               ("#F5C451", "#F8DFA6"), ("#E6EDF3", "#CBD8E6")],
    ),
    "light": dict(
        top="#0E9A87", mid="#2E86C1", tail="#C08A1E",
        grid="#0b1220", grid_op=0.05,
        glass="#ffffff", glass_op=0.6, edge="#0b1220", edge_op=0.11,
        name="#0B1220", tag="#455A70", eyebrow="#0B7F70", sub="#6B7C93",
        mark_a="#0B7F70", mark_b="#B8860B", glow_a="#0E9A87", glow_b="#E0A93A",
        chips=[("#0E9A87", "#0A6E60"), ("#2E86C1", "#1C5E8C"),
               ("#C08A1E", "#7A560C"), ("#0b1220", "#33445A")],
    ),
}

STACK = {
    "dark": dict(pill="#ffffff", pill_op=0.075, edge="#ffffff", edge_op=0.17,
                 label="#8AA3BE", text="#EAF2FA", mark="#4EE1C0"),
    "light": dict(pill="#0B1220", pill_op=0.04, edge="#0B1220", edge_op=0.16,
                  label="#6B7C93", text="#1B2836", mark="#0B7F70"),
}

BRAND = {
    "dark": {
        "python": "#4B9BD6", "javascript": "#E8C547", "typescript": "#4A9EE8",
        "html5": "#F0653F", "css": "#A78BFA", "nextdotjs": "#FFFFFF",
        "tailwindcss": "#38BDF8", "git": "#F0653F", "githubactions": "#4EA8FF",
        "vercel": "#FFFFFF", "xrp": "#4EE1C0", "solidity": "#9AA5B1",
        "github": "#D5E2F0", "googlemaps": "#4EA8FF", "gmail": "#EA4335",
        "tradingview": "#4EA8FF", "ethereum": "#9AA5B1",
    },
    "light": {
        "python": "#2E6C99", "javascript": "#8A6500", "typescript": "#1F6FBF",
        "html5": "#C43A1B", "css": "#663399", "nextdotjs": "#0B1220",
        "tailwindcss": "#0E7C99", "git": "#C0392B", "githubactions": "#1B6FC4",
        "vercel": "#0B1220", "xrp": "#1F8A5B", "solidity": "#4A5561",
        "github": "#3D4A57", "googlemaps": "#1A73E8", "gmail": "#C5221F",
        "tradingview": "#131622", "ethereum": "#4A5561",
    },
}

# label, [(icon slug, mark, caption)]
ROWS = [
    ("CODE", [
        ("python", None, "Python"), ("javascript", None, "JavaScript"),
        ("typescript", None, "TypeScript"), ("html5", None, "HTML / CSS"),
        ("tradingview", None, "Pine Script"), (None, "candles", "MQL4 / MQL5"),
    ]),
    ("BUILD & SHIP", [
        ("nextdotjs", None, "Next.js"), ("tailwindcss", None, "Tailwind"),
        ("git", None, "Git"), ("githubactions", None, "Actions"),
        ("vercel", None, "Vercel"), ("github", None, "GitHub"),
    ]),
    ("CHAIN & MARKETS", [
        ("xrp", None, "XRP Ledger"), ("solidity", None, "Solidity"),
        ("ethereum", None, "Ethereum"), (None, "candles", "MetaTrader 4/5"),
        (None, "check", "Manual QA"),
    ]),
]


# ─── stack ───────────────────────────────────────────────────────────────────
def build_stack(theme: str, bold: Outliner) -> str:
    t = STACK[theme]
    brand = BRAND[theme]
    pill_h, radius, ic = 34, 17, 15
    pad_l, pad_r, ic_gap, pill_gap, row_gap = 13, 15, 9, 10, 13
    label_col, left, top, width = 140, 22, 20, 980
    cap, lab = 13.0, 9.5
    out: list[str] = []
    y = top

    for name, items in ROWS:
        lx = left
        for ch in name:
            d = bold.path(ch, lx, y + pill_h / 2 + lab * 0.35, lab)
            if d:
                out.append(f'<path d="{d}" fill="{t["label"]}"/>')
            lx += bold.width(ch, lab) + 2.0

        x = left + label_col
        for slug, mark, caption in items:
            cw = bold.width(caption, cap)
            pw = pad_l + ic + ic_gap + cw + pad_r
            colour = brand.get(slug, t["text"]) if slug else t["mark"]
            gy = y + (pill_h - ic) / 2

            if slug:
                glyph = icon(slug, x + pad_l, gy, colour, ic)
            elif mark == "candles":
                glyph = candles(x + pad_l, gy, colour, ic)
            else:
                glyph = check(x + pad_l, gy, colour, ic)

            d = bold.path(caption, x + pad_l + ic + ic_gap, y + pill_h / 2 + cap * 0.36, cap)
            out.append(
                f'<rect x="{x:.2f}" y="{y}" width="{pw:.2f}" height="{pill_h}" rx="{radius}" '
                f'fill="{t["pill"]}" fill-opacity="{t["pill_op"]}" stroke="{t["edge"]}" '
                f'stroke-opacity="{t["edge_op"]}"/>{glyph}<path d="{d}" fill="{t["text"]}"/>'
            )
            x += pw + pill_gap
        y += pill_h + row_gap

    height = y - row_gap + top
    label = "|".join(c for _, items in ROWS for *_, c in items)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height:.0f}" '
        f'width="{width}" height="{height:.0f}" role="img" aria-label="Tech stack: {su.escape(label)}">\n'
        f'<title>Stack</title>\n' + "\n".join(out) + "\n</svg>\n"
    )


# ─── banner ──────────────────────────────────────────────────────────────────
def build_banner(theme: str, bold: Outliner, reg: Outliner) -> str:
    t = BANNER[theme]
    W, H = 1200, 340
    out: list[str] = []

    def grad(gid, stops):
        return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">' +
                "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops) + "</linearGradient>")

    defs = (
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{"#070b14" if theme=="dark" else "#F8FBFF"}"/>'
        f'<stop offset=".55" stop-color="{"#0a1220" if theme=="dark" else "#EEF4FA"}"/>'
        f'<stop offset="1" stop-color="{"#050e14" if theme=="dark" else "#FBF7EE"}"/>'
        f"</linearGradient>" + grad("accent", [("0", t["top"]), (".55", t["mid"]), ("1", t["tail"])]) +
        f'<radialGradient id="ga"><stop offset="0" stop-color="{t["glow_a"]}" stop-opacity="{0.26 if theme=="dark" else 0.15}"/>'
        f'<stop offset="1" stop-color="{t["glow_a"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="gb"><stop offset="0" stop-color="{t["glow_b"]}" stop-opacity="{0.14 if theme=="dark" else 0.16}"/>'
        f'<stop offset="1" stop-color="{t["glow_b"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="mono" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{"#FFE7A8" if theme=="dark" else "#D9A62E"}"/>'
        f'<stop offset=".5" stop-color="{"#F5C451" if theme=="dark" else "#B8860B"}"/>'
        f'<stop offset="1" stop-color="{"#C8922A" if theme=="dark" else "#8A6108"}"/>'
        f"</linearGradient>"
        f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M40 0H0V40" fill="none" stroke="{t["grid"]}" stroke-opacity="{t["grid_op"]}"/></pattern>'
        f'<clipPath id="round"><rect width="{W}" height="{H}" rx="24"/></clipPath>'
        f'<clipPath id="card"><rect x="28" y="28" width="1144" height="284" rx="20"/></clipPath>'
        f"</defs>"
    )

    out.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#grid)"/>')
    out.append(f'<circle cx="1075" cy="52" r="290" fill="url(#ga)"/>')
    out.append(f'<circle cx="120" cy="342" r="300" fill="url(#gb)"/>')
    out.append(f'<rect x="28" y="28" width="1144" height="284" rx="20" fill="{t["glass"]}" '
               f'fill-opacity="{t["glass_op"]}" stroke="{t["edge"]}" stroke-opacity="{t["edge_op"]}" stroke-width="1.5"/>')
    out.append('<g clip-path="url(#card)">'
               f'<rect x="28" y="28" width="1144" height="2.5" fill="url(#accent)" opacity=".9"/>'
               '</g>')

    # eyebrow
    out.append(f'<path d="{bold.path("GITHUB.COM/FARIZTIGER — MALAYSIA", 74, 104, 11, 3.1)}" fill="{t["eyebrow"]}"/>')
    # name
    out.append(f'<path d="{bold.path("Faiz Suhaimi", 72, 174, 56)}" fill="{t["name"]}"/>')
    # tagline
    out.append(f'<path d="{reg.path("Trading automation · Web3 research · Python tooling · QA", 75, 208, 18.5)}" fill="{t["tag"]}"/>')

    # chips
    chips = ["XAUUSD · MQL4/MQL5", "Python & data", "XRPL / Web3", "Manual QA"]
    cx, cy, ch = 74.0, 236.0, 33.0
    for (edge, text_col), label in zip(t["chips"], chips):
        tw = bold.width(label, 12.5)
        cw = tw + 30
        out.append(f'<rect x="{cx:.2f}" y="{cy}" width="{cw:.2f}" height="{ch}" rx="{ch/2}" '
                   f'fill="{edge}" fill-opacity="{0.10 if theme=="dark" else 0.08}" '
                   f'stroke="{edge}" stroke-opacity="{0.34 if theme=="dark" else 0.3}"/>')
        out.append(f'<path d="{bold.path(label, cx + 15, cy + ch / 2 + 4.4, 12.5)}" fill="{text_col}"/>')
        cx += cw + 10

    # monogram
    mx, my = 1004.0, 170.0
    out.append(f'<circle cx="{mx}" cy="{my}" r="84" fill="{t["glass"]}" fill-opacity="{0.05 if theme=="dark" else 0.85}" '
               f'stroke="url(#accent)" stroke-opacity=".6" stroke-width="1.6"/>')
    out.append(f'<circle cx="{mx}" cy="{my}" r="72" fill="none" stroke="{t["edge"]}" stroke-opacity=".09"/>')
    ft = bold.path("FT", 0, 0, 54)
    ftw = bold.width("FT", 54)
    out.append(f'<g transform="translate({mx - ftw / 2:.2f} {my + 19:.2f})"><path d="{ft}" fill="url(#mono)"/></g>')
    since = bold.path("SINCE 2016", 0, 0, 8.5, 2.4)
    sw = bold.width("SINCE 2016", 8.5, 2.4)
    out.append(f'<g transform="translate({mx - sw / 2:.2f} {my + 40:.2f})"><path d="{since}" fill="{t["sub"]}"/></g>')

    out.append(f'<rect x="44" y="308" width="1112" height="1" fill="url(#accent)" opacity=".18"/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Faiz Suhaimi — Malaysia-based independent developer: trading automation, Web3 research, Python tooling and QA">\n'
        f'<title>Faiz Suhaimi — Trading automation, Web3 research, Python tooling, QA</title>\n'
        f"{defs}\n<g clip-path=\"url(#round)\">\n" + "\n".join(out) + "\n</g>\n</svg>\n"
    )


DIVIDER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 44" width="1200" height="44" role="img" aria-label="Section divider">
<defs>
<linearGradient id="dl" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="#4EE1C0" stop-opacity="0"/>
<stop offset=".3" stop-color="#4EE1C0" stop-opacity=".5"/>
<stop offset=".5" stop-color="#78C8FF" stop-opacity=".7"/>
<stop offset=".7" stop-color="#F5C451" stop-opacity=".5"/>
<stop offset="1" stop-color="#F5C451" stop-opacity="0"/>
</linearGradient>
<linearGradient id="dg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#4EE1C0"/><stop offset="1" stop-color="#F5C451"/>
</linearGradient>
</defs>
<path d="M60 22H528" stroke="url(#dl)" stroke-width="1.25" stroke-linecap="round"/>
<path d="M672 22H1140" stroke="url(#dl)" stroke-width="1.25" stroke-linecap="round"/>
<rect x="592.5" y="14.5" width="15" height="15" rx="3.5" transform="rotate(45 600 22)" fill="none" stroke="url(#dg)" stroke-width="1.4"/>
<circle cx="600" cy="22" r="2.6" fill="url(#dg)"/>
</svg>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inter-regular", required=True)
    ap.add_argument("--inter-bold", required=True)
    a = ap.parse_args()

    bold, reg = Outliner(a.inter_bold), Outliner(a.inter_regular)
    for theme in ("dark", "light"):
        for name, data in (
            (f"banner-{theme}.svg", build_banner(theme, bold, reg)),
            (f"stack-{theme}.svg", build_stack(theme, bold)),
        ):
            (ASSETS / name).write_text(data)
            print(f"  {name:20s} {(ASSETS / name).stat().st_size:>7,} bytes")
    (ASSETS / "divider.svg").write_text(DIVIDER)
    print(f"  {'divider.svg':20s} {(ASSETS / 'divider.svg').stat().st_size:>7,} bytes")


if __name__ == "__main__":
    main()
