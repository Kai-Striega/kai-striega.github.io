+++
title = 'Appendix D: Trying to Break It'
date = 2026-11-22T10:30:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* The posts report each result once. This appendix is every way I could think of to make them fall over.
* The survey findings hold across four alternative specifications, except one (the Nationals), which depends on a
  single choice.
* Some Senate ballots get filed in the wrong House division. Dropping them changes no winner.
* Squeezes only appear among the 1% of voters who number every box, a group that looks nothing like the electorate.
* Donkey votes, exhaustion and the booth resampling don't create a squeeze anywhere.
* There's also a whole analysis I *cut* from the series, because its assumptions did too much of the work.

## Introduction

A result is only as good as the attempts to knock it over. This appendix collects those attempts in one place, with
the code behind each check. In parts:

1. The survey regression
2. Ballots in the wrong division
3. Counting subsets of ballots
4. Donkey votes and exhaustion
5. The analysis I cut
6. The limits I can't fix

## The survey regression

The regression in [Appendix A][appa] involves some choices. Rather than pick one and hope, I fixed a set of
alternatives *before* running any of them, and report all of them:

```r
VARIANTS <- list(
  main            = list(bloc = TRUE,  distance = "perceived", drop_fives = FALSE, party_slopes = FALSE),
  drop_fives      = list(bloc = TRUE,  distance = "perceived", drop_fives = TRUE,  party_slopes = FALSE),
  mean_placement  = list(bloc = TRUE,  distance = "mean",      drop_fives = FALSE, party_slopes = FALSE),
  party_slopes    = list(bloc = TRUE,  distance = "perceived", drop_fives = FALSE, party_slopes = TRUE),
  party_outsiders = list(bloc = FALSE, distance = "perceived", drop_fives = FALSE, party_slopes = FALSE)
)
```

Each one changes a single thing: dropping every rating of 5 (which mixes "neutral" with "don't know"); measuring
distance from where the *whole sample* places a party instead of each person; giving each party its own slope; and
dropping the Coalition bloc. Counting the surveys (of 11) where the difference is clearly below (↓) or above (↑) zero:

| a − b | Main | Drop 5s | Sample placement | Party slopes | No Coalition bloc |
|---|---|---|---|---|---|
| Liberal − Labor | 10↓ 1↑ | 9↓ 1↑ | 6↓ 1↑ | 10↓ 1↑ | 6↓ 1↑ |
| Liberal − Greens | 8↓ | 8↓ | 8↓ | 8↓ | 6↓ |
| Liberal − Nationals | 2↓ 6↑ | 6↑ | 1↓ 5↑ | 2↓ 6↑ | 11↓ |
| Greens − Labor | 4↓ 5↑ | 5↓ 3↑ | 1↓ 5↑ | 5↓ 5↑ | 4↓ 5↑ |

* **The Liberal finding holds.** The Liberals are below Labor in at least six surveys under every version, and ten
  under the main one. 1996 goes the other way in all of them.
* **The Nationals finding depends on one choice.** With the Coalition bloc, outsiders dislike the Nationals about as
  much as the Liberals. Without it, they don't. I think the bloc is the right call, but if you disagree, you should
  disregard that finding too.

The other worry is the weights. The surveys from 1996 to 2007 have no weights, so the trend mixes weighted and
unweighted years. Rerunning everything unweighted, the rise in zeros barely changes (50% either way in 2025). The rise
in people with no party at all, on the other hand, only shows up *with* weights (26% weighted, 16% unweighted), so
I've stayed away from claiming it.

## Ballots in the wrong division

The squeeze test assumes each Senate ballot sits in its voter's own House division. Mostly it does. But a pre-poll
centre serving several divisions can file all its Senate ballots under just one of them. To catch that, I compared
each polling place's Senate ballots with its House ballots (every voter gets both papers, so they should roughly
match):

```r
checked = !is.na(ratio) & ratio >= 0.8 & ratio <= 1.2   # Senate ballots / House ballots at each polling place
```

About one polling place in 60 fails (144 of 8,479 in 2022, 147 of 8,940 in 2025), holding 1.5–1.7% of Senate ballots.
Dropping them changes no winner and creates no squeeze.

## Counting subsets of ballots

Every 2022 and 2025 contest also gets recounted on subsets of its ballots:

```r
keep <- switch(f,
  all_checked            = dp$checked[trip$point],
  ordinary_booth         = dp$category[trip$point] == "ordinary booth",
  ordinary_booth_checked = dp$category[trip$point] == "ordinary booth" & dp$checked[trip$point],
  ordinary_votes         = dp$category[trip$point] %in% ORDINARY,
  full_rankers           = rk$lens[trip$rid] == G,      # numbered every box
  ranks_last_three       = has3[trip$rid])              # numbered all of the last three groups
```

Squeezes across 2022 and 2025:

| Subset | Share of ballots kept | Squeezes |
|---|---|---|
| Passing the House check | 100% | 0 / 0 |
| Election-day booths only | 40–44% | 0 / 0 |
| All ordinary votes | 77–80% | 0 / 0 |
| Number every box | 1% | 32 / 25 |
| Number all of the last three | 18–21% | 1 / 0 |

Hmm, that "number every box" row looks alarming! But those voters (about 600 to 1,300 a seat) are nothing like the
electorate. In Macnamara, 31% of them put the Greens first, against 27% of all voters, and 14% put the Coalition first,
against 30%. Most of their squeezes have a little-known minor party as the Condorcet winner: a party almost nobody
puts first but almost nobody puts near the bottom either. It's the squeeze mechanism in its purest form, but on a
group that can't stand in for anyone.

The booth resampling from [Appendix C][appc] gives the same picture: across 301 contests and 1,000 rebuilt versions of
each, squeezes turn up in only 4 contests, all of them near misses.

## Donkey votes and exhaustion

A *donkey vote* numbers the boxes 1, 2, 3, … straight across from the first column. I leave those out of every count.
Could adding them back create a squeeze? Only if the first-column party were in a contest's final three *and* the
donkey share were bigger than the Condorcet winner's lead. In the at-risk contests (lead under 10 points), donkey votes
are at most 0.26% of ballots, against a smallest lead of 0.3 points. Not enough.

About a tenth of Senate ballots also *exhaust* (run out of numbered preferences) before the final two, which can't
happen in the House. Neither of the subsets where nothing exhausts makes a good stand-in for the House either, which
is a big part of why the NSW check in [Appendix B][appb] matters so much.

## The analysis I cut

There was originally a whole extra section asking: how many first preferences would One Nation (or the Greens, or
Trumpet of Patriots) need to win a typical seat, under first past the post versus preferences? I simulated it by
"recruiting" voters to a party on the Senate ballots while keeping the rest of their rankings, and bisecting for the
share needed to win.

It produced some fun numbers. Under one way of growing, One Nation's extra hurdle from preferences in a typical seat
fell from 4.6 points in 2016 to 0.7 in 2025. But that depended heavily on *how* you assume a party grows, and with two
equally plausible assumptions giving quite different answers, the assumptions were doing most of the work. So I took
it out of the argument. I mention it here so it's not quietly hidden.

## The limits I can't fix

* **House ballots are never published**, so every federal result on full rankings leans on the Senate stand-in.
* **First past the post is simulated** on ballots cast under preferential voting. People would vote differently.
* **Survey ratings** are noisy: a 5 means "neutral or don't know", 1993 words the question differently, and there are
  a lot of comparisons with no correction. Read patterns, not single intervals.
* **One Nation was only rated in 1998–2004**, and Trumpet of Patriots never.
* **Senate last places** come only from the 2.7% of voters who number every box.
* **How-to-vote cards** shape rankings as well as voters' own views.
* **"Independents"** lumps the teals in with every other kind of independent.

## Conclusion

Most of the results survived everything I threw at them. The ones that didn't (the Nationals finding, the cut
threshold analysis) are flagged as such. If you can think of a check I didn't try, I'd love to hear it. The last
appendix, [Appendix E][appe], covers where all the data comes from.

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[appa]: https://kaistriega.com/blog/preferential-voting/appendix-a-measuring/
[appb]: https://kaistriega.com/blog/preferential-voting/appendix-b-nsw-ballots/
[appc]: https://kaistriega.com/blog/preferential-voting/appendix-c-bootstrap/
[appe]: https://kaistriega.com/blog/preferential-voting/appendix-e-data/
