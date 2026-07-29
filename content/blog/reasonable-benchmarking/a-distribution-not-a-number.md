+++
title = 'A Distribution, Not a Number'
date = 2026-07-29T09:30:00+10:00
draft = true
tags = ['performance', 'rust', 'benchmarking', 'statistics']
+++

[Last time][part1] I timed a function that returns the same answer every run and got a different runtime every
time, and argued that the honest object to reason about is not a number but a *distribution*: the whole spread
of times, produced by every source of variation at once. This post is about looking at that spread properly:
what shape it takes, and which single number you are entitled to read off it.

I'll warn you up front that the last question doesn't have a settled answer. People who benchmark for a living
disagree about it, for good reasons, and by the end I want you to understand the disagreement rather than
pretend it away.

## Look at the shape first

Here is a real one. I benchmarked a pointer-chasing loop (walk a random cycle through an array far too big for
cache, so every step is a cache miss and the loop runs at the mercy of memory latency) and kept all five
hundred of criterion's per-iteration samples. This is the picture:

![A histogram of five hundred per-iteration times with a fitted normal curve that does not match, beside a normal QQ-plot whose points bend away from the straight reference line](/images/benchmark-distribution.svg "benchmark-distribution")

Two ways of looking at the same five hundred numbers. On the left, a histogram with the best-fit normal curve
drawn over it. The bars pile up against a hard floor on the left (nothing runs faster than the memory system
allows) and trail off to the right in a long tail of slower runs. The curve, which is what you're implicitly
assuming every time you write "mean ± standard deviation", sits over the top fitting almost none of it. On the
right, the same data as a normal QQ-plot: if the sample were Gaussian the points would lie on the dashed line,
and instead they bend away from it at both ends, the signature of a skewed, heavy-tailed distribution.

This shape is not special to my machine or my loop. It's what benchmark timings *look like*, and the reason is
already in the last post: the sources of noise are one-sided. Nothing makes a run faster than the ideal (the
code can't execute in negative time) while a hundred things can make it slower, each adding a little more to
the right tail. Daniel Lemire has [the same picture][lemire] for memory-bound code and reaches the same
conclusion.

## Why the normality test is the wrong tool

The statistically-trained instinct here is to reach for a test. Shapiro-Wilk is the usual one, and run against
this sample it returns a p-value of `2.7e-15`: normality overwhelmingly rejected. Case closed?

I want to argue that the test is close to useless here, for two reasons. The first is that with a few hundred
samples it will reject *almost any* real benchmark, because real benchmarks are never exactly normal, and a
sensitive enough test on a large enough sample will always find the departure. It's answering a yes/no question
whose answer you already knew was "no". The second, more important, is that rejecting normality tells you what
your data *isn't* and gives you no idea what to *do*. A gate that only ever says "stop" is not helping you across
the road.

There's a sharper version of the trap in my *other* benchmark. I also timed a tiny sum-of-squares loop that
fits entirely in cache, the compute-bound cousin of the one above. Its middle is beautifully tight: minimum
5.19 µs, median 5.49 µs, they agree to a couple of percent. But its skewness is **+15**, because a handful of
the five hundred runs are enormous: a scheduler interrupt or a migration to an efficiency core landing in the
middle of a measurement. Those are *perturbing events*, and they are not really part of the distribution you're
trying to measure at all; they're a different process leaking into your sample. A normality test lumps them in
and rejects. It can't tell you the thing you actually want to know, which is that the loop is stable and got hit
by something external a handful of times.

So what do you do instead? There are two honest answers, and they point in opposite directions.

One is to stop assuming normality and use methods that don't need it. Compare whole distributions with
non-parametric tools: Lemire reaches for the [Kolmogorov-Smirnov statistic and the Wasserstein distance][lemire];
Andrey Akinshin, who maintains BenchmarkDotNet, has [built a whole toolkit][akinshin] around detecting the
multimodality these distributions often hide. Criterion, as we'll see, quietly does the non-parametric thing by
default. The other answer is to *engineer* the normality you want: Curtsinger and Berger's [Stabilizer][stabilizer],
which I mentioned last time, randomises code and data layout so that the layout noise (the single biggest
confound) is re-drawn on every run, at which point the central limit theorem does you a favour and the residual
*is* Gaussian, and honest analysis of variance becomes available again. Both start from the same admission: the
raw sample is not a bell curve, and pretending otherwise is where the lie gets in.

## Which number do you read off?

Grant that we have a distribution and we've looked at it. At some point you still have to collapse it to a
number, to put in a table or a regression-detector. Which one?

Here are three candidates for each of my two workloads, straight off the samples:

| workload | minimum | mean | median | slope (OLS) |
|:---------|--------:|-----:|-------:|------------:|
| sum-of-squares (in cache) | 5.19 µs | 5.52 µs | 5.49 µs | 5.53 µs |
| pointer-chase (memory-bound) | 339 µs | 348 µs | 348 µs | n/a |

They disagree: modestly here, by three to six percent, and by much more on noisier workloads. That gap is not
rounding. It is three different answers to the question "what is this benchmark's time", and each has a serious
argument behind it.

**The minimum.** The fastest run you saw is the one least polluted by one-sided noise, so it's the best estimate
of what the machine is actually *capable* of, a "frictionless" model of the code. Jiahao Chen and Jarrett Revels
make this case rigorously in [*Robust Benchmarking in Noisy Environments*][chen], deriving how many iterations to
batch so the minimum converges to the true floor; it's the estimator behind Julia's BenchmarkTools, and Python's
`timeit` reports it too. Its weakness is the flip side of its strength: by construction it ignores the tail, so
it tells you nothing about what a run will *typically* cost when the interrupts and the throttling are part of
real life.

**The mean, with a confidence interval.** If you want to model the time you'll actually experience, including the
perturbations, the mean is the honest summary, provided you say how uncertain it is. This is [criterion's][crit]
approach, and it's more careful than a bare average: criterion runs the workload for a range of iteration counts,
fits a line through *total time against iteration count* by ordinary least squares (the slope of that line is
the per-iteration estimate, with the fixed measurement overhead falling out as the intercept) and then puts a
**bootstrap** confidence interval around it by resampling, assuming no particular distribution. Tomas Kalibera
and Richard Jones give the fuller statistical recipe, including how to report a difference as an [effect-size
confidence interval][kalibera]. The mean's weakness is that it's dragged around by exactly the outliers the
minimum discards: one interrupt in five hundred runs moves it.

**The median.** The robust middle ground: unmoved by a handful of monstrous outliers, still a measure of central
tendency rather than a floor. It's what [divan][divan] leads with.

There is no universally right choice, and anyone who tells you otherwise is selling something. The minimum
answers "what is this code capable of?"; the mean and median answer "what will I actually get?". Pick the one
that matches the question you're asking. Whichever it is, report enough around it (an interval, or the
minimum *and* the mean side by side) that a reader can see how noisy the underlying sample was.

## The tools have already chosen for you

Which is worth knowing because your benchmarking library has made this choice on your behalf, and it's good to
know which one. Run the same two workloads under criterion and under divan and you can watch their philosophies
diverge:

Criterion, reporting its OLS estimate with the bootstrap interval in brackets, and counting the outliers it
found:

```
compute_bound/sum_of_squares
                time:   [5.4869 µs 5.5302 µs 5.5961 µs]
Found 22 outliers among 500 measurements (4.40%)
memory_bound/pointer_chase
                time:   [348.10 µs 348.49 µs 348.90 µs]
Found 16 outliers among 500 measurements (3.20%)
```

Divan, the same two workloads, leading with the median and laying the fastest, slowest and mean around it:

```
                    fastest   │ slowest   │ median    │ mean
├─ compute_bound    5.374 µs  │ 6.708 µs  │ 5.416 µs  │ 5.426 µs
╰─ memory_bound     323 µs    │ 5.171 ms  │ 324.9 µs  │ 337.6 µs
```

Look at the memory-bound row in divan's table and the whole argument of this post is sitting in one line: the
median is 325 µs, the mean is 338 µs, and the slowest sample is **5.17 milliseconds**, fifteen times the
median, a single perturbing event that the mean can feel and the median shrugs off.



Criterion leads with the OLS-slope estimate and a bootstrap confidence interval, and, the part I like most,
flags the outliers explicitly rather than hiding them, so the perturbing events show up as a line in the report
instead of silently inflating your mean. Divan leads with the median and shows you the minimum, mean and maximum
around it, so the spread is right there in the table. Neither is wrong. They are answering slightly different
questions, and now you know which.

A last, practical layer: some quick sanity checks worth running on any sample before you trust its summary. If
the minimum and the mean are far apart, the tail is heavy and your mean is doing you a disservice; Lemire
suggests watching exactly that [gap][lemire]. `pyperf` [warns][pyperf] when the standard deviation exceeds ten
percent of the mean, when the minimum or maximum is more than fifty percent off it, or when the whole thing ran
in under a millisecond and is really measuring timer resolution. These are conventions, not laws (my in-cache
loop sits right on the ten-percent line, and that's a nudge to look closer, not a verdict) but they're cheap,
and they catch the measurement that has quietly gone wrong.

## Where this leaves us

We can now take one benchmark and say something defensible about it: here is its distribution, here is its shape,
here is the summary I've chosen and why, and here is how noisy the sample under it was. That is a real
improvement over reading a single number off the screen.

But almost nobody benchmarks to characterise one thing in isolation. You benchmark to make a *comparison* (this
version against that one, my change against the baseline) and a comparison of two noisy distributions is its own
problem, with its own ways of going wrong. Is a five percent difference real or is it two samples from the same
spread? And once you're comparing not one benchmark but a whole suite of them, how do you avoid the trap of
running so many comparisons that some come up "significant" purely by chance? That's the [last post][part3].

Everything here (both workloads, the criterion and divan harnesses, and the Python that drew the figure and ran
the tests) is [in the repo for this blog][code].

[part1]: https://kaistriega.com/blog/reasonable-benchmarking/one-number-is-a-lie/
[part3]: https://kaistriega.com/blog/reasonable-benchmarking/is-it-actually-faster/
[lemire]: https://lemire.me/blog/2023/04/06/are-your-memory-bound-benchmarking-timings-normally-distributed/
[akinshin]: https://aakinshin.net/tags/statistics/
[stabilizer]: https://people.cs.umass.edu/~emery/pubs/stabilizer-asplos13.pdf
[chen]: https://arxiv.org/abs/1608.04295
[crit]: https://bheisler.github.io/criterion.rs/book/analysis.html
[kalibera]: https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf
[divan]: https://nikolaivazquez.com/blog/divan/
[pyperf]: https://pyperf.readthedocs.io/en/latest/system.html
[code]: https://github.com/Kai-Striega/kai-striega.github.io/tree/main/code/reasonable-benchmarking
