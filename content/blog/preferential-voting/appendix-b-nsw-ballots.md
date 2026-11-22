+++
title = 'Appendix B: Counting Every NSW Ballot'
date = 2026-11-22T10:10:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* This is the working behind the NSW half of [Does Preferential Voting Squeeze the Centre?][post2].
* NSW publishes the preferences on every lower-house ballot paper. I read all 13.7 million formal ballots from 2015,
  2019 and 2023.
* A preferential count is a simple loop: exclude the lowest, move their ballots on, repeat. I show it in C++, and
  run a made-up centre squeeze through it.
* Optional preferential voting means you need a rule for "candidates this voter didn't number". The choice matters.
* My reconstruction of the 2023 count matches the official one exactly: 1,496 out of 1,496 checks.

## Introduction

The federal results in this series lean on Senate ballots as a stand-in for House ballots, because the AEC never
publishes House ballots. NSW is different. The NSW Electoral Commission data-enters every Legislative Assembly ballot
paper and publishes the preferences on each one. As far as I could find, it's the only place in Australia where you
can test preferential voting on real single-member lower-house ballots. This appendix shows how. In parts:

1. Reading the ballots
2. Counting a contest three ways
3. The trouble with unnumbered candidates
4. Checking against the official count
5. Measuring the Senate stand-in

## Reading the ballots

Each NSWEC file has one row per *mark*: district, ballot number, formality, candidate, the raw mark the voter wrote
(`PrefMarking`) and the NSWEC's reading of it (`PrefCounted`), already cut off wherever the sequence breaks. A
ballot's ranking is just its `PrefCounted` marks in order.

I don't like trusting a field I didn't compute, so as a check I read every formal ballot's raw marks myself: numbers
1, 2, 3, … until one is missing or repeated; a lone tick or cross with no numbers is a first preference; and one tick
with every other mark a cross makes the tick the first preference. How do those compare?

```
year  formal   numbers  single_mark  tick_with_crosses  differs
2015  4404334  4402696         1570                 68        0
2019  4551886  4549206         2578                102        0
2023  4701930  4700362         1470                 98        0
```

Zero disagreements across 13.66 million ballots. Nearly every ballot uses numbers; a few thousand are a single tick or
cross.

One thing that jumps out straight away: NSW uses *optional* preferential voting, so a ballot with just a 1 is formal.
And lots of people do exactly that. Between 57% and 65% of ballots number only one candidate. Keep that in mind.

## Counting a contest three ways

Every district gets counted three ways: first past the post, the NSW preferential count, and Condorcet (who beats
everyone head to head).

The preferential count is a surprisingly small loop. Here's the core of it, from the C++ that does the counting for
the whole series:

```cpp
while (n_cont > 2) {
  int loser = /* the continuing candidate with the fewest votes (tie rule below) */;
  cont[loser] = 0;
  --n_cont;
  std::vector<double> moved(G, 0.0);
  double exhausted = 0.0;
  for (int b : piles[loser]) {                       // every ballot sitting with the loser
    int p = pos[b] + 1;
    while (p < lens[b] && !cont[items[starts[b] + p]]) ++p;   // skip anyone already excluded
    pos[b] = p;
    if (p < lens[b]) { int g = items[starts[b] + p]; piles[g].push_back(b); moved[g] += w[b]; }
    else exhausted += w[b];                          // no further preference: the ballot exhausts
  }
  for (int g = 0; g < G; ++g) if (cont[g]) tallies[g] += moved[g];
  tallies[loser] = 0.0;
}
```

Each candidate has a pile of ballots. Exclude the smallest pile, walk each of its ballots forward to the next
candidate still standing, and either move it onto that pile or mark it exhausted. Repeat until two are left.

NSW has a specific rule for ties at the bottom: the candidate who was lower at the most recent count where the tied
candidates *differed* is excluded. That's this bit:

```cpp
// Walk back through earlier counts until the tied candidates differ.
for (int k = (int)out.totals.size() - 2; k >= 0 && tied.size() > 1; --k) {
  double lowest = std::numeric_limits<double>::infinity();
  for (int c : tied) lowest = std::min(lowest, out.totals[k][c]);
  std::vector<int> keep;
  for (int c : tied) if (out.totals[k][c] == lowest) keep.push_back(c);
  tied.swap(keep);
}
```

Let's give it a go on the made-up seat from the post: 35 voters rank Left, Centre, Right; 16 rank Centre, Left,
Right; 14 rank Centre, Right, Left; and 35 rank Right, Centre, Left.

```r
groups <- c("Left", "Centre", "Right")
rk <- list(items  = c(0L,1L,2L,  1L,0L,2L,  1L,2L,0L,  2L,1L,0L),  # four rankings, zero-based
           starts = c(0L,3L,6L,9L), lens = c(3L,3L,3L,3L))
w <- c(35, 16, 14, 35)                                              # how many voters cast each
irv(rk, w, 3L)$totals
```

```
     [,1] [,2] [,3]
[1,]   35   30   35
[2,]   51    0   49
```

Round one: Left 35, Centre 30, Right 35. Centre is excluded, its 30 ballots split 16 to Left and 14 to Right, and
Left wins 51 to 49. Now the head-to-heads:

```r
P <- pairwise(rk, w, 3L); dimnames(P) <- list(groups, groups); P
```

```
       Left Centre Right
Left      0     35    51
Centre   65      0    65
Right    49     35     0
```

Read across a row: Centre is preferred to Left by 65 voters to 35, and to Right by 65 to 35. Centre is the Condorcet
winner, and the preferential count threw it out first. That's a centre squeeze, live. Across 279 real NSW contests,
this never happened.

## The trouble with unnumbered candidates

With optional preferences there's a wrinkle. What does a ballot that only says "1 Smith" tell you about Jones versus
Brown? Nothing. So comparing two candidates head to head needs a rule for ballots that don't number both. I tried
three:

| Rule | Counts as "A over B" |
|---|---|
| **primary** | A is numbered above B, *or* A is numbered and B isn't. Two unnumbered candidates is an abstention. |
| both | only ballots that number both A and B |
| first-or-both | ballots that number both, plus ballots whose first preference is A or B |

The primary rule is the main one, and there's a good reason: under it, the preferential count's final round *is* the
head-to-head between the last two candidates, so "was the Condorcet winner excluded?" compares like with like. Under
each rule, how many contests have the preferential count excluding the Condorcet winner?

```
year  districts  primary  first-or-both  both
2015         93        0              1    44
2019         93        0              2    44
2023         93        0              0    30
```

The "both" rule flags 30 to 44 seats a year, but that's an artefact. Most of the leading candidate's voters number
only their own candidate, so this rule throws them all away, even though a voter who numbers only A obviously prefers
A to everyone. The three first-or-both cases (Gosford 2015, Coogee 2019, Lismore 2019) are genuinely close seats
whose result depends on how you read truncated ballots, not squeezes.

## Checking against the official count

None of this is worth much if my count is wrong. The NSWEC publishes a distribution of preferences page for every
district, plus a final first-preference workbook, so I checked the 2023 reconstruction against both: candidate names,
formal and informal ballots, first preferences, the order of exclusions, every count's transfers and totals, every
count's exhausted ballots, and the final two.

```r
> all(validation$ok)
[1] TRUE
> nrow(validation)
[1] 1496
```

All 1,496 checks match exactly. That was a very satisfying `TRUE`. (One caveat: I only had the official count pages
for 2023, so the 2015 and 2019 counts use exactly the same code but aren't independently checked.)

## Measuring the Senate stand-in

This is the part I think is most useful. NSW's 2023 *upper-house* ballots also record which lower-house district they
were cast in, just like federal Senate ballots record their House division. So I can run exactly the Senate-style
method on them, district by district, and compare it with the real lower-house ballots in the same seats.

Upper-house groups aren't named in the preference files, so each lower-house party is matched to the upper-house
group whose first-preference share across districts correlates best with it (Labor r = 0.96, Greens 0.94,
Liberal/National 0.89), and I checked each match by hand against the group's lead candidate.

The stand-in picks the real winner in 72 of 93 districts. Split by who held the seat, its error on the Labor versus
Coalition head-to-head looks like this:

```
sitting_party  seats  mean_error  mean_abs_error  proxy_more_labor
ALP               33     -0.0013          0.0175                19
LIB/NAT           31      0.0653          0.0653                31
open seat         19      0.0454          0.0454                19
other              8      0.0187          0.0351                 7
```

In seats held by the Coalition, the stand-in overstates Labor in *every single one*, by 6.5 points on average. That
fits a personal vote for sitting MPs, which a party-level ballot can't see. But it still overstates Labor by 4.5
points in open seats, so part of the gap is people simply voting differently for the two houses.

## Conclusion

NSW turned out to be the best data in the whole series: real lower-house ballots, an official count to check
against, and a natural experiment for measuring how wrong the Senate method can be. If you only trust one result in
this series, make it the 1,496 out of 1,496. Next, [Appendix C][appc] explains the bootstrap.

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post2]: https://kaistriega.com/blog/preferential-voting/squeeze-the-centre/
[appc]: https://kaistriega.com/blog/preferential-voting/appendix-c-bootstrap/
