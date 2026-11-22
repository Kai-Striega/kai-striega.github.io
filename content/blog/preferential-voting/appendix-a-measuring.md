+++
title = 'Appendix A: Measuring Position, Dislike and Rejection'
date = 2026-11-22T10:00:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* This is the working behind [Not More Partisan, Just More Rejecting][post1]. Lots of R, a little C++.
* The **median voter** has to be *interpolated*, because a third of people answer 5 on a 0–10 scale.
* **Dislike beyond ideology** comes from one regression per survey: \(\text{rating} = \text{intercept}_p + \text{slope} \times \text{distance}\).
  The gap between two parties splits *exactly* into a distance part and a party part.
* A Senate ballot becomes a **ranking of parties** by following the voter's numbers until the sequence breaks.
* **Last places are corrected for ballot position** with a conditional logit, which only works because the AEC
  draws the column order by lot.

## Introduction

The posts in this series keep the maths out of the way. This appendix is the opposite: it walks through how each
measure in the first post is actually built, with the real code, trimmed down to the lines that matter. The
analysis is in R, with the heavy ballot reading done in C++ through Rcpp. In parts:

1. The median voter
2. Dislike beyond ideology: the survey regression
3. From a ballot paper to a ranking
4. Correcting last places for ballot position

## The median voter

Every Australian Election Study asks people to place themselves on a scale from 0 (left) to 10 (right). A party's
*distance from the median voter* is just its average placement minus the median voter's position. Easy. Let's try
it on 2025:

```r
> median(self)
[1] 5
```

Hmm. That's 5. It's also 5 in basically every survey since 1996, which would make the median voter look like they
never move. The problem is that the scale is coarse and an enormous number of people answer exactly 5:

```r
> sum(w[self == 5]) / sum(w)
[1] 0.353
```

More than a third of respondents. So I treat each answer \(k\) as covering everything from \(k - 0.5\) to \(k + 0.5\),
find which category the 50% point falls in, and interpolate inside it. If \(N\) is the total (weighted) number of
answers, \(N_{<k}\) the number below category \(k\), and \(N_k\) the number in it, then

$$\text{median} = k - \tfrac{1}{2} + \frac{N/2 - N_{<k}}{N_k}$$

which in R is:

```r
interpolated_median <- function(x, w) {
  totals <- vapply(0:10, \(k) sum(w[x == k]), numeric(1))   # weighted count at each answer
  half <- sum(totals) / 2
  k <- which(cumsum(totals) >= half)[1] - 1                  # the category holding the median
  below <- sum(totals[seq_len(k)])                           # weight below that category
  k - 0.5 + (half - below) / totals[k + 1]                   # how far into it the 50% point falls
}
```

```r
> interpolated_median(self, w)
[1] 4.953016
```

Now it moves smoothly from survey to survey, and small shifts in the 5s actually show up. A side benefit: it behaves
nicely under the bootstrap ([Appendix C][appc]), where a plain median would just jump between whole numbers.

## Dislike beyond ideology: the survey regression

### The data

The unit here is a *pair*: one respondent and one party they don't support (an **outsider** pair). Each pair has two
numbers: the respondent's rating of the party (0–10), and their **perceived distance** from it, the gap between where
they place themselves and where they place the party. A voter at 3 who puts the Liberals at 8 is 5 points from them.
2025 has about 5,500 of these pairs.

### The model

Each survey gets one weighted least-squares fit over all its pairs:

$$\text{rating}_{ip} = \alpha_p + \beta \, d_{ip} + \varepsilon_{ip}$$

where \(d_{ip}\) is respondent \(i\)'s perceived distance from party \(p\), \(\alpha_p\) is party \(p\)'s intercept, and
\(\beta\) is the slope. There's one intercept per party but a single shared slope. In R that's a design matrix with one dummy column per
party plus a distance column, handed to `lm.wfit` with the survey weights. Here's the heart of it:

```r
D <- sapply(parties, \(p) as.numeric(party == p))      # one indicator column per party
X <- cbind(D, dist)                                     # ... plus the shared distance column
coef <- lm.wfit(X, like, w)$coefficients                # weighted least squares

pooled <- sum(dist * w) / sum(w)                        # average distance across all pairs
adjusted <- coef[parties] + coef[["dist"]] * pooled     # each party's rating at that same distance
```

Running it on 2025 gives:

```
       party adjusted effect   slope
1:    Greens   3.2502 4.7304 -0.4425
2:     Labor   3.7301 5.2104 -0.4425
3:   Liberal   3.1022 4.5824 -0.4425
4: Nationals   3.2041 4.6843 -0.4425
pooled mean distance: 3.3449
```

How to read that:

* **The slope** (−0.44) is the cost of distance. Every extra point between a voter and a party knocks about 0.44
  points off their rating, whichever party it is.
* **The intercept** (`effect`) is the rating a party would get from a voter sitting exactly where they place it.
  Differences between intercepts are the dislike that distance doesn't explain.
* **The adjusted rating** is each party's predicted rating at the *same* distance for everyone, the average
  distance \(\bar d = 3.34\): that is, \(\alpha_p + \beta \bar d\). It's the intercept moved onto the familiar 0–10
  scale, so it's the number the posts chart.

### Splitting a gap into distance and dislike

This bit is genuinely neat. Because every party has its own intercept, least squares forces the errors to average
to zero *within each party*. So each party's mean rating is exactly its intercept plus the slope times its mean
distance. Subtract two parties and the gap splits cleanly in two:

$$\bar{y}_a - \bar{y}_b = \underbrace{\beta \, (\bar{d}_a - \bar{d}_b)}_{\text{distance}} + \underbrace{(\alpha_a - \alpha_b)}_{\text{the party itself}}$$

where \(\bar{y}\) is a party's mean rating among its outsiders and \(\bar{d}\) their mean distance from it.

For the Liberals and Labor in 2025:

|                              | Rating points |
|------------------------------|--------------:|
| Mean rating, Liberal − Labor |         −0.85 |
| Due to distance              |         −0.22 |
| Due to the party             |         −0.63 |

Outsiders rate the Liberals 0.85 points below Labor. A quarter of that is because the Liberals' outsiders (mostly
left-of-centre voters) see them as further away. The other 0.63 is dislike that distance doesn't explain.

### What could go wrong

A few things, and I want to be honest about them:

* **Projection.** People may push parties they dislike further away from themselves, so some dislike leaks into the
  distance. Measuring distance from where the *whole sample* places a party avoids that, and gives a steeper slope
  (−0.59), a sign that individual placements are noisy. So I only trust findings that survive both versions
  ([Appendix D][appd]).
* **Straight lines.** The model assumes ratings fall linearly and symmetrically with distance. The binned data look
  close to straight, but the far end rests on few people.
* **Different outsiders.** Each party's intercept describes how *its own* outsiders see it, not how one fixed group
  of voters sees every party.
* **The 5s again.** A 5 means "neutral *or* don't know", which flatters less familiar parties. Dropping every 5 is one
  of the robustness checks.

## From a ballot paper to a ranking

Over to the Senate. Each formal ballot is a row of numbers, one per box: one box per party above the line, one per
candidate below it. The AEC's rule is that you follow the numbers 1, 2, 3, … until one is missing or written twice,
and that's where the vote stops. A ballot counts as below the line if that sequence reaches at least 6.

That rule, in C++ (it runs over 15.8 million rows, so it needs to be quick):

```cpp
// The longest valid sequence 1, 2, 3, ... among boxes c0..c1 of ballot i:
// stop at the first number that is missing or written in two boxes.
static void valid_sequence(const IntegerMatrix& M, int i, int c0, int c1,
                           std::vector<int>& pos, std::vector<char>& rep, std::vector<int>& out) {
  int n = c1 - c0;
  out.clear();
  for (int j = c0; j < c1; ++j) {
    int v = M(i, j);
    if (v == NA_INTEGER || v < 1 || v > n) continue;
    if (pos[v] == -1) pos[v] = j - c0; else rep[v] = 1;   // remember where each number is, and repeats
  }
  for (int k = 1; k <= n && pos[k] != -1 && !rep[k]; ++k) out.push_back(pos[k]);
  // ... reset pos and rep for the next ballot
}
```

A below-the-line ballot is then turned into a ranking of *parties* in the order of each party's first numbered
candidate. Let's try it on three made-up ballots, with three parties (A, B, C) and two candidates each:

```r
marks <- rbind(
  c(2, 1, 3,  NA, NA, NA, NA, NA, NA),   # above the line: B, A, C
  c(NA, NA, NA, 3, 4, 1, 2, 6, 5),       # below the line: B's candidates, then A's, then C's
  c(1, 1, 2,  NA, NA, NA, NA, NA, NA))   # two 1s: the sequence breaks straight away
aggregate_rankings(marks, n_atl = 3, cand_group = c(0, 0, 1, 1, 2, 2), unit = rep(1, 3), n_units = 1)
```

```
$items
[1] 1 0 2
$n
[1] 2
$unusable
[1] 1
```

Both the first two ballots collapse into the same ranking, B then A then C (`1 0 2`, zero-based), which is stored
once with a count of 2. The third ballot is unusable. Collapsing identical rankings like this is what makes the whole
thing feasible: 15.8 million ballots become a few million distinct rankings, each with a count.

## Correcting last places for ballot position

Voters who number every box have to put someone last, and they put the parties at the *edges* of the ballot far more
often than chance. So a raw count of last places mixes two things: how much voters reject a party, and where it
happened to sit on the paper.

### What makes this possible

The AEC draws each state's and territory's column order by lot. So the same party sits in different columns in
different places, and comparing how often it's put last in each lets a model tell the party from its column. If a
party always sat at the edge, you'd never be able to separate "unpopular" from "unlucky".

### The model

Each full ranker's last place is treated as a choice among every party *except* the one they put first (nobody puts
their own first choice last). The chance \(P_f(g)\) that a voter whose first preference is \(f\) puts party \(g\) last
is

$$P_f(g) = \frac{\exp(\alpha_{g} + \gamma_{c(g)})}{\sum_{h \ne f} \exp(\alpha_{h} + \gamma_{c(h)})}$$

where \(\alpha_g\) is a *party effect* for party \(g\) and \(\gamma_{c(g)}\) a *column effect* for the column \(c(g)\) it sits in.

That's a *conditional logit*. Column effects are estimated for the first, second, second-last and last columns
(middle columns are the zero baseline), separately for minor parties (under 5% of first preferences in that state)
and major ones, because voters with no view of a small party seem to place it by where it sits. It's fitted by
Newton's method; here's the inner loop over each group of voters who share a first preference:

```r
for (st in prep) for (bf in st$by_first) {         # each state, each first preference
  f <- bf$first[1]; n <- sum(bf$n)
  Xc <- st$X[-f, , drop = FALSE]                   # everyone except their own first choice
  s <- drop(Xc %*% theta); p <- exp(s - max(s)); p <- p / sum(p)
  xbar <- colSums(p * Xc)
  grad <- grad + colSums(st$X[bf$last, , drop = FALSE] * bf$n) - n * xbar
  H <- H - n * (crossprod(Xc, p * Xc) - tcrossprod(xbar))
}
theta <- theta - solve(H, grad)                    # one Newton step
```

A column effect reads as an odds multiplier, \(e^{\gamma}\): how many times more likely a party is to be put last in
that column than the same party in a middle column. The fitted values:

```
                            column log_odds odds_multiplier
1:       first column, major party   0.3730          1.4520
2:       first column, minor party   1.4154          4.1180
3:        last column, major party  -0.1483          0.8622
4:        last column, minor party   1.8260          6.2091
...
```

![Grouped bar chart of odds multipliers: for minor parties, the first column 4.1 times, second 1.0, second-last 1.9 and last 6.2; major-party effects are all between 0.8 and 1.5.](/images/preferential-voting/position-effects.svg)

A minor party in the last column is about six times as likely to be put last as the same party in the middle. The
major-party estimates are much smaller, and they rest on only a handful of cases (a major party has to land at an
edge for its effect to be estimated at all), so I don't lean on them. Dropping them barely changes any result.

### From the model to the measure

The column effects become an expected number of last places for each party: how many it would get if voters ignored
parties entirely and chose by column alone. Give each party the weight \(w_g = e^{\gamma_{c(g)}}\) (which is 1 in a
middle column) and add up over the \(n_f\) voters who put each other party \(f\) first:

$$E_g = \sum_{f \ne g} n_f \, \frac{w_g}{\sum_{h \ne f} w_h}$$

In R:

```r
weight <- exp(ifelse(is.na(cols), 0, effects[cols]))     # 1 for a middle column
for (i in seq_len(nrow(by_first))) {
  f <- by_first$first[i]
  others <- setdiff(seq_len(G), f)
  expected[others] <- expected[others] + by_first$n[i] * weight[others] / (sum(weight) - weight[f])
}
```

The measure in the post is actual last places over that expectation, \(\text{last}_g / E_g\). Notice that the *party*
effects play no part in it. That's deliberate: the expectation is the "party doesn't matter" baseline that the real last places get
compared with.

To make it concrete, here's the ACT in 2025, the smallest ballot paper and the place where the most people number
every box:

| Column | Party | Column weight | Put last | Expected from column | Ratio |
|---|---|---|---|---|---|
| 1 | Sustainable Australia | 4.12 | 14,224 | 51,171 | 0.28 |
| 2 | David Pocock | 1.17 | 1,633 | 8,395 | 0.19 |
| 3 | Animal Justice | 1.00 | 12,620 | 12,511 | 1.01 |
| 4 | Labor | 1.00 | 7,380 | 9,145 | 0.81 |
| 5 | Liberal | 1.00 | 35,856 | 10,701 | 3.35 |
| 6 | HEART/Libertarian | 1.93 | 35,171 | 24,062 | 1.46 |
| 7 | Greens | 0.86 | 19,090 | 9,989 | 1.91 |

The Liberals sat in a middle column and were put last more than three times as often as that column predicts.
Sustainable Australia, in the first column, was put last a lot in raw terms, but far *less* than its column alone
predicts, so its ratio is 0.28. The correction works in both directions.

## Conclusion

That's the measuring done. None of it is especially exotic: an interpolated median, a regression with party dummies,
a careful reading of ballot papers, and a conditional logit. The care goes into the boring bits, like the 5s, the
edge columns, and not letting Canberra decide the national answer. Next up, [Appendix B][appb] counts every NSW
lower-house ballot.

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post1]: https://kaistriega.com/blog/preferential-voting/not-more-partisan/
[appb]: https://kaistriega.com/blog/preferential-voting/appendix-b-nsw-ballots/
[appc]: https://kaistriega.com/blog/preferential-voting/appendix-c-bootstrap/
[appd]: https://kaistriega.com/blog/preferential-voting/appendix-d-breaking-it/
