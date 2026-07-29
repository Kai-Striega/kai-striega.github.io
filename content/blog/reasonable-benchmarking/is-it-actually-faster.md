+++
title = 'Is It Actually Faster?'
date = 2026-07-29T10:00:00+10:00
draft = true
tags = ['performance', 'rust', 'benchmarking', 'statistics']
+++

The first two posts were about measuring one thing. [Part one][part1] argued that a single timing is untrustworthy;
[part two][part2] argued that one benchmark is really a distribution, and showed how to summarise it honestly.
But almost nobody benchmarks to admire one number in isolation. You benchmark to answer a *comparison*: is my
change faster than the baseline? Is this data structure faster than that one? This post is about that question,
which turns out to be two questions wearing a trench coat (comparing two things, and comparing many) each with
its own way of fooling you.

I'll use a concrete pair throughout: Rust's two standard-library sorts. `sort` is a stable, adaptive merge sort;
`sort_unstable` is a pattern-defeating quicksort. Which is faster? Let's be careful about what that even means.

## Comparing two: don't race the point estimates

Here's the naive comparison. On a hundred thousand random `u64`s, the stable sort's per-element estimate is
2,285,568 ns and the unstable sort's is 1,667,686 ns. Unstable is faster. Done?

We should already be suspicious, because part two taught us those two numbers are each a summary of a whole
distribution, and two distributions can overlap heavily even when their point estimates differ. This pair is a
textbook case:

![Two overlaid density curves for the same sort on the same input, unstable in blue and stable in orange, with two dashed median lines sitting clearly apart while the bodies of the two distributions overlap across most of their width](/images/two-distributions-overlap.svg "two-distributions-overlap")

The two dashed lines are the point estimates, a clear 27% apart. But look at the bodies: they overlap across
about **two-thirds** of the samples' combined range. Draw one run of each at random and you would, fairly often,
watch the "slower" sort beat the "faster" one. Comparing the two point estimates and stopping there is exactly
the mistake this picture is warning about. The right question is not "is one number bigger" but "if I drew these
two samples from the same underlying process, how surprised would I be to see a gap this large?" That's a
hypothesis test, and because part two also taught us these samples are not normal, it should be a
*non-parametric* one, not the t-test that assumes a bell curve. The Mann-Whitney U test asks exactly that
question without assuming a distribution, and here it returns a p-value of `7e-61`. The individual runs overlap
wildly, but with two hundred samples the *centres* are pinned down far more precisely than any single run, and
the gap between them is not two draws from one spread. It's real.

You get this for free, as it happens. Criterion's built-in comparison (the thing that prints `Performance has
improved` when you re-run a benchmark) does a bootstrap version of the same idea: it [resamples][crit] both the
old and new measurements many times, builds up a distribution of the difference, and reports how much of that
distribution sits on the wrong side of zero, along with a confidence interval on the change itself. Reporting the
*interval*, not just "faster", is the part worth insisting on: "11% faster, 95% CI [9%, 13%]" is a claim a reader
can check; "11% faster" is a number that might be noise. Kalibera and Jones make the [full case][kalibera] for
reporting a difference as an effect-size confidence interval, and it is the single habit that most improves a
benchmarking write-up.

## One benchmark is one facet

So unstable wins on random data. Let me now run the *same* comparison across a small suite, four input shapes
(random, already-sorted, reversed, few distinct values) at two sizes, because a single input only ever
illuminates one corner of a system's behaviour.

| input | stable (ns) | unstable (ns) | unstable is |
|:------|------------:|--------------:|:------------|
| random, 100k     | 2,285,568 | 1,667,686 | 27% faster |
| random, 1k       | 10,353    | 8,960     | 16% faster |
| few-unique, 100k | 417,413   | 328,583   | 27% faster |
| sorted, 100k     | 54,033    | 52,628    | 2.6% faster |
| reversed, 100k   | 79,046    | 77,160    | 2.4% faster |

Unstable wins every case, but look at the *margins*. On random data it's 27% faster; on already-sorted or
reversed data it's barely two percent, because both algorithms are adaptive and a pre-ordered input is the easy
case for each. If you had benchmarked only random input you'd walk away saying "unstable is a quarter faster";
if you'd benchmarked only sorted input you'd say "they're basically the same". Both would be true, and both would
be a misleading summary of the whole. Which is the entire reason to run a suite, and it immediately creates two
new ways to lie.

## Trap one: how you average the suite

You want one headline number: overall, how much faster is unstable? The obvious move is to average the per-case
ratios. The obvious move is wrong, and it's wrong in a way that has been [known since 1986][fleming].

Take the arithmetic mean of the unstable/stable ratios across my suite and you get **0.875**: "unstable takes
87.5% of the time, so it's 12.5% faster". But now flip the question and average the stable/unstable ratios: you
get **1.153**: "stable takes 115.3% of the time". Those two should be reciprocals of each other. They aren't:
0.875 × 1.153 = 1.009, not 1. The arithmetic mean of ratios gives you a different answer about the size of the
gap depending on which implementation you arbitrarily chose as the denominator. That is not a rounding artefact;
it is a property of the arithmetic mean, and it means any headline built on it is partly an artefact of your
choice of baseline.

The geometric mean (multiply the ratios and take the nth root) does not have this defect. Its value here is
**0.871**, and its reciprocal is **1.148**, which is *exactly* the geometric mean of the flipped ratios. The gap
is the same size whichever way you point it. Fleming and Wallace's paper, titled with admirable directness *How
Not to Lie With Statistics: The Correct Way to Summarize Benchmark Results*, is the canonical reference, and it's
why SPEC and the Computer Language Benchmarks Game report geometric means. So: on this suite, unstable is **14.8%
faster overall**, and I can say that without it depending on which sort I called the baseline.

## Trap two: running lots of comparisons

Every row in that table came with a p-value, and every one was significant even after correction. That is not
luck; the effects are large and the samples clean, so nothing marginal is going on. But it lets me make the more
dangerous point using a case where the honest answer is *no difference at all*.

Suppose you compare not two implementations but twenty, or you run one comparison across twenty benchmarks. Each
test has, by construction, a five-percent chance of calling a difference significant when there is none: that's
what choosing α = 0.05 *means*. Run twenty such tests and you should expect one false winner even if every
implementation is identical. Run enough benchmarks and you will always find something "significant" to put in
your changelog.

I measured this rather than asserting it. Take one benchmark's five hundred real samples (a single
distribution, so any "difference" within it is definitionally noise), split it in half at random, and run the
test. Do that a thousand times:

- **5.3%** of those random splits come up significant at p < 0.05. Almost exactly the five percent you asked for.
  Twenty honest comparisons, expect one false winner.

And a sharper version, closer to what people actually do. I benchmarked the *same* unstable sort against itself
(labelled "left" and "right", identical code) across all eight suite cases:

- **3 of 8** came up "significant" at p < 0.05.

Three out of eight is well above the five percent the random splits gave, and the gap is instructive: because I
ran "left" to completion and *then* "right", the machine had time to drift between them (warm up, throttle,
migrate cores) so the same code genuinely ran at two slightly different speeds. That's an argument for
interleaving your measurements rather than running all of A then all of B, which is exactly what criterion's
comparison mode does when it re-measures the baseline alongside the new code.

The fix for the counting problem is a multiple-comparison correction. The Benjamini-Hochberg procedure is the
gentle, standard one: it adjusts the p-values for the number of tests so that the *rate* of false discoveries
stays controlled. On my real sort suite it changes nothing, because every effect was overwhelming, but that is
the point of a correction, that it costs you nothing when your results are solid and saves you from yourself when
they aren't. The failure mode it prevents, cherry-picking the benchmarks that happened to cross the line, is
the most common way an honest-looking performance claim turns out to be noise.

## What the whole series was about

Three posts, one argument, built up a scale at a time. A single measurement is a lie, because the optimiser, the
layout, the machine's power state and the warm-up transient all move it and none of them are your code. One
benchmark is not a number but a distribution, usually skewed and heavy-tailed, and which summary you read off it
(minimum, mean, median) is a real choice about whether you're modelling the ideal machine or the messy real one.
And a comparison is a statistical claim: two distributions need a test, not a race; a suite needs a geometric
mean, not an arithmetic one; and many comparisons need a correction, not a change of luck.

If you take one habit from all of it, take this: **report the distribution, not the summary.** An interval
instead of a point, the minimum *and* the mean, the spread across the suite instead of the headline. Nearly every
benchmarking mistake I've shown you (the deleted loop, the layout confound, the dragged mean, the cherry-picked
win) survives precisely because a single number hides the thing that would have given it away. The number is
where the lie lives. The distribution is where the truth is, and it was never hiding; you just have to agree to
look at it.

Everything here (the sorts, the null experiments, the statistics and the figure from part two) is [in the repo
for this blog][code]. Run it on your machine. Your numbers will be different, and after three posts you know
exactly why.

[part1]: https://kaistriega.com/blog/reasonable-benchmarking/one-number-is-a-lie/
[part2]: https://kaistriega.com/blog/reasonable-benchmarking/a-distribution-not-a-number/
[crit]: https://bheisler.github.io/criterion.rs/book/analysis.html
[kalibera]: https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf
[fleming]: https://doi.org/10.1145/5666.5673
[code]: https://github.com/Kai-Striega/kai-striega.github.io/tree/main/code/reasonable-benchmarking
