+++
title = 'Appendix C: The Bootstrap, From First Principles'
date = 2026-11-22T10:20:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* Nearly every range in this series comes from one trick: the **bootstrap**. Resample your data with replacement,
  recompute, repeat a thousand times, and look at the spread.
* For the surveys, it measures ordinary sampling uncertainty: what if a different 2,000 people had answered?
* For the ballot counts, every vote was counted, so there's *no* sampling uncertainty. There it answers a different
  question: what if the seat were a slightly different mix of neighbourhoods?
* Resample **booths**, not single ballots. Neighbours vote alike, and ignoring that makes results look about 3.5
  times more certain than they are.
* "A squeeze in 37.5% of replicates" does **not** mean "a 37.5% chance it was really a squeeze".

## Introduction

Plenty of numbers in this series come with a range attached: an interval around a survey estimate, or "Labor gets
knocked out in more than a third of the rebuilt seats". I tried to keep the posts free of statistics, but if you want
to know what those ranges actually mean, this is the appendix. No statistics background assumed. In parts:

1. One survey, and no way to rerun it
2. Resample the sample
3. Why not just use a formula?
4. Counting every vote: what's left to be uncertain about?
5. Worked example: Macnamara 2022
6. Why booths, not ballots
7. What the bootstrap can't do

## One survey, and no way to rerun it

The 2025 Australian Election Study asked about 2,000 people where they sit on a 0–10 left–right scale. That's 2,000
out of 18 million voters. Phone a different 2,000 and you'd get slightly different numbers. The question is *how*
different. If another survey might put the Greens anywhere from 1 to 4 points left of the median voter, a 0.3 point
change between elections means nothing. If it would only ever put them between 2.2 and 2.6, it might.

The ideal fix is to run the survey a thousand times. That costs a thousand times as much, and nobody can go back and
rerun 2004.

## Resample the sample

The bootstrap's answer: the 2,000 people you *did* reach are your best picture of the 18 million you didn't. So
instead of drawing new samples from the population, draw them from your sample.

Let's do it with ten respondents instead of 2,000. Their self-placements are:

```r
x <- c(2, 3, 4, 5, 5, 5, 6, 6, 7, 8)
mean(x)   # 5.1
```

Now make a new "survey" of ten by drawing names out of a hat, putting each name back after you draw it. Because
names go back in, some people get drawn twice and others not at all. One draw might come out as
`2, 2, 4, 4, 4, 5, 5, 6, 6, 7` (an average of 4.5, leaning left); another as `3, 5, 5, 5, 6, 6, 6, 7, 7, 8` (5.8,
leaning right). That's exactly what happens with real surveys: by luck, one sample has a few too many of some kinds
of people. The bootstrap simulates that luck with the people you've actually got.

The "putting the name back" part is essential. Draw ten from ten *without* replacement and you get the same ten
people every time.

Do it a thousand times, line up the thousand averages, and chop off the lowest 25 and the highest 25:

```r
set.seed(1)
means <- replicate(1000, mean(sample(x, replace = TRUE)))
quantile(means, c(0.025, 0.975), type = 1)
```

```
 2.5% 97.5%
  4.1   6.1
```

That's the **95% interval**: with only ten people, an average of 5.1 is compatible with a true average anywhere from
about 4 to 6. For a simple average there's also the textbook formula behind a poll's "margin of error",

$$\bar{x} \pm 1.96 \, \frac{s}{\sqrt{n}}$$

where \(\bar{x}\) is the average, \(s\) the standard deviation and \(n\) the number of respondents. In R:

```r
mean(x) + c(-1, 1) * 1.96 * sd(x) / sqrt(length(x))
```

```
[1] 3.989333 6.210667
```

Almost the same. That's the reassuring bit: where a formula exists, the bootstrap agrees with it.

## Why not just use a formula?

Because for nearly everything in this series, there isn't one. A party's distance from the median voter uses an
*interpolated* median with survey weights. An adjusted rating comes out of a regression. A centre squeeze depends on
a full preferential count of tens of thousands of ballots, and the answer is yes or no. Nobody has a neat formula for
the uncertainty of any of those.

The bootstrap doesn't need one. It only needs a recipe that turns data into a result: run the recipe on a thousand
resampled datasets and look at the spread. That's why it's everywhere in this series.

For the surveys, it's exactly the toy example scaled up. Party placements use about 1,900 respondents, so they're
tight: in 2025 the Greens are 2.39 points left of the median voter, with an interval of 2.19 to 2.57. The position of
One Nation's *voters* rests on just the 43 respondents who voted One Nation in the Senate, so its interval is wide:
2.11 points right of the median, but anywhere from 1.16 to 3.03.

## Counting every vote: what's left to be uncertain about?

The centre squeeze analysis is a different beast. It doesn't use a sample at all: it uses every formal ballot cast in
a seat, 94,452 in Macnamara in 2022. There's no other set of voters we could have reached instead. The count is the
count. So what could a range possibly mean?

Here, the bootstrap answers a different question:

> If this seat were made up of a similar but slightly different mix of neighbourhoods, would the result still hold?

I find it easiest to picture as a **redistribution**. Every few years the AEC redraws electorate boundaries. A seat
gains some booths and loses others but mostly keeps its character. The booth-level bootstrap is like a thousand
imaginary redistributions, each one building a new version of the seat from the original seat's own booths, drawn
with replacement, and recounting it from scratch.

What it is **not** is a probability that a squeeze "really" happened. It doesn't model a swing, a new candidate or a
different campaign. It only reshuffles the voters who actually voted. So I call its results **ranges across
replicates**, never confidence intervals or margins of error, which would imply sampling.

## Worked example: Macnamara 2022

Macnamara was the closest call in the whole series. With three groups left, the Coalition had 35.1%, Labor 32.6% and
the Greens 32.3%. Labor was the Condorcet winner, and it made the final two by just 0.26 points. Here's the recipe:

1. **Take the seat apart** into its 72 collection points: 34 ordinary polling booths, 7 pre-poll voting centres, and 31
   other points (mostly batches of postal and other declaration votes). Each point keeps its ballots together.
2. **Build a reshuffled seat.** Draw 34 booths from the 34 with replacement, 7 pre-poll centres from the 7, and so on
   for each type, so every rebuilt seat has the same mix of booth types as the real one.
3. **Count it in full**, exactly as the original was counted.
4. **Repeat** a thousand times.

The resampling step lives in the C++ (it has to recount the whole seat a thousand times, so speed matters):

```cpp
for (int rep = 0; rep <= replicates; ++rep) {
  if (rep == 0) std::fill(mult.begin(), mult.end(), 1.0);          // replicate 0 is the real seat
  else {
    std::fill(mult.begin(), mult.end(), 0.0);
    for (auto& idx : strata) {                                     // each type of collection point
      int k = idx.size();
      for (int d = 0; d < k; ++d) {                                // draw k points from the k, with replacement
        int pick = std::min(k - 1, (int)std::floor(R::unif_rand() * k));
        mult[idx[pick]] += 1.0;                                    // how many times each point was drawn
      }
    }
  }
  // ... weight every point's ballots by mult, then count the rebuilt seat in full
}
```

Labor was the Condorcet winner in all 1,000 replicates, so that part is solid. But its margin with three left ranged
from −1.3 to +2.3 points, and in **37.5%** of replicates it was below zero: Labor knocked out, a centre squeeze.

It would be easy to read that as "a 37.5% chance Macnamara was really a squeeze". It isn't! On the ballots actually
cast, Labor survived. The 37.5% describes *how close* it was, in a useful unit. Labor's margin moves by about 0.9
points either way from one rebuilt seat to the next; call that the seat's wobble. The real margin, 0.26 points, is
only about 0.28 of a wobble above zero, and on a bell curve about 39% of draws land that far below the middle
(\(\Phi(-0.28) \approx 0.39\), where \(\Phi\) is the standard normal distribution function). That's
close to the 37.5% the bootstrap found. The squeeze frequency is basically "distance from the tipping point, measured
in wobbles".

Compare Griffith in 2025: a margin of 7.4 points and a range of 5.8 to 9.1. Many wobbles from the line, and zero
squeezes in a thousand replicates. That's what "robust" means here.

## Why booths, not ballots

Why draw whole booths instead of single ballots? Because people who vote at the same booth live near each other, and
neighbours tend to vote alike. The bootstrap can only simulate the variation its units carry. Resample single
ballots and it treats Macnamara's voters as 94,452 independent coin flips, which average out quickly, so the seat
looks far more predictable than it is.

To show the difference, I reran Macnamara resampling single ballots instead, still within each vote type. That's
easy to write in R, because drawing ballots with replacement from a set of distinct rankings is just a multinomial
draw:

```r
weights <- replicate(1000, {
  w <- numeric(n_rankings)
  for (s in split(by_type, by_type$stratum))        # each vote type keeps its number of ballots
    w[s$rid] <- w[s$rid] + rmultinom(1, sum(s$n), s$n)[, 1]
  w
}, simplify = FALSE)
ballot <- mclapply(weights, \(w) contest(rk, w, groups), mc.cores = 12)   # count each one in full
```

| Resampled unit | Units in the seat | Labor's margin (middle 95%) | Squeezes in 1,000 |
|---|---|---|---|
| Collection points | 72 | −1.31 to +2.31 points | 375 (37.5%) |
| Single ballots | 94,452 | −0.27 to +0.75 points | 175 (17.5%) |

![Two histograms of Labor's margin across 1,000 rebuilt versions of Macnamara. Resampling collection points, the margins spread from about −1.3 to +2.3 points; resampling single ballots, they bunch tightly between about −0.3 and +0.8.](/images/preferential-voting/bootstrap-macnamara.svg)

Resampling single ballots makes the range about 3.5 times narrower. That narrow range is roughly what a textbook
formula gives for 94,000 independent voters: it measures nothing but the luck of individual ballots, and misses the
much bigger variation between neighbourhoods. Macnamara is so close that even the narrow range crosses zero. But if
Labor had been a full point clear, single-ballot resampling would call it safe, while booth resampling would still
show it flipping in a noticeable share of replicates. Pick the wrong unit and your results look much sturdier than
they are.

## What the bootstrap can't do

The bootstrap assumes your data stand in for the population, or for the squeeze, that a seat's own booths stand in
for the neighbourhoods it could be made of. That works when there are lots of independent pieces, and less well
when:

* **There are few pieces.** Lingiari has only 15 or 16 polling places in the booths-only version, so its replicates
  can only vary in so many ways, and its ranges come out a bit too narrow.
* **A few pieces are huge.** Macnamara's biggest pre-poll centre holds 8,974 ballots. Drawing it twice, or not at
  all, is a lurch, not a wobble.
* **The problem isn't in the sample at all.** The bootstrap says nothing about whether Senate ballots are a good
  stand-in for House ballots, or whether people answer surveys honestly. Those limits are in [Appendix D][appd].

And a thousand replicates isn't infinitely many, so the frequencies carry a little noise of their own: about ±1.5
points for one like Macnamara's. "0.1%" means one replicate in a thousand: read it as "rare", not as a precise
number. Everything is seeded, so rerunning reproduces every figure exactly.

## Conclusion

The bootstrap is one of my favourite tools, because it turns "how sure are we?" into something you can just compute,
for any calculation, however messy. The trick is remembering which question it's answering: sampling uncertainty for
a survey, and something closer to "how fragile is this?" for a full count. Next, [Appendix D][appd] tries to break
everything.

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[appd]: https://kaistriega.com/blog/preferential-voting/appendix-d-breaking-it/
