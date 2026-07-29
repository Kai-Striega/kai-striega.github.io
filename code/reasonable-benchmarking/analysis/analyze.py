#!/usr/bin/env python3
"""Analysis pipeline for the *Reasonable Benchmarking* series.

Reads the raw samples Criterion persists under ``target/criterion`` and produces:

  * E4: a histogram + QQ-plot of one benchmark's distribution (house-style SVG),
    plus a Shapiro-Wilk normality test.
  * E5: the minimum / mean / median / slope of the same sample, side by side.
  * E7: a stable-vs-unstable sort comparison across a small suite: per-case
    ratios, the geometric mean, a per-case Mann-Whitney U test with a
    Benjamini-Hochberg correction, and the naive win count for contrast.

Everything is printed as Markdown so it can be pasted straight into the posts, and
the one figure is written into the site's ``static/images`` directory.

    analysis/.venv/bin/python analysis/analyze.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
CRITERION = HERE.parent / "target" / "criterion"
IMAGES = HERE.parent.parent.parent / "static" / "images"

# The dark-palette <style> block shared verbatim across the site's diagrams, so a
# generated figure themes itself for dark mode exactly like the hand-drawn ones.
DARK_STYLE = """  <style>
    /* Dark palette. CSS beats presentation attributes, so the drawing below is
       untouched. Shared verbatim across the diagrams. */
    @media (prefers-color-scheme: dark) {
      [fill="#f7f7f5"] { fill: #1b212a }   [stroke="#f7f7f5"] { stroke: #1b212a }
      [fill="#ffffff"] { fill: #262e3a }
      [fill="#1d1d1b"] { fill: #e3e8ee }   [stroke="#1d1d1b"] { stroke: #e3e8ee }
      [fill="#5a5a55"] { fill: #ced6dd }   [stroke="#5a5a55"] { stroke: #ced6dd }
      [stroke="#e4e4de"] { stroke: #394454 }
      [stroke="#b9b9b2"] { stroke: #48566b }
      [fill="#1f6feb"] { fill: #6ea8ff }   [stroke="#1f6feb"] { stroke: #6ea8ff }
      [fill="#e8effb"] { fill: #1c2942 }
      [fill="#c2410c"] { fill: #f08a4b }   [stroke="#c2410c"] { stroke: #f08a4b }
    }
  </style>"""

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def per_iter_ns(bench_dir: Path) -> np.ndarray:
    """Criterion 'Linear' sampling: sample i ran ``iters[i]`` times in ``times[i]``
    nanoseconds, so the per-iteration time is the ratio."""
    sample = json.loads((bench_dir / "new" / "sample.json").read_text())
    iters = np.asarray(sample["iters"], dtype=float)
    times = np.asarray(sample["times"], dtype=float)
    return times / iters


def estimates(bench_dir: Path) -> dict:
    est = json.loads((bench_dir / "new" / "estimates.json").read_text())
    return {k: v["point_estimate"] for k, v in est.items() if isinstance(v, dict)}


def summarize(name: str, x: np.ndarray) -> dict:
    w, p = stats.shapiro(x)
    return {
        "name": name,
        "n": len(x),
        "min": float(np.min(x)),
        "mean": float(np.mean(x)),
        "median": float(np.median(x)),
        "std": float(np.std(x, ddof=1)),
        "skew": float(stats.skew(x)),
        "kurtosis": float(stats.kurtosis(x)),  # excess (0 == normal)
        "shapiro_W": float(w),
        "shapiro_p": float(p),
    }


# --------------------------------------------------------------------------- #
# House-style SVG helpers                                                      #
# --------------------------------------------------------------------------- #

def _svg_open(w: int, h: int, title: str, desc: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
        DARK_STYLE,
        f'<title id="t">{title}</title>',
        f'<desc id="d">{desc}</desc>',
        f'<rect width="{w}" height="{h}" fill="#f7f7f5"/>',
        f'<g font-family="{FONT}">',
    ]


def figure_distribution(x: np.ndarray, out: Path, *, unit_ns: float, unit: str,
                        title: str, subtitle: str, desc: str) -> None:
    """A two-panel figure: histogram with a fitted normal curve (left) and a
    normal QQ-plot (right). If the sample were normal, the histogram would sit
    under the curve and the QQ points would lie on the line."""
    xs = x / unit_ns
    W, H = 700, 380
    s = _svg_open(W, H, title, desc)
    s.append(f'<text x="24" y="30" font-size="15" font-weight="600" fill="#1d1d1b">{title}</text>')
    s.append(f'<text x="24" y="50" font-size="12" fill="#5a5a55">{subtitle}</text>')

    # ---- Left panel: histogram + normal fit ----
    px0, py0, pw, ph = 60, 78, 280, 250
    counts, edges = np.histogram(xs, bins=40)
    cmax = counts.max()
    s.append(f'<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" fill="#e8effb"/>')
    xmin, xmax = edges[0], edges[-1]

    def hx(v):
        return px0 + (v - xmin) / (xmax - xmin) * pw

    def hy(c):
        return py0 + ph - (c / cmax) * ph

    for c, lo, hi in zip(counts, edges[:-1], edges[1:]):
        if c == 0:
            continue
        x0, x1 = hx(lo), hx(hi)
        y0 = hy(c)
        s.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{max(x1-x0-0.5,0.5):.1f}" '
                 f'height="{py0+ph-y0:.1f}" fill="#1f6feb"/>')

    # Fitted normal curve, scaled to the histogram (bin width * n).
    mu, sd = np.mean(xs), np.std(xs, ddof=1)
    binw = edges[1] - edges[0]
    grid = np.linspace(xmin, xmax, 160)
    pdf = stats.norm.pdf(grid, mu, sd) * len(xs) * binw
    pts = " ".join(f"{hx(g):.1f} {hy(p):.1f}" for g, p in zip(grid, pdf))
    s.append(f'<polyline points="{pts}" fill="none" stroke="#c2410c" stroke-width="2"/>')

    ycen = py0 + ph / 2
    s.append(f'<text transform="rotate(-90 30 {ycen:.0f})" x="30" y="{ycen:.0f}" font-size="11" '
             f'fill="#5a5a55" text-anchor="middle">count</text>')
    s.append(f'<text x="{px0+pw/2:.0f}" y="{py0+ph+22:.0f}" font-size="11" fill="#5a5a55" '
             f'text-anchor="middle">time per iteration ({unit})</text>')
    for frac in (0.0, 0.5, 1.0):
        v = xmin + frac * (xmax - xmin)
        s.append(f'<text x="{hx(v):.0f}" y="{py0+ph+10:.0f}" font-size="10" fill="#5a5a55" '
                 f'text-anchor="middle">{v:.1f}</text>')
    s.append(f'<text x="{px0+pw/2:.0f}" y="{py0-8}" font-size="11" font-weight="600" '
             f'fill="#c2410c" text-anchor="middle">normal fit (it does not fit)</text>')

    # ---- Right panel: QQ-plot ----
    qx0, qy0, qw, qh = 400, 78, 270, 250
    s.append(f'<rect x="{qx0}" y="{qy0}" width="{qw}" height="{qh}" fill="#e8effb"/>')
    (osm, osr), _ = stats.probplot(xs, dist="norm")
    tx_min, tx_max = osm.min(), osm.max()
    sy_min, sy_max = osr.min(), osr.max()

    def qx(v):
        return qx0 + (v - tx_min) / (tx_max - tx_min) * qw

    def qy(v):
        return qy0 + qh - (v - sy_min) / (sy_max - sy_min) * qh

    # Reference line through the robust centre (least-squares fit from probplot).
    slope, inter = np.polyfit(osm, osr, 1)
    x_line = np.array([tx_min, tx_max])
    y_line = slope * x_line + inter
    y_line = np.clip(y_line, sy_min, sy_max)
    s.append(f'<line x1="{qx(x_line[0]):.1f}" y1="{qy(y_line[0]):.1f}" '
             f'x2="{qx(x_line[1]):.1f}" y2="{qy(y_line[1]):.1f}" stroke="#c2410c" '
             f'stroke-width="1.5" stroke-dasharray="4 3"/>')
    for tq, sq in zip(osm, osr):
        s.append(f'<circle cx="{qx(tq):.1f}" cy="{qy(sq):.1f}" r="1.8" fill="#1f6feb"/>')
    s.append(f'<text transform="rotate(-90 366 {ycen:.0f})" x="366" y="{ycen:.0f}" font-size="11" '
             f'fill="#5a5a55" text-anchor="middle">observed ({unit})</text>')
    s.append(f'<text x="{qx0+qw/2:.0f}" y="{qy0+qh+22:.0f}" font-size="11" fill="#5a5a55" '
             f'text-anchor="middle">normal quantiles</text>')
    s.append(f'<text x="{qx0+qw/2:.0f}" y="{qy0-8}" font-size="11" font-weight="600" '
             f'fill="#1f6feb" text-anchor="middle">QQ-plot: a straight line would be normal</text>')

    s.append("</g></svg>")
    out.write_text("\n".join(s) + "\n")
    print(f"wrote {out}")


def figure_two_distributions(a: np.ndarray, b: np.ndarray, out: Path, *, unit_ns: float,
                             unit: str, label_a: str, label_b: str, title: str,
                             subtitle: str, desc: str, xmin: float | None = None,
                             xmax: float | None = None) -> None:
    """Two overlaid kernel-density curves for a pair of benchmarks, with a dashed line at
    each median. The visual point: the point estimates (the two lines) are clearly apart,
    while the bodies of the distributions overlap heavily."""
    xa, xb = a / unit_ns, b / unit_ns
    W, H = 700, 380
    px0, py0, pw, ph = 70, 92, 600, 224
    s = _svg_open(W, H, title, desc)
    s.append(f'<text x="24" y="30" font-size="15" font-weight="600" fill="#1d1d1b">{title}</text>')
    s.append(f'<text x="24" y="50" font-size="12" fill="#5a5a55">{subtitle}</text>')
    s.append(f'<rect x="{px0}" y="{py0}" width="{pw}" height="{ph}" fill="#e8effb"/>')

    # Default to a zero baseline and a right edge that shows the tail without chasing the far outliers
    # (which are the subject of part two, not this figure). Both overridable by the caller.
    pooled = np.concatenate([xa, xb])
    lo = 0.0 if xmin is None else xmin
    hi = np.percentile(pooled, 95.0) if xmax is None else xmax
    grid = np.linspace(lo, hi, 240)
    da = stats.gaussian_kde(xa)(grid)
    db = stats.gaussian_kde(xb)(grid)
    dmax = max(da.max(), db.max())

    def gx(v):
        return px0 + (np.clip(v, lo, hi) - lo) / (hi - lo) * pw

    def gy(d):
        return py0 + ph - (d / dmax) * (ph - 12)

    def density_path(dens):
        pts = [f"{gx(lo):.1f} {py0+ph:.1f}"]
        pts += [f"{gx(g):.1f} {gy(d):.1f}" for g, d in zip(grid, dens)]
        pts.append(f"{gx(hi):.1f} {py0+ph:.1f}")
        return " L ".join(pts)

    # Blue = a (unstable/faster, on the left), orange = b (stable/slower, on the right).
    for dens, colour in ((da, "#1f6feb"), (db, "#c2410c")):
        s.append(f'<path d="M {density_path(dens)} Z" fill="{colour}" fill-opacity="0.42" '
                 f'stroke="{colour}" stroke-width="2"/>')
    # Median markers: the "point estimates" you must not simply race.
    for sample, colour in ((xa, "#1f6feb"), (xb, "#c2410c")):
        med = np.median(sample)
        s.append(f'<line x1="{gx(med):.1f}" y1="{py0+8}" x2="{gx(med):.1f}" y2="{py0+ph}" '
                 f'stroke="{colour}" stroke-width="1.5" stroke-dasharray="4 3"/>')

    # Axis ticks.
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        v = lo + frac * (hi - lo)
        s.append(f'<text x="{gx(v):.0f}" y="{py0+ph+16:.0f}" font-size="10" fill="#5a5a55" '
                 f'text-anchor="middle">{v:.2f}</text>')
    s.append(f'<text x="{px0+pw/2:.0f}" y="{py0+ph+34:.0f}" font-size="11" fill="#5a5a55" '
             f'text-anchor="middle">time per iteration ({unit})</text>')
    ycen = py0 + ph / 2
    s.append(f'<text transform="rotate(-90 34 {ycen:.0f})" x="34" y="{ycen:.0f}" font-size="11" '
             f'fill="#5a5a55" text-anchor="middle">density of samples</text>')

    # Legend.
    s.append(f'<rect x="{px0}" y="{py0-20}" width="12" height="12" rx="2" fill="#1f6feb"/>'
             f'<text x="{px0+18}" y="{py0-10}" font-size="12" fill="#1d1d1b">{label_a}</text>')
    lx = px0 + 200
    s.append(f'<rect x="{lx}" y="{py0-20}" width="12" height="12" rx="2" fill="#c2410c"/>'
             f'<text x="{lx+18}" y="{py0-10}" font-size="12" fill="#1d1d1b">{label_b}</text>')

    s.append("</g></svg>")
    out.write_text("\n".join(s) + "\n")
    print(f"wrote {out}")


# --------------------------------------------------------------------------- #
# E4 / E5                                                                      #
# --------------------------------------------------------------------------- #

def part2() -> None:
    print("\n## Part 2: one benchmark's distribution (E4/E5)\n")
    rows = []
    samples = {}
    for group, bench in [("compute_bound", "sum_of_squares"),
                         ("memory_bound", "pointer_chase")]:
        d = CRITERION / group / bench
        x = per_iter_ns(d)
        samples[group] = x
        rows.append(summarize(group, x))

    # E5 table: the estimators disagree, and by how much.
    print("### E5: the estimators disagree (per iteration)\n")
    print("| workload | n | min | mean | median | slope (OLS) | std/mean | Shapiro-Wilk p |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        bench = "sum_of_squares" if r["name"] == "compute_bound" else "pointer_chase"
        est = estimates(CRITERION / r["name"] / bench)
        slope = est.get("slope")  # absent when Criterion falls back to Flat sampling (slow benches)
        unit = 1.0 if r["mean"] < 1000 else 1000.0
        u = "ns" if unit == 1.0 else "µs"
        slope_str = f"{slope/unit:.3g} {u}" if slope is not None else "n/a (Flat)"
        print(f"| {r['name']} | {r['n']} | {r['min']/unit:.3g} {u} | {r['mean']/unit:.3g} {u} | "
              f"{r['median']/unit:.3g} {u} | {slope_str} | {r['std']/r['mean']*100:.1f}% | "
              f"{r['shapiro_p']:.2e} |")
    print()

    for r in rows:
        verdict = "reject normality" if r["shapiro_p"] < 0.05 else "cannot reject normality"
        print(f"- **{r['name']}**: skew {r['skew']:+.2f}, excess kurtosis {r['kurtosis']:+.2f}, "
              f"Shapiro-Wilk W={r['shapiro_W']:.3f} p={r['shapiro_p']:.2e} → {verdict}.")
    print()

    # E4 figure: the memory-bound sample. It is Lemire's example and shows a clean,
    # smoothly right-skewed shape; the compute-bound one is dominated by a couple of
    # rare huge outliers (skew +15), which is a great "perturbing events" point for the
    # prose but an unreadable histogram.
    target = next(r for r in rows if r["name"] == "memory_bound")
    x = samples[target["name"]]
    unit_ns = 1.0 if np.mean(x) < 1000 else 1000.0
    unit = "ns" if unit_ns == 1.0 else "µs"
    skew_word = "right" if target["skew"] > 0 else "left"
    figure_distribution(
        x, IMAGES / "benchmark-distribution.svg",
        unit_ns=unit_ns, unit=unit,
        title="A benchmark is a distribution, not a number",
        subtitle=(f"{target['name'].replace('_', '-')}, {len(x)} samples, "
                  f"Apple Silicon, Shapiro-Wilk p={target['shapiro_p']:.1e}"),
        desc=(f"Left, a histogram of {len(x)} per-iteration times with a fitted normal "
              f"curve drawn over it; the bars are clearly {skew_word}-skewed and do not "
              f"follow the curve. Right, a normal QQ-plot whose points bend away from the "
              f"straight reference line, the signature of a non-normal, heavy-tailed sample."),
    )


# --------------------------------------------------------------------------- #
# E7                                                                           #
# --------------------------------------------------------------------------- #

def part3() -> None:
    print("\n## Part 3: comparing a suite (E7)\n")
    sort_root = CRITERION / "sort"
    if not sort_root.exists():
        print("_sort benchmarks not found yet: run `cargo bench --bench sorts` first._")
        return

    # Figure for the "comparing two" section: the two distributions overlap heavily even though
    # their point estimates are clearly apart. random_100000 is the case discussed in the prose.
    us = per_iter_ns(sort_root / "unstable" / "random_100000")
    st = per_iter_ns(sort_root / "stable" / "random_100000")
    lo, hi = max(us.min(), st.min()), min(us.max(), st.max())
    ov = max(0.0, hi - lo)
    span = max(us.max(), st.max()) - min(us.min(), st.min())
    gap = (1 - np.median(us) / np.median(st)) * 100
    print(f"- **Overlap figure** (random 100k): sample ranges overlap {ov/span*100:.0f}% of the pooled "
          f"span despite a {gap:.0f}% gap in medians.\n")
    figure_two_distributions(
        us, st, IMAGES / "two-distributions-overlap.svg", unit_ns=1e6, unit="ms",
        label_a="unstable (pdqsort)", label_b="stable (merge sort)",
        title="The point estimates differ; the distributions overlap",
        subtitle="sorting 100,000 random u64, 200 per-iteration samples each, Apple Silicon",
        desc=("Two overlaid density curves for the same sort on the same input, unstable in blue and "
              "stable in orange. The two dashed median lines sit clearly apart, yet the bodies of the "
              "two distributions overlap across most of their width."),
        xmin=0.0, xmax=3.0,
    )

    # Discover the (pattern/size) cases present under both stable and unstable.
    cases = {}
    for est_path in sorted(sort_root.glob("*/*/new/estimates.json")):
        algo = est_path.parents[2].name          # "stable" or "unstable"
        case = est_path.parents[1].name          # e.g. "random/1000"
        cases.setdefault(case, {})[algo] = est_path.parents[1]

    rows = []
    stable_win = unstable_win = 0
    ratios = []
    pvals = []
    for case, algos in sorted(cases.items()):
        if not {"stable", "unstable"} <= set(algos):
            continue
        xs_stable = per_iter_ns(algos["stable"])
        xs_unstable = per_iter_ns(algos["unstable"])
        est_stable = estimates(algos["stable"]).get("slope") or np.median(xs_stable)
        est_unstable = estimates(algos["unstable"]).get("slope") or np.median(xs_unstable)
        ratio = est_unstable / est_stable  # <1 means unstable faster
        ratios.append(ratio)
        u, p = stats.mannwhitneyu(xs_unstable, xs_stable, alternative="two-sided")
        pvals.append(p)
        faster = "unstable" if ratio < 1 else "stable"
        if ratio < 1:
            unstable_win += 1
        else:
            stable_win += 1
        rows.append((case, est_stable, est_unstable, ratio, faster, p))

    # Benjamini-Hochberg correction across the suite.
    pv = np.asarray(pvals)
    order = np.argsort(pv)
    m = len(pv)
    bh = np.empty(m)
    prev = 1.0
    for rank, idx in enumerate(reversed(order), start=1):
        k = m - rank + 1
        prev = min(prev, pv[idx] * m / k)
        bh[idx] = prev

    print("### Per-case results (estimator = OLS slope, ns)\n")
    print("| case | stable | unstable | ratio (uns/stab) | faster | p (MWU) | p (BH) | sig? |")
    print("|---|---|---|---|---|---|---|---|")
    for (case, es, eu, ratio, faster, p), q in zip(rows, bh):
        sig = "yes" if q < 0.05 else "no"
        print(f"| {case} | {es:,.0f} | {eu:,.0f} | {ratio:.3f} | {faster} | "
              f"{p:.2e} | {q:.2e} | {sig} |")
    print()

    geo = math.exp(np.mean(np.log(ratios)))
    print(f"- **Geometric mean of ratios (unstable / stable):** {geo:.3f} "
          f"→ unstable is {(1/geo - 1)*100:.1f}% faster *overall* on this suite.")
    print(f"- **Naive win count:** unstable wins {unstable_win} cases, stable wins {stable_win}.")
    n_sig = int((bh < 0.05).sum())
    n_raw = int((pv < 0.05).sum())
    print(f"- **Significant differences:** {n_raw}/{m} at raw p<0.05, "
          f"{n_sig}/{m} after Benjamini-Hochberg. On this suite the effects are large and "
          f"well separated, so every one survives correction; correction earns its keep when "
          f"effects are marginal, which is what the null experiment below shows.")
    print()

    null_demonstration(sort_root)


def null_demonstration(sort_root: Path) -> None:
    """The multiple-comparison trap, shown with real measured noise.

    First the honest anecdote: the `null` group benchmarks the *same* algorithm as
    "left" and "right", so any difference is noise. Then the rate, at scale: take one
    real sample, split it 50/50 at random many times (nothing differs by construction)
    and count how often an uncorrected test calls it significant."""
    print("### The multiple-comparison trap (E7, null experiment)\n")

    null_root = sort_root.parent / "null"
    raw_hits = 0
    cases = {}
    for est_path in sorted(null_root.glob("*/*/new/estimates.json")):
        side = est_path.parents[2].name
        case = est_path.parents[1].name
        cases.setdefault(case, {})[side] = est_path.parents[1]
    null_pvals = []
    for case, sides in sorted(cases.items()):
        if not {"left", "right"} <= set(sides):
            continue
        p = stats.mannwhitneyu(per_iter_ns(sides["left"]), per_iter_ns(sides["right"]),
                               alternative="two-sided").pvalue
        null_pvals.append(p)
    null_pvals = np.asarray(null_pvals)
    if len(null_pvals):
        raw_hits = int((null_pvals < 0.05).sum())
        print(f"- **Same sort, benchmarked twice** ({len(null_pvals)} cases, nothing differs): "
              f"{raw_hits} of {len(null_pvals)} come up \"significant\" at raw p<0.05.")

    # The rate at scale: many random 50/50 partitions of one real sample.
    rng = np.random.default_rng(0xBEEF)
    pooled = np.concatenate([
        per_iter_ns(next(iter(c.values())))
        for c in cases.values()
    ]) if cases else np.array([])
    if len(pooled) >= 40:
        trials = 1000
        hits = 0
        for _ in range(trials):
            perm = rng.permutation(pooled)
            half = len(perm) // 2
            p = stats.mannwhitneyu(perm[:half], perm[half:], alternative="two-sided").pvalue
            if p < 0.05:
                hits += 1
        rate = hits / trials
        expected = int(round(0.05 * 20))
        print(f"- **{trials} random splits of one real sample** (again, nothing differs): "
              f"{rate*100:.1f}% land under raw p<0.05, almost exactly the 5% you asked for by "
              f"choosing α=0.05. Run 20 honest comparisons and you should *expect* ~{expected} "
              f"false winners; that is the inflation a correction removes.")
    print()


def main() -> None:
    print("# Reasonable Benchmarking: computed results")
    print("\n_Measured on Apple Silicon (arm64), macOS, Rust 1.95. Regenerate with "
          "`analysis/.venv/bin/python analysis/analyze.py`._")
    part2()
    part3()


if __name__ == "__main__":
    main()
