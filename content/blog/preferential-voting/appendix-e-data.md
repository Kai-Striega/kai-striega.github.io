+++
title = 'Appendix E: Where the Data Comes From'
date = 2026-11-22T10:40:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* Everything in this series comes from public data: the Australian Election Study, the AEC, and the NSW Electoral
  Commission.
* The biggest piece is every formal Senate ballot from 2016 to 2025, which arrives as one CSV row per ballot paper.
* Reading those files quickly takes a little care: R for the plumbing, C++ for the hot loop.

## Introduction

This is the least exciting appendix, and possibly the most useful one if you want to try any of this yourself. It
covers what data I used, what it looks like when it arrives, and how it gets read. In parts:

1. The sources
2. What a Senate ballot file looks like
3. Reading it without waiting all day
4. The other files

## The sources

| Source | What | Used for |
|---|---|---|
| Australian Election Study, 1993–2025 | Twelve post-election surveys: party ratings, left–right placements, party identification, weights | [Who voters dislike][post1] |
| AEC Senate formal preferences, 2016–2025 | Every formal Senate ballot, with the House division and polling place it was cast at | [Last places][post1], [the squeeze test][post2], [the One Nation blocs][post3] |
| AEC House distributions of preferences, 2004–2025 | Every count in every division's official preference distribution | [Transfers][post3], [winning from behind][post4] |
| AEC House first preferences and polling places | Booth-level House counts, to check Senate ballots are in the right division | [Appendix D][appd] |
| NSW Electoral Commission, 2015–2023 | Every Legislative Assembly ballot's preferences, plus the official 2023 count | [Appendix B][appb] |

The AEC files come from its results download pages, one folder per election. The AES is available from the Australian
Data Archive under its terms of use. The NSW data is © State of New South Wales through the NSW Electoral Commission,
licensed CC BY 4.0.

## What a Senate ballot file looks like

Each state and territory's Senate ballots come as one zipped CSV per election. NSW's 2025 file is about 42 MB
zipped, and much bigger unzipped. Let's peek at the first ballot in the ACT's:

```shell
$ unzip -p aec-senate-formalpreferences-31496-ACT.zip | head -2
State,Division,Vote Collection Point Name, Vote Collection Point ID, Batch No, Paper No,A:Sustainable Australia Party - Universal Basic Income,B:David Pocock,C:Animal Justice Party,D:Australian Labor Party,E:Liberal,F:HEART/LIBERTARIAN,G:Australian G...
ACT,Canberra,Ainslie North,1,1,1,5,2,3,4,7,6,1
```

The header has six columns of bookkeeping (state, division, polling place, batch, paper number), then one column per
box: first the above-the-line boxes, one per group (`A:`, `B:`, …), then one per candidate below the line. Each row is
one ballot paper, with the number the voter wrote in each box. This voter put the Greens (column G) first, David
Pocock second, Animal Justice third, and so on, all above the line.

Two things make these files mildly annoying:

1. **Rows are ragged.** A row stops at the last box the voter filled in, so rows have different lengths.
2. **2016 is different.** The 2016 files pack every box into a single comma-separated field, with `*` (a tick) and `/`
   (a cross) both counting as a 1.

## Reading it without waiting all day

Here's the reader for the newer format, trimmed a little. `fread` streams the zip straight from `unzip -p`, `fill`
pads the ragged rows out to the full width of the ballot paper, and the marks end up in an integer matrix:

```r
cmd <- sprintf("unzip -p %s", shQuote(path))
head <- unlist(fread(cmd = cmd, nrows = 1, header = FALSE, colClasses = "character"))
cols <- head[-(1:6)]                                      # one column per box on the paper
dt <- fread(cmd = cmd, skip = 1, header = FALSE, fill = 6L + length(cols),
            colClasses = list(character = 1:6))
marks <- matrix(NA_integer_, nrow(dt), length(cols))
for (j in seq_len(min(ncol(dt) - 6, length(cols))))
  marks[, j] <- suppressWarnings(as.integer(dt[[6 + j]]))
```

The marks matrix then goes to C++ (`aggregate_rankings`, walked through in [Appendix A][appa]), which turns each row
into a ranking of parties and collapses identical rankings into one entry with a count. Doing that row loop in C++
rather than R is what takes reading all 15.8 million 2025 ballots from "go and make a coffee" to "a minute or so", one
state or territory per process.

## The other files

The **AES** surveys come as SPSS files, read with `haven`. The annoying part isn't reading them, it's that every survey
stores the same questions under different names. So each wave gets a small lookup table, read off its codebook:

```r
`2025` = list(weight = "weight", self = "B8_1", senate = "B9_2_r", parties = b8_16,
              codes = c(`1` = LIB, `2` = ALP, `3` = NAT, `4` = GRN, `11` = ONP, `96` = "Independents"))
```

The **House distributions of preferences** are one long CSV per election, with a row for every candidate at every
count. A quick reshape gives each candidate's running total and transfer at each step:

```r
dop <- dop[CalculationType %in% c("Preference Count", "Transfer Count")]
w <- dcast(dop, year + StateAb + DivisionNm + CountNumber + CandidateID + Surname + PartyAb ~ CalculationType,
           value.var = "CalculationValue")
```

And the **NSW** files have one row per *mark*, rather than per ballot, which [Appendix B][appb] covers.

## Conclusion

That's the end of the series. If you made it all the way to the data appendix, thank you, and I'm a little worried
about you. If you try any of this yourself, or spot something I got wrong, I'd love to hear about it.

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post1]: https://kaistriega.com/blog/preferential-voting/not-more-partisan/
[post2]: https://kaistriega.com/blog/preferential-voting/squeeze-the-centre/
[post3]: https://kaistriega.com/blog/preferential-voting/who-keeps-one-nation-out/
[post4]: https://kaistriega.com/blog/preferential-voting/winning-from-behind/
[appa]: https://kaistriega.com/blog/preferential-voting/appendix-a-measuring/
[appb]: https://kaistriega.com/blog/preferential-voting/appendix-b-nsw-ballots/
[appd]: https://kaistriega.com/blog/preferential-voting/appendix-d-breaking-it/
