+++
title = 'One Number Is a Lie'
date = 2026-07-29T09:00:00+10:00
draft = true
tags = ['performance', 'rust', 'benchmarking', 'statistics']
+++

I have a function. Given the same input it returns the same number every single time, on every machine, forever.
I am going to time it three times, and get three different answers.

```rust
pub fn sum_of_squares(values: &[u64]) -> u64 {
    values
        .iter()
        .fold(0u64, |acc, &x| acc.wrapping_add(x.wrapping_mul(x)))
}
```

Here is that function, timed over a fixed ten-thousand-element array, a hundred thousand times a round, three
rounds:

```
answer (identical every run): 11251846665439727927

round 1:    602.421ms  ( 6024.21 ns / iteration)
round 2:    547.283ms  ( 5472.83 ns / iteration)
round 3:    544.821ms  ( 5448.21 ns / iteration)
```

Same code, same input, the same nineteen-digit answer each time. The runtime moved by ten percent between the
first round and the last. Which round was the *real* time?

That question is the reason this series exists. A computer will reproduce an *answer* bit for bit; that's the
whole point of a computer. It will not reproduce a *runtime*, because the runtime isn't a property of your
program alone; it's a property of your program tangled up with a cache, a branch predictor, a scheduler, a
clock that changes speed, and every other process on the machine. Timing is hard not because clocks are
imprecise but because the thing you are measuring genuinely varies.

Over three posts I want to take that seriously and build up, from the smallest unit to the largest, a way of
benchmarking that doesn't lie to you. This first post is about the smallest unit: **a single measurement, and
why you should not trust one.** Everything is measured on the machine I'm writing this on (an Apple Silicon
laptop) and, as with everything in this series, your numbers will be different. That is rather the point.

## A measurement is an experiment

The frame that fixes all of this is to stop thinking of a benchmark as a *number you read off* and start
thinking of it as an *experiment you run*. An experiment has a hypothesis, it has conditions you hold fixed, it
has conditions you vary on purpose, and (the part people skip) it has confounds you have to rule out. The
three numbers above aren't a precision problem to be averaged away. They're an experiment whose conditions I
failed to control, telling me so.

So before we can compare anything to anything, we have to get *one* measurement to mean what we think it means.
There are three ways it can betray you, and all three show up before you've written a line of statistics.

## The compiler deletes your benchmark

Start with the most alarming one, because it is unique to compiled languages and it is silent. Here is the same
workload, timed twice: once ignoring the result, and once feeding the result through `std::hint::black_box`, an
optimisation barrier that forces the compiler to treat a value as used.

```
no black_box :     83.000ns  (   0.000 ns/iter)
black_box    :       5.458s  (5457.803 ns/iter)
```

The first line is not a fast benchmark. `sum_of_squares` is pure, so if nothing downstream uses its result, the
optimiser is entitled to conclude the call has no observable effect, delete it, delete the now-empty loop body,
and delete the loop. Eighty-three nanoseconds is the cost of asking the clock what time it is, twice. My program
reported an apparent throughput of *nine hundred million gigabytes a second* for a computation that no longer
existed.

In Python, the noise in a measurement almost always *adds* work you didn't ask for: the interpreter, the garbage
collector, another process waking up. In a compiled language the sharpest pitfall runs the other way: the
optimiser *removes* work you did ask for. `black_box` is the fix, but it is a blunt one, and matklad has
[written up][matklad] the ways it can still mislead you. The habit to build is simpler than the tool: every
time you write a benchmark, confirm that the thing you are measuring is a thing that still happens.[^1]

Notice, too, that once the barrier is in place the per-iteration time, 5457 ns, lands right on top of the
three numbers we started with. The real measurement is consistent with itself. It's the fictional one that was
suspiciously round.

## The things that move the number aren't the ones you'd reach for

Say we've defeated the optimiser and we're timing real work. Surely *now* the number is a property of the code?

Here is the minimum time per iteration (the fastest we ever saw, which is the most stable floor a workload has,
since noise can only ever slow a run down) under four conditions. Same source. Same answer. I've changed only
things that have no business affecting arithmetic:

| condition | min ns/iter |
|:----------|------------:|
| baseline release build | 5420.0 |
| + 8&nbsp;KB of extra environment variables | 5420.1 |
| compiled with `-C target-cpu=native` | 5420.0 |
| compiled with `codegen-units = 1` | 5420.1 |

Nothing. The floor is identical to four significant figures, because for a loop this simple LLVM emits the same
vectorised inner loop every time, and none of these knobs touches it. That is worth knowing on its own: a lot of
what people fiddle with changes nothing.

But the reason I show you a *null* result here is that the literature is full of cases where these exact knobs
move everything. Mytkowicz and colleagues, in a paper with the wonderful title [*Producing Wrong Data Without
Doing Anything Obviously Wrong!*][mytkowicz], showed that changing the size of your Unix environment (which
shifts where the stack sits in memory) or changing the link order of your object files could swing measured
performance by margins large enough to reverse a paper's conclusions. Curtsinger and Berger's [*Stabilizer*][stabilizer]
drove the point home: once you account for the noise created by code and data *layout* alone, the measured
difference between `-O2` and `-O3` across the SPEC benchmark suite is statistically indistinguishable from zero.

My loop is too small and too vectorisable to show that: the effect lives in code that branches and calls and
chases pointers, where layout decides what shares a cache line and how the branch predictor's tables get
indexed. The point stands regardless: **incidental facts about the build and the environment can dominate the
number, and they are exactly the facts you don't think to write down.**

There is one incidental I *can* show you moving the number, and it isn't a compiler flag at all. Run that same
binary enough times and the minimum occasionally drops from 5420 ns to around **4500 ns**, thirteen percent
faster, depending on which core the scheduler picked and what clock speed it happened to be running at. The
machine's own power and scheduling state moved the floor further than any of the flags did.

## Warmup is the machine reaching a steady state

That thirteen-percent jump is the same phenomenon behind the very first table, where round one was the slowest.
The first iterations of any benchmark run on a cold machine: caches that don't yet hold your data, a branch
predictor that hasn't seen your branches, a CPU still ramping from an idle clock toward its boost frequency and
not yet throttling from the heat that boost produces. Every one of those is a piece of *state* that your loop
has to drive to a steady value before the number it produces means anything.

This is why every serious benchmarking tool runs a warm-up phase and throws the early samples away, and it's the
seam where this series meets the [Mechanical Sympathy][ms] one: warm-up is just "wait for the caches and the
predictor to reach the state your real workload would keep them in". If those words mean nothing yet, the posts
on [cache lines][ms-aos] and [branch prediction][ms-branch] are the warm-up for this one.

You can also *hold* some of that state still, which is what a quiet-machine checklist is for. On Linux the
standard moves are to pin the process to one core, disable frequency boost, set the CPU governor to
`performance`, and disable address-space layout randomisation so the layout confound above stops moving between
runs. [Google's benchmark library][gbench], [easyperf][easyperf], and the [`pyperf`][pyperf] and
[BenchmarkTools.jl][btools] projects all document versions of the same ritual. I want to be honest that I ran
none of it, because my measurement machine is a macOS laptop where those knobs mostly don't exist and the CPU
has a mix of performance and efficiency cores that the OS shuffles work between at will. That's a fine reason to
distrust any single number I show you, which is precisely the argument I'm making, so I'll take it.

## Where this leaves us

We have not computed anything yet. We have only established that a single timing is the wrong object to reason
about. It can be a measurement of nothing, if the optimiser got to it first. It can be shifted by facts about
the build and the machine that have nothing to do with your code and that you never recorded. And it carries a
warm-up transient that has to be paid before it settles.

The honest consequence is that you don't have *a number*. You have a *distribution*: a spread of times, with a
shape, produced by all of this variation at once. Round one at 6024 ns and round three at 5448 ns are not a
right answer and a wrong one; they are two samples from that distribution. The next post is about looking at the
whole thing: what shape benchmark timings actually take, why it is almost never the bell curve everyone assumes,
and which single number (the minimum, the mean, the median) you should read off it, a question on which the
experts genuinely disagree.

The function, the timing harness and the instructions to reproduce every number here are [in the repo for this
blog][code]. Run them. You will get different numbers, and now you know why.

[^1]: The version with the barrier does one more thing worth noticing: it launders the *input* through
`black_box` on every iteration too, not just the output. Without that, the optimiser sees that the input never
changes, computes the sum once outside the loop, and you're back to measuring an empty loop, a subtler version
of the same deletion. Barriers on both ends, every time.

[matklad]: https://matklad.github.io/2025/12/09/do-not-optimize-away.html
[mytkowicz]: https://doi.org/10.1145/2528521.1508275
[stabilizer]: https://people.cs.umass.edu/~emery/pubs/stabilizer-asplos13.pdf
[gbench]: https://google.github.io/benchmark/reducing_variance.html
[easyperf]: https://easyperf.net/blog/2019/08/02/Perf-measurement-environment-on-Linux
[pyperf]: https://pyperf.readthedocs.io/en/latest/system.html
[btools]: https://juliaci.github.io/BenchmarkTools.jl/stable/linuxtips/
[ms]: https://kaistriega.com/blog/mechanical-sympathy/
[ms-aos]: https://kaistriega.com/blog/mechanical-sympathy/array-of-structs-vs-struct-of-arrays/
[ms-branch]: https://kaistriega.com/blog/mechanical-sympathy/branch-prediction/
[code]: https://github.com/Kai-Striega/kai-striega.github.io/tree/main/code/reasonable-benchmarking
