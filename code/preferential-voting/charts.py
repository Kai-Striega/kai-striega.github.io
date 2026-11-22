#!/usr/bin/env python3
"""Figures for the *Polarisation and the Preferential Vote* series.

Every number comes from the CSVs in ``data/``, which are copies of the outputs of
the R analysis behind the series. Nothing here recomputes the analysis: it only
reads the results and draws them as house-style SVGs (the same palette, font and
dark-mode block as the rest of the site) into ``static/images/preferential-voting``.

Standard library only:

    python3 code/preferential-voting/charts.py
"""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
IMAGES = HERE.parent.parent / "static" / "images" / "preferential-voting"

# The dark-palette <style> block shared verbatim across the site's diagrams, plus
# one rule for the independents' teal, which no earlier diagram used.
DARK_STYLE = """  <style>
    /* Dark palette. CSS beats presentation attributes, so the drawing below is
       untouched. Shared verbatim across the mechanical-sympathy diagrams;
       selectors that match nothing here are harmless. */
    @media (prefers-color-scheme: dark) {
      /* canvas and neutrals */
      [fill="#f7f7f5"] { fill: #1b212a }   [stroke="#f7f7f5"] { stroke: #1b212a }
      [fill="#ffffff"] { fill: #262e3a }
      [fill="#1d1d1b"] { fill: #e3e8ee }   [stroke="#1d1d1b"] { stroke: #e3e8ee }
      [fill="#5a5a55"] { fill: #ced6dd }   [stroke="#5a5a55"] { stroke: #ced6dd }
      [fill="#6a6a63"] { fill: #9ca4af }
      [fill="#8a8a82"] { fill: #868f9c }   [stroke="#8a8a82"] { stroke: #868f9c }
      [fill="#a9a9a1"] { fill: #566072 }   [stroke="#a9a9a1"] { stroke: #566072 }
      [fill="#e8e8e2"] { fill: #333d4b }
      [fill="#dcdcd6"] { fill: #2f3947 }
      [stroke="#e4e4de"] { stroke: #394454 }
      [stroke="#b9b9b2"] { stroke: #48566b }
      [stroke="#c4c4bc"] { stroke: #48566b }
      /* blue */
      [fill="#1f6feb"] { fill: #6ea8ff }   [stroke="#1f6feb"] { stroke: #6ea8ff }
      [stroke="#12408c"] { stroke: #3d6fbf }
      [fill="#e8effb"] { fill: #1c2942 }
      /* orange */
      [fill="#c2410c"] { fill: #f08a4b }   [stroke="#c2410c"] { stroke: #f08a4b }
      [stroke="#7d2a08"] { stroke: #b35a2a }
      [fill="#f9e9e2"], [fill="#f8ebe7"], [fill="#f4ece7"] { fill: #33241c }
      /* green */
      [fill="#2f6f4f"] { fill: #57b98a }
      [stroke="#1f4a35"] { stroke: #2f7a56 }
      [fill="#4a8f6a"] { fill: #6fc79b }
      [fill="#7aa88c"] { fill: #86b89f }
      [fill="#f0f6f2"], [fill="#e3f0e9"], [fill="#d6e8de"] { fill: #1a2c24 }
      /* purple */
      [fill="#6b3fa0"] { fill: #a77dff }   [stroke="#6b3fa0"] { stroke: #a77dff }
      [fill="#f0eefa"] { fill: #251f38 }
      /* terracotta */
      [fill="#b5705f"] { fill: #d0917f }   [stroke="#b5705f"] { stroke: #d0917f }
      [stroke="#7d4436"] { stroke: #a5654f }
      /* memory-hierarchy only */
      [fill="#f7f5ee"] { fill: #1f2229 }
      [fill="#b0a98f"] { fill: #a8a184 }
      [stroke="#6b6552"] { stroke: #8a8470 }
    }
    /* Teal, for independents: only this series uses it. */
    @media (prefers-color-scheme: dark) {
      [fill="#008080"] { fill: #3fb8b8 }   [stroke="#008080"] { stroke: #3fb8b8 }
    }
  </style>"""

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

CANVAS, INK, MUTED, GRID, AXIS, PALE = "#f7f7f5", "#1d1d1b", "#5a5a55", "#e4e4de", "#b9b9b2", "#e8e8e2"
GREY, MID = "#a9a9a1", "#8a8a82"
BLUE, ORANGE, GREEN, PURPLE, TERRA, TEAL = "#1f6feb", "#c2410c", "#2f6f4f", "#6b3fa0", "#b5705f", "#008080"

# Party colours: house palette, with Labor in terracotta (the palette has no red).
PARTY = {"Liberal": BLUE, "Coalition": BLUE, "Liberal / Coalition": BLUE, "Labor": TERRA, "Greens": GREEN,
         "Nationals": PURPLE, "One Nation": INK, "Independents": TEAL, "Other": GREY}


def read(name: str) -> list[dict]:
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x: str) -> float:
    return float(x) if x not in ("", "NA") else math.nan


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- #
# House-style SVG helpers                                                      #
# --------------------------------------------------------------------------- #

class Svg:
    def __init__(self, w: int, h: int, title: str, subtitle: str, desc: str):
        self.w, self.h = w, h
        self.s = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
            DARK_STYLE,
            f'<title id="t">{esc(title)}</title>',
            f'<desc id="d">{esc(desc)}</desc>',
            f'<rect width="{w}" height="{h}" fill="{CANVAS}"/>',
            f'<g font-family="{FONT}">',
            f'<text x="24" y="30" font-size="15" font-weight="600" fill="{INK}">{esc(title)}</text>',
            f'<text x="24" y="50" font-size="12" fill="{MUTED}">{esc(subtitle)}</text>',
        ]

    def text(self, x, y, s, size=11, fill=MUTED, anchor="start", weight="normal", rotate=None):
        t = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ""
        self.s.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                      f'font-weight="{weight}"{t}>{esc(str(s))}</text>')

    def line(self, x1, y1, x2, y2, stroke=GRID, width=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                      f'stroke-width="{width}"{d}/>')

    def rect(self, x, y, w, h, fill, stroke=None):
        st = f' stroke="{stroke}"' if stroke else ""
        self.s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" fill="{fill}"{st}/>')

    def circle(self, x, y, r, fill, stroke=None, width=1.5):
        st = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        self.s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"{st}/>')

    def polyline(self, pts, stroke, width=2.0):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.s.append(f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{width}" '
                      f'stroke-linejoin="round" stroke-linecap="round"/>')

    def legend(self, x, y, items, gap=22):
        """items: (label, colour, kind) with kind 'line' or 'box'."""
        for label, colour, kind in items:
            if kind == "line":
                self.line(x, y - 4, x + 18, y - 4, stroke=colour, width=2.5)
                self.circle(x + 9, y - 4, 3.5, colour)
            else:
                self.rect(x, y - 10, 12, 12, colour)
            self.text(x + 24, y, label, size=12, fill=INK)
            x += 24 + 6.6 * len(label) + gap

    def save(self, name: str):
        self.s.append("</g></svg>")
        IMAGES.mkdir(parents=True, exist_ok=True)
        (IMAGES / name).write_text("\n".join(self.s) + "\n", encoding="utf-8")
        print("wrote", name)


class Panel:
    """A plotting region with linear (or log) scales and recessive axes."""

    def __init__(self, svg: Svg, x0, y0, w, h, xlim, ylim, xlog=False):
        self.svg, self.x0, self.y0, self.w, self.h = svg, x0, y0, w, h
        self.xlim, self.ylim, self.xlog = xlim, ylim, xlog

    def sx(self, v):
        a, b = self.xlim
        if self.xlog:
            v, a, b = math.log(v), math.log(a), math.log(b)
        return self.x0 + (v - a) / (b - a) * self.w

    def sy(self, v):
        a, b = self.ylim
        return self.y0 + self.h - (v - a) / (b - a) * self.h

    def ygrid(self, ticks, fmt: Callable[[float], str] = str, labels=True):
        for t in ticks:
            y = self.sy(t)
            self.svg.line(self.x0, y, self.x0 + self.w, y, stroke=GRID)
            if labels:
                self.svg.text(self.x0 - 8, y + 4, fmt(t), size=10, anchor="end")

    def xgrid(self, ticks, fmt: Callable[[float], str] = str, labels=True):
        for t in ticks:
            x = self.sx(t)
            self.svg.line(x, self.y0, x, self.y0 + self.h, stroke=GRID)
            if labels:
                self.svg.text(x, self.y0 + self.h + 16, fmt(t), size=10, anchor="middle")

    def baseline(self):
        self.svg.line(self.x0, self.y0 + self.h, self.x0 + self.w, self.y0 + self.h, stroke=AXIS)

    def xlabel(self, s):
        self.svg.text(self.x0 + self.w / 2, self.y0 + self.h + 34, s, size=11, anchor="middle")

    def ylabel(self, s, dx=44):
        yc = self.y0 + self.h / 2
        self.svg.text(self.x0 - dx, yc, s, size=11, anchor="middle", rotate=-90)

    def heading(self, s):
        self.svg.text(self.x0, self.y0 - 10, s, size=12, fill=INK, weight="600")


def pct(v, d=0):
    return f"{100 * v:.{d}f}%"


def wmean(pairs):
    tw = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / tw


# --------------------------------------------------------------------------- #
# Post 0 and 1: rejection, not tribalism                                       #
# --------------------------------------------------------------------------- #

def fig_intro_trends():
    rows = [r for r in read("trends.csv") if r["weights"] == "weighted"]
    get = lambda m: sorted(((int(r["year"]), num(r["value"])) for r in rows if r["measure"] == m))
    gap, zero = get("major_gap"), get("rates_some_party_zero")
    svg = Svg(760, 330, "Not more partisan, but more rejecting",
              "Australian Election Study, 1993–2025 (weighted where the survey has weights)",
              "Two line charts. Left: the gap between how much Labor and Liberal partisans like their own party "
              f"and the other one, about {gap[0][1]:.1f} rating points in 1993 and {gap[-1][1]:.1f} in 2025, with no "
              f"upward trend. Right: the share of voters who give at least one party 0 out of 10, which fell from "
              f"{pct(zero[0][1])} in 1993 to {pct(min(v for _, v in zero))} in 2001 and rose to {pct(zero[-1][1])} in 2025.")
    years = [1993, 2004, 2016, 2025]
    for i, (series, head, ylim, ticks, fmt) in enumerate([
            (gap, "Partisan gap (rating points, 0–10 scale)", (0, 6), [0, 2, 4, 6], str),
            (zero, "Voters who rate some party 0", (0, 0.6), [0, 0.2, 0.4, 0.6], lambda t: pct(t))]):
        p = Panel(svg, 70 + i * 360, 90, 300, 190, (1992, 2026), ylim)
        p.heading(head); p.ygrid(ticks, fmt); p.xgrid(years, labels=True); p.baseline()
        pts = [(p.sx(x), p.sy(y)) for x, y in series]
        svg.polyline(pts, INK)
        for x, y in pts:
            svg.circle(x, y, 3.5, INK)
        if i == 1:
            for x, y in series:
                if x in (1993, 2001, 2025):
                    svg.text(p.sx(x), p.sy(y) - 10, pct(y), size=11, fill=INK, anchor="middle")
    svg.save("intro-trends.svg")


def fig_adjusted():
    rows = [r for r in read("regression.csv") if r["variant"] == "main" and r["measure"] == "adjusted"]
    parties = ["Liberal", "Labor", "Greens", "Nationals"]
    data = {p: sorted((int(r["year"]), num(r["value"]), num(r["lo"]), num(r["hi"])) for r in rows if r["party"] == p)
            for p in parties}
    lib, lab = dict((y, v) for y, v, _, _ in data["Liberal"]), dict((y, v) for y, v, _, _ in data["Labor"])
    below = sum(1 for y in lib if lib[y] < lab[y])
    svg = Svg(760, 380, "At the same distance, the Liberals are liked least",
              "Outsiders' rating of each party at the same left–right distance (adjusted rating), with 95% intervals",
              f"Line chart of adjusted ratings by party, 1996 to 2025. The Liberals sit below Labor in {below} of "
              f"{len(lib)} surveys, every one since 1998; in 1996 Labor was lower.")
    p = Panel(svg, 70, 110, 560, 220, (1994.5, 2026.5), (2, 5.5))
    p.ygrid([2, 3, 4, 5]); p.xgrid([1996, 2004, 2013, 2025]); p.baseline()
    p.ylabel("Adjusted rating (0–10)")
    for k, party in enumerate(parties):
        c, off = PARTY[party], (k - 1.5) * 0.25
        pts = [(p.sx(y + off), p.sy(v)) for y, v, _, _ in data[party]]
        svg.polyline(pts, c, 1.8)
        for (_, v, lo, hi), (x, yy) in zip(data[party], pts):
            svg.line(x, p.sy(lo), x, p.sy(hi), stroke=c, width=1.2)
            svg.circle(x, yy, 3.2, c)
    ends = sorted(((p.sy(data[q][-1][1]), q) for q in parties))
    placed = []
    for y, q in ends:                                   # push overlapping labels apart, keeping their order
        y = max(y, placed[-1][0] + 14) if placed else y
        placed.append((y, q))
    for y, q in placed:
        svg.text(p.sx(2025.6), y + 4, q, size=12, fill=PARTY[q])
    svg.legend(70, 84, [(q, PARTY[q], "line") for q in parties])
    svg.save("adjusted-ratings.svg")


def fig_one_nation():
    rows = [r for r in read("regression.csv") if r["variant"] == "with_onp" and r["measure"] == "adjusted"]
    parties = ["One Nation", "Liberal", "Nationals", "Greens", "Labor"]
    years = sorted({int(r["year"]) for r in rows})
    svg = Svg(760, 330, "One Nation was disliked far beyond its distance",
              "Adjusted rating at the same left–right distance, 1998–2004, the only surveys that asked about One Nation",
              "Three dot charts, one per survey (1998, 2001, 2004). In each, One Nation's adjusted rating sits well "
              "below every other party, with no overlap in the 95% intervals.")
    for i, yr in enumerate(years):
        p = Panel(svg, 120 + i * 215, 90, 175, 170, (0.5, 5.5), (0, len(parties)))
        p.heading(str(yr)); p.xgrid([1, 3, 5]); p.baseline()
        for j, party in enumerate(parties):
            r = next(r for r in rows if int(r["year"]) == yr and r["party"] == party)
            y = p.sy(len(parties) - j - 0.5)
            if i == 0:
                svg.text(p.x0 - 10, y + 4, party, size=11, fill=INK, anchor="end")
            svg.line(p.sx(num(r["lo"])), y, p.sx(num(r["hi"])), y, stroke=PARTY[party], width=1.6)
            svg.circle(p.sx(num(r["value"])), y, 4, PARTY[party])
    svg.text(380, 305, "Adjusted rating (0–10)", size=11, anchor="middle")
    svg.save("one-nation-adjusted.svg")


def fig_last_place():
    rows = [r for r in read("isolation_national.csv") if len(r["states"].split()) >= 3]
    rows.sort(key=lambda r: -num(r["last_vs_position_weighted"]))
    rows = rows[:8]
    rename = {"Pauline Hanson's One Nation": "One Nation", "Liberal / Coalition": "Liberal / Coalition"}
    svg = Svg(760, 360, "Who Senate voters put last, 2025",
              "Last places relative to what each party's ballot column alone would produce; 1× = no more than position explains",
              "Dot chart. Greens " + f"{num(rows[0]['last_vs_position_weighted']):.1f}×, " +
              ", ".join(f"{rename.get(r['party'], r['party'])} {num(r['last_vs_position_weighted']):.1f}×" for r in rows[1:]) +
              ". The parties standing in at least three states or territories; each weighted by its voters.")
    p = Panel(svg, 250, 80, 440, 230, (0, 4.6), (0, len(rows)))
    p.xgrid([0, 1, 2, 3, 4], fmt=lambda t: f"{t}×"); p.baseline()
    p.svg.line(p.sx(1), p.y0, p.sx(1), p.y0 + p.h, stroke=AXIS, width=1.5)
    for j, r in enumerate(rows):
        y, v = p.sy(len(rows) - j - 0.5), num(r["last_vs_position_weighted"])
        name = rename.get(r["party"], r["party"])
        svg.text(p.x0 - 10, y + 4, name, size=11, fill=INK, anchor="end")
        svg.line(p.sx(1), y, p.sx(v), y, stroke=GRID, width=2)
        svg.circle(p.sx(v), y, 4.5, INK)
        svg.text(p.sx(v) + 10, y + 4, f"{v:.1f}×", size=11, fill=INK)
    p.xlabel("Ranked last, relative to ballot position (each state or territory weighted by its voters)")
    svg.save("senate-last-place.svg")


# --------------------------------------------------------------------------- #
# Post 2: the centre squeeze                                                   #
# --------------------------------------------------------------------------- #

def fig_squeeze_margins():
    rows = [r for r in read("squeeze_contests.csv") if r["division"] != "(whole state)" and r["squeeze_margin"] not in ("", "NA")]
    years = sorted({int(r["year"]) for r in rows})
    n = len(rows)
    svg = Svg(760, 330, "No Condorcet winner was knocked out; a handful came close",
              "The Condorcet winner's lead over the weaker of the other two, with three groups left, every House division",
              f"Strip chart of {n} divisions across 2016, 2019, 2022 and 2025. No point is below zero, which would be "
              "a centre squeeze. The closest each year is labelled; the shaded band is the 10-point at-risk zone.")
    p = Panel(svg, 80, 80, 620, 200, (-2, 62), (0, len(years)))
    svg.rect(p.sx(0), p.y0, p.sx(10) - p.sx(0), p.h, PALE)
    p.xgrid([0, 10, 20, 30, 40, 50, 60]); p.baseline()
    rng = random.Random(1)
    for j, yr in enumerate(years):
        yc = p.sy(len(years) - j - 0.5)
        svg.text(p.x0 - 10, yc + 4, str(yr), size=11, fill=INK, anchor="end")
        ys = [r for r in rows if int(r["year"]) == yr]
        for r in ys:
            svg.circle(p.sx(100 * num(r["squeeze_margin"])), yc + rng.uniform(-14, 14), 2.2, MID)
        lo = min(ys, key=lambda r: num(r["squeeze_margin"]))
        svg.text(p.sx(100 * num(lo["squeeze_margin"])) + 4, yc - 18, f"{lo['division']} ({100 * num(lo['squeeze_margin']):.1f})", size=10, fill=INK)
    p.svg.line(p.sx(0), p.y0, p.sx(0), p.y0 + p.h, stroke=INK, width=1.2)
    p.xlabel("Condorcet winner's lead with three left (points)")
    svg.save("squeeze-margins.svg")


def fig_strategic():
    rows = [r for r in read("fptp_sensitivity.csv") if r["condorcet"]]
    xs = [i / 20 for i in range(21)]
    misses = []
    for x in xs:
        m = 0
        for r in rows:
            v1 = num(r["first1"]) + x * num(r["others_to1"]); v2 = num(r["first2"]) + x * num(r["others_to2"])
            v3 = (1 - x) * num(r["first3"])
            w = r["top1"] if v1 >= v2 and v1 >= v3 else (r["top2"] if v2 >= v3 else r["third"])
            m += w != r["condorcet"]
        misses.append(m)
    svg = Svg(760, 320, "Most first-past-the-post misses depend on voters not adapting",
              "Contests where first past the post would miss the Condorcet winner, if some third-party voters switched",
              f"Line chart. With no switching, first past the post misses the Condorcet winner in {misses[0]} contests; "
              f"if a quarter of third-party voters switch to the front-runner they prefer, {misses[5]}; at half, "
              f"{misses[10]}; if all do, {misses[-1]}.")
    p = Panel(svg, 80, 80, 600, 190, (0, 1), (0, max(misses) * 1.15))
    p.ygrid([0, 20, 40, 60, 80]); p.xgrid([0, 0.25, 0.5, 0.75, 1], fmt=lambda t: pct(t)); p.baseline()
    pts = [(p.sx(x), p.sy(m)) for x, m in zip(xs, misses)]
    svg.polyline(pts, INK)
    for (x, y), m, xv in zip(pts, misses, xs):
        svg.circle(x, y, 3, INK)
        if xv in (0, 0.25, 0.5, 1):
            svg.text(x + 6, y - 8, str(m), size=11, fill=INK)
    p.xlabel("Third-party voters who switch to their preferred front-runner")
    p.ylabel("Contests missed", dx=40)
    svg.save("fptp-strategic.svg")


def fig_nsw_trailing():
    rows = [r for r in read("nsw_contests.csv") if r["condorcet"] and r["condorcet_first_rank"] not in ("", "NA")
            and int(float(r["condorcet_first_rank"])) > 1]
    for r in rows:
        r["first"] = num(r["condorcet_first_share"])
        f = num(r["irv_final_share"])
        r["final"] = f if r["irv"] == r["condorcet"] else 1 - f
    rows.sort(key=lambda r: -r["first"])
    svg = Svg(760, 90 + 26 * len(rows) + 60, "Every trailing Condorcet winner came through on preferences",
              "NSW Legislative Assembly: Condorcet winner's first-preference share (hollow) and final share (filled)",
              f"Dumbbell chart of the {len(rows)} NSW contests, 2015 to 2023, where the Condorcet winner was not first "
              "on first preferences. Each starts between about 26% and 42% and finishes above 50%: it won every one.")
    p = Panel(svg, 180, 80, 520, 26 * len(rows), (20, 60), (0, len(rows)))
    p.xgrid([20, 30, 40, 50, 60], fmt=lambda t: f"{t}%"); p.baseline()
    p.svg.line(p.sx(50), p.y0, p.sx(50), p.y0 + p.h, stroke=AXIS, width=1.5)
    for j, r in enumerate(rows):
        y = p.sy(len(rows) - j - 0.5)
        svg.text(p.x0 - 10, y + 4, f"{r['district']} {r['year']}", size=11, fill=INK, anchor="end")
        svg.line(p.sx(100 * r["first"]), y, p.sx(100 * r["final"]), y, stroke=GREY, width=1.5)
        svg.circle(p.sx(100 * r["first"]), y, 4, CANVAS, stroke=MUTED)
        svg.circle(p.sx(100 * r["final"]), y, 4.5, INK)
    p.xlabel("Condorcet winner's share of the vote")
    svg.save("nsw-trailing.svg")


def fig_nsw_proxy():
    rows = [r for r in read("nsw_proxy.csv") if r["alp_v_coalition_error"] not in ("", "NA")]
    def group(s):
        return {"ALP": "Labor", "LIB/NAT": "Coalition", "": "Open seat"}.get(s, "Other")
    order = ["Coalition", "Labor", "Open seat", "Other"]
    by = defaultdict(list)
    for r in rows:
        by[group(r["sitting_party"])].append(100 * num(r["alp_v_coalition_error"]))
    mean = sum(sum(v) for v in by.values()) / sum(len(v) for v in by.values())
    svg = Svg(760, 310, "The Senate-style stand-in misses most where an MP has a personal vote",
              "NSW 2023: stand-in minus real Labor share of the Labor v Coalition head-to-head, by who held the seat",
              f"Strip chart of {len(rows)} districts. Seats held by the Coalition all sit to the right of zero, by up to "
              f"{max(by['Coalition']):.0f} points: the stand-in shows Labor stronger than the real ballots. Seats held by "
              f"Labor straddle zero. The average lean is {mean:.1f} points towards Labor.")
    p = Panel(svg, 120, 80, 580, 180, (-8, 18), (0, len(order)))
    p.xgrid([-5, 0, 5, 10, 15]); p.baseline()
    p.svg.line(p.sx(0), p.y0, p.sx(0), p.y0 + p.h, stroke=INK, width=1.2)
    rng = random.Random(1)
    for j, g in enumerate(order):
        yc = p.sy(len(order) - j - 0.5)
        svg.text(p.x0 - 10, yc + 4, g, size=11, fill=INK, anchor="end")
        for v in by[g]:
            svg.circle(p.sx(v), yc + rng.uniform(-12, 12), 3, MID)
    p.xlabel("Stand-in error, points (positive = stand-in favours Labor)")
    svg.save("nsw-proxy.svg")


# --------------------------------------------------------------------------- #
# Post 3: who keeps One Nation out                                             #
# --------------------------------------------------------------------------- #

def fig_transfers():
    rows = read("transfer_model.csv")
    groups = ["One Nation", "Trumpet of Patriots", "Palmer / UAP", "Katter", "Greens", "Independents", "Coalition"]
    colour = {"Trumpet of Patriots": ORANGE, "Palmer / UAP": PURPLE, "Katter": MID}
    sources = ["From Labor and Greens candidates", "From minor parties and independents"]
    svg = Svg(760, 340, "One Nation draws preferences from the right, and gets few from the left",
              "Share of an excluded candidate's votes each group receives, vs a Labor candidate of the same size (log scale)",
              "Two dot charts with 95% intervals. From Labor and Greens candidates, One Nation receives about a quarter "
              "of what a same-size Labor candidate would; from minor parties and independents, almost three times as much.")
    for i, src in enumerate(sources):
        p = Panel(svg, 190 + i * 290, 90, 250, 190, (0.08, 6), (0, len(groups)), xlog=True)
        p.heading(src.replace(" candidates", "")); p.xgrid([0.1, 0.25, 1, 4], fmt=lambda t: f"{t:g}×"); p.baseline()
        p.svg.line(p.sx(1), p.y0, p.sx(1), p.y0 + p.h, stroke=AXIS, width=1.5)
        for j, g in enumerate(groups):
            r = next((r for r in rows if r["source"] == src and r["group"] == g), None)
            y = p.sy(len(groups) - j - 0.5)
            if i == 0:
                svg.text(p.x0 - 10, y + 4, g, size=11, fill=INK, anchor="end")
            if r is None or r["value"] in ("", "NA"):
                continue
            c = colour.get(g, PARTY.get(g, INK))
            svg.line(p.sx(max(num(r["lo"]), 0.08)), y, p.sx(min(num(r["hi"]), 6)), y, stroke=c, width=1.6)
            svg.circle(p.sx(num(r["value"])), y, 4, c)
    svg.text(475, 315, "Transferred votes received, relative to a same-size Labor candidate", size=11, anchor="middle")
    svg.save("transfers.svg")


def bloc_series(kind="all"):
    rows = [r for r in read("bloc_preferences.csv") if r["ballots_read"] == kind]
    out = defaultdict(list)
    for r in rows:
        out[(r["voters"], int(r["year"]))].append((num(r["share"]), num(r["ballots"])))
    return {k: wmean(v) for k, v in out.items()}


def fig_blocs():
    s = bloc_series()
    years = [2016, 2019, 2022, 2025]
    blocs = [("Coalition voters: One Nation above Labor", "Coalition voters", BLUE),
             ("Labor voters: One Nation above the Coalition", "Labor voters", TERRA),
             ("Greens voters: One Nation above the Coalition", "Greens voters", GREEN)]
    svg = Svg(760, 360, "The Coalition vote has swung behind One Nation",
              "Senate ballots: share of each bloc ranking One Nation above the rival major party",
              f"Line chart. Coalition voters ranking One Nation above Labor: {pct(s[('Coalition voters', 2016)])} in 2016, "
              f"{pct(s[('Coalition voters', 2025)])} in 2025. Labor voters ranking One Nation above the Coalition fell from "
              f"{pct(s[('Labor voters', 2016)])} to {pct(s[('Labor voters', 2025)])}; Greens voters were never above "
              f"{pct(max(s[('Greens voters', y)] for y in years))}.")
    p = Panel(svg, 70, 110, 560, 200, (2015, 2026), (0, 1))
    p.ygrid([0, 0.25, 0.5, 0.75, 1], fmt=pct); p.xgrid(years); p.baseline()
    p.svg.line(p.x0, p.sy(0.5), p.x0 + p.w, p.sy(0.5), stroke=AXIS, width=1.5)
    for label, key, c in blocs:
        pts = [(p.sx(y), p.sy(s[(key, y)])) for y in years]
        svg.polyline(pts, c)
        for x, y in pts:
            svg.circle(x, y, 3.5, c)
        svg.text(pts[-1][0] + 10, pts[-1][1] + 4, pct(s[(key, 2025)]), size=12, fill=c)
    for k, (label, key, c) in enumerate(blocs):
        svg.legend(70, 70 + 16 * k, [(label, c, "line")])
    svg.save("blocs.svg")


def fig_btl():
    rows = [r for r in read("bloc_preferences.csv") if r["voters"] == "Coalition voters"]
    w = {(r["year"], r["state"]): num(r["ballots"]) for r in rows if r["ballots_read"] == "all"}
    out = defaultdict(list)
    for r in rows:
        if r["ballots_read"] != "all":
            out[(r["ballots_read"], int(r["year"]))].append((num(r["share"]), w[(r["year"], r["state"])]))
    s = {k: wmean(v) for k, v in out.items()}
    years = [2016, 2019, 2022, 2025]
    svg = Svg(760, 340, "Coalition voters' own rankings shifted too",
              "Coalition voters ranking One Nation above Labor, by how they filled in the Senate ballot",
              f"Line chart. Above the line, where many voters copy a party card: {pct(s[('ATL', 2016)])} in 2016, "
              f"{pct(s[('ATL', 2025)])} in 2025. Below the line, where voters number their own order: "
              f"{pct(s[('BTL', 2016)])} to {pct(s[('BTL', 2025)])}. Each state or territory is weighted by all its "
              "Coalition voters. The 2019 below-the-line point is inflated by a NSW campaign for below-the-line votes.")
    p = Panel(svg, 70, 100, 560, 190, (2015, 2026), (0.3, 0.85))
    p.ygrid([0.3, 0.4, 0.5, 0.6, 0.7, 0.8], fmt=pct); p.xgrid(years); p.baseline()
    for kind, label, c, hollow in [("ATL", "Above the line (often a party card)", BLUE, False),
                                   ("BTL", "Below the line (own order)", INK, True)]:
        pts = [(p.sx(y), p.sy(s[(kind, y)])) for y in years]
        svg.polyline(pts, c)
        for (x, y), yr in zip(pts, years):
            svg.circle(x, y, 4, CANVAS if hollow else c, stroke=c if hollow else None)
            if yr in (2016, 2025):
                svg.text(x, y - 10, pct(s[(kind, yr)]), size=11, fill=INK, anchor="middle")
    svg.legend(70, 78, [("Above the line (often a party card)", BLUE, "line"), ("Below the line (own order)", INK, "line")])
    svg.save("btl.svg")


# --------------------------------------------------------------------------- #
# Post 4: seats won from behind                                                #
# --------------------------------------------------------------------------- #

def fig_overturns():
    rows = read("house_overturns.csv")
    years = sorted({int(r["year"]) for r in rows})
    kinds = ["Labor", "Independents", "Greens", "Other"]
    kind = lambda g: g if g in kinds[:3] else "Other"
    counts = {(y, k): sum(1 for r in rows if int(r["year"]) == y and kind(r["winner_group"]) == k) for y in years for k in kinds}
    totals = {y: sum(counts[(y, k)] for k in kinds) for y in years}
    svg = Svg(760, 340, "About one seat in twelve is won from behind",
              "House divisions won by a candidate who trailed on first preferences, by winner",
              f"Stacked bar chart of {len(rows)} seats won from behind, 2004 to 2025: " +
              ", ".join(f"{totals[y]} in {y}" for y in years) + ". Labor won most; independents won 7 in 2022 and 5 in 2025.")
    p = Panel(svg, 70, 100, 620, 190, (0, len(years)), (0, 18))
    p.ygrid([0, 5, 10, 15]); p.baseline()
    for j, y in enumerate(years):
        x0, bw, acc = p.sx(j + 0.2), p.sx(0.6) - p.sx(0), 0
        for k in kinds:
            c = counts[(y, k)]
            if c:
                svg.rect(x0, p.sy(acc + c), bw, p.sy(acc) - p.sy(acc + c) - 1.5, PARTY[k])
            acc += c
        svg.text(x0 + bw / 2, p.sy(acc) - 6, str(acc), size=11, fill=INK, anchor="middle")
        svg.text(x0 + bw / 2, p.y0 + p.h + 16, str(y), size=10, anchor="middle")
    svg.legend(70, 78, [(k, PARTY[k], "box") for k in kinds])
    svg.save("overturns.svg")


def fig_overturn_sources():
    rows = read("house_overturn_flows.csv")
    sources = ["Greens", "Labor", "Coalition", "Independents", "One Nation", "Other"]
    panels = [("Labor", "Labor's 78 comebacks"), ("Independents", "Independents' 15 comebacks")]
    shares = {}
    for g, _ in panels:
        sel = [r for r in rows if r["winner_group"] == g]
        tot = sum(num(r["net"]) for r in sel)
        for s in sources:
            src = [r for r in sel if r["source"] == s]
            shares[(g, s)] = sum(num(r["net"]) for r in src) / tot if src else None
    svg = Svg(760, 330, "Whose preferences carried the comebacks",
              "Share of the winners' net preference gain from each source; negative = net flow to the leader",
              "Two bar charts. In Labor's comebacks, Greens preferences supplied "
              f"{pct(shares[('Labor', 'Greens')])} of the net gain, more than all of it, because One Nation and other "
              "minor-party preferences flowed back to the leader. In independents' comebacks, Labor supplied "
              f"{pct(shares[('Independents', 'Labor')])} and the Greens {pct(shares[('Independents', 'Greens')])}.")
    for i, (g, head) in enumerate(panels):
        p = Panel(svg, 140 + i * 310, 90, 260, 180, (-0.2, 1.2), (0, len(sources)))
        p.heading(head); p.xgrid([0, 0.5, 1], fmt=pct); p.baseline()
        p.svg.line(p.sx(0), p.y0, p.sx(0), p.y0 + p.h, stroke=INK, width=1.2)
        for j, s in enumerate(sources):
            y, v = p.sy(len(sources) - j - 0.5), shares[(g, s)]
            if i == 0:
                svg.text(p.x0 - 10, y + 4, s, size=11, fill=INK, anchor="end")
            if v is None:                       # e.g. no Labor preferences in a Labor comeback
                svg.text(p.sx(0) + 6, y + 4, "not applicable", size=10, fill=MUTED)
                continue
            x0, x1 = sorted((p.sx(0), p.sx(v)))
            svg.rect(x0, y - 9, x1 - x0, 18, PARTY.get(s, GREY))
            svg.text((p.sx(v) + 6) if v >= 0 else (p.sx(v) - 6), y + 4, f"{100 * v:+.0f}%", size=10, fill=INK,
                     anchor="start" if v >= 0 else "end")
    svg.save("overturn-sources.svg")


# --------------------------------------------------------------------------- #
# Appendices                                                                   #
# --------------------------------------------------------------------------- #

def fig_position_effects():
    rows = read("position_effects.csv")
    cols = ["first column", "second column", "second-last column", "last column"]
    val = {}
    for r in rows:
        col, size = r["column"].rsplit(", ", 1)
        val[(col, size.replace(" party", ""))] = num(r["odds_multiplier"])
    svg = Svg(760, 320, "Edge columns attract last places, mostly for minor parties",
              "How much a ballot column multiplies the odds of being ranked last, relative to a middle column",
              "Grouped bar chart. For minor parties: " +
              ", ".join(f"{c} {val[(c, 'minor')]:.1f}×" for c in cols) + ". Major-party effects are smaller and rest on few cases.")
    p = Panel(svg, 70, 100, 620, 170, (0, len(cols)), (0, math.ceil(max(val.values()))))
    p.ygrid(range(0, math.ceil(max(val.values())) + 1), fmt=lambda t: f"{t}×"); p.baseline()
    p.svg.line(p.x0, p.sy(1), p.x0 + p.w, p.sy(1), stroke=AXIS, width=1.5)
    for j, c in enumerate(cols):
        for k, (size, colour) in enumerate([("minor", BLUE), ("major", GREY)]):
            v = val.get((c, size))
            if v is None:
                continue
            x = p.sx(j + 0.18 + 0.32 * k)
            bw = p.sx(0.3) - p.sx(0)
            svg.rect(x, p.sy(v), bw, p.sy(0) - p.sy(v), colour)
            svg.text(x + bw / 2, p.sy(v) - 5, f"{v:.1f}×", size=10, fill=INK, anchor="middle")
        svg.text(p.sx(j + 0.5), p.y0 + p.h + 16, c, size=11, anchor="middle")
    svg.legend(70, 78, [("Minor party (under 5% in that state)", BLUE, "box"), ("Major party", GREY, "box")])
    svg.save("position-effects.svg")


def fig_bootstrap():
    reps = read("bootstrap_replicates.csv")
    summ = {r["design"]: r for r in read("bootstrap_summary.csv")}
    real = num(summ["booth"]["squeeze_margin"])
    svg = Svg(760, 400, "Resampling single ballots makes the seat look far too predictable",
              "Macnamara 2022: Labor's margin with three left in 1,000 reshuffled seats, two ways",
              f"Two histograms. Resampling whole collection points, the margin ranges from "
              f"{100 * num(summ['booth']['margin_p2.5']):.1f} to {100 * num(summ['booth']['margin_p97.5']):.1f} points and "
              f"{pct(num(summ['booth']['squeeze']), 1)} of replicates are squeezes. Resampling single ballots, it ranges from "
              f"{100 * num(summ['ballot']['margin_p2.5']):.1f} to {100 * num(summ['ballot']['margin_p97.5']):.1f} points, with "
              f"{pct(num(summ['ballot']['squeeze']), 1)} squeezes.")
    bins = [i / 10 for i in range(-25, 36)]          # points, 0.1 wide
    for i, (design, head) in enumerate([("booth", "Resampling collection points (booths, pre-poll centres, batches)"),
                                        ("ballot", "Resampling single ballots")]):
        m = [100 * num(r["margin"]) for r in reps if r["design"] == design and r["margin"] not in ("", "NA")]
        counts = [sum(1 for v in m if a <= v < a + 0.1) for a in bins]
        p = Panel(svg, 70, 90 + i * 150, 620, 100, (-2.5, 3.6), (0, 160))
        p.heading(head)
        svg.rect(p.sx(-2.5), p.y0, p.sx(0) - p.sx(-2.5), p.h, PALE)
        p.ygrid([0, 50, 100, 150]); p.xgrid([-2, -1, 0, 1, 2, 3], labels=(i == 1)); p.baseline()
        bw = p.sx(0.1) - p.sx(0)
        for a, c in zip(bins, counts):
            if c:
                svg.rect(p.sx(a) + 0.5, p.sy(c), bw - 1, p.sy(0) - p.sy(c), MID)
        p.svg.line(p.sx(100 * real), p.y0, p.sx(100 * real), p.y0 + p.h, stroke=INK, width=1.5)
    svg.text(380, 385, "Labor's margin with three left (points); left of zero, Labor is excluded", size=11, anchor="middle")
    svg.save("bootstrap-macnamara.svg")


if __name__ == "__main__":
    for f in [fig_intro_trends, fig_adjusted, fig_one_nation, fig_last_place, fig_squeeze_margins, fig_strategic,
              fig_nsw_trailing, fig_nsw_proxy, fig_transfers, fig_blocs, fig_btl, fig_overturns,
              fig_overturn_sources, fig_position_effects, fig_bootstrap]:
        f()
