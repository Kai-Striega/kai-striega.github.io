+++
title = 'Does Preferential Voting Squeeze the Centre?'
date = 2026-11-22T09:20:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* The "centre squeeze" is the main criticism of preferential voting: a broadly liked moderate gets knocked out early
  for having too few first preferences.
* I recounted all 602 House contests from 2016 to 2025 using Senate ballots. No squeezes. In every contest that had
  a Condorcet winner, the preferential count elected it.
* On real NSW lower-house ballots (279 contests), same result, including all 12 where that candidate trailed on first
  preferences.
* First past the post would have missed the Condorcet winner 77 times, mostly by splitting the Labor and Greens vote.
* The Condorcet winner isn't always the centrist. Sometimes it's the Greens.
* The Senate stand-in is good but not perfect, so the very closest calls could go either way.

## Introduction

Last time, we saw that Australians are increasingly willing to rule parties out completely. If that's true, then how
the voting system handles those rejections matters a lot. Preferential voting's best-known criticism is that it
handles them badly, and in a specific way: it can knock out exactly the candidate most people could live with.

This post tests that criticism on as many ballots as I could find. In parts:

1. What a centre squeeze actually is
2. Counting every House seat with Senate ballots
3. The near misses
4. What first past the post would have done
5. Is the Condorcet winner really the centrist?
6. Checking with real lower-house ballots

## What a centre squeeze is

Here's a made-up seat with three candidates and a hundred voters:

| Voters | Their ranking |
|---|---|
| 35 | Left, Centre, Right |
| 16 | Centre, Left, Right |
| 14 | Centre, Right, Left |
| 35 | Right, Centre, Left |

On first preferences Left has 35, Centre 30 and Right 35. Centre has the fewest, so Centre is excluded. Its 30
ballots split 16 to Left and 14 to Right, and Left wins 51 to 49.

But look at the head-to-heads. Centre beats Left 65 to 35 (everyone except Left's own voters prefers Centre), and
beats Right 65 to 35 as well. Centre is the **Condorcet winner**: a majority prefers it to every rival. And the
preferential count knocked it out first. That's a centre squeeze. (I ran this exact example through the real
counting code in [Appendix B][appb].)

If this happened often, preferential voting would be *rewarding* polarisation, not filtering it. So does it?

## Counting every House seat

The AEC doesn't publish House ballot papers. Annoying! But it does publish every Senate ballot, and each one records
the House division it was cast in. So for each division I can treat the Senate parties as candidates, treat every
Senate ballot cast there as a ranking, and count the seat three ways: first past the post, preferential (exactly as
the House does it), and Condorcet.

That gives 602 contests across four elections. The result is short: **no squeezes**. In all 601 contests that had a
Condorcet winner, the preferential count elected it. (The one without a Condorcet winner, Adelaide in 2016, had a
three-way cycle where every candidate loses to someone.)

## The near misses

A squeeze needs a specific shape: three candidates close together with the broadly liked one in the middle. So I
measured, for every contest, how far ahead the Condorcet winner was of the weaker of the other two when three were
left. A negative number would be a squeeze.

![Strip chart of 601 divisions across 2016, 2019, 2022 and 2025. No point is below zero; the closest each year is labelled: Kennedy 2016 at 3.2 points, Griffith 2019 at 0.9, Macnamara 2022 at 0.3, Kennedy 2025 at 3.5.](/images/preferential-voting/squeeze-margins.svg)

Most seats aren't remotely close. The handful that are tend to be inner-city seats where Labor, the Greens and the
Liberals are all around a third each.

The closest of all is Macnamara in 2022. With three left, the Coalition had 35.1%, Labor 32.6% and the Greens 32.3%.
Labor was the Condorcet winner, and it survived into the final two by 0.26 points. That's close enough that it isn't
really robust in either direction. If I rebuild the seat a thousand times from its own booths drawn at random, Labor
gets knocked out in more than a third of the rebuilt seats. And on election-day booth votes alone, the Greens, not
Labor, are the Condorcet winner. ([Appendix C][appc] explains the rebuilding trick; [Appendix D][appd] has the
other checks.)

## What first past the post would have done

On the same ballots, first past the post (most first preferences wins) would have missed the Condorcet winner 77
times. Nearly all of those are seats where the Coalition led on first preferences while the left vote was split
between Labor and the Greens.

But that's not quite a fair fight. These ballots were cast under preferential voting. Under first past the post, a
lot of Greens voters would just vote Labor. So I moved a share of every third-party ballot to whichever of the top
two it ranked higher:

![Line chart: with no switching first past the post misses the Condorcet winner 77 times; if a quarter of third-party voters switch, 58; half, 41; all of them, 2.](/images/preferential-voting/fptp-strategic.svg)

If a quarter of third-party voters switch, 58 misses remain. At half, 41. If all of them do, just 2. So the honest
version is: first past the post would miss a lot more Condorcet winners than preferential voting, *unless* voters
adapt by voting tactically. Which, to be fair, they do.

## Is the Condorcet winner really the centrist?

The squeeze criticism imagines the broadly acceptable option as the moderate in the middle. But those two things
don't have to be the same. Using where survey respondents place each party, I checked whether each contest's
Condorcet winner was the ideological middle of the final three.

It is in 253 of the 400 contests I could check. Most of the rest are safe Coalition seats where the Coalition wins
outright: a majority prefers it to everyone, even though it sits at one end. The interesting ones are the close
seats where the Condorcet winner is the *Greens*: Griffith in 2019 and 2022, Brisbane in 2022 and Ryan in 2022. There
the broadly acceptable option was the party furthest from the median voter. A "squeeze" in those seats would have
knocked out an end option, not the centre.

### Quick check-in

So far:

* no squeezes in 602 contests counted with Senate ballots;
* a few near misses, all in close three-way inner-city seats;
* first past the post would miss far more, unless voters vote tactically;
* the broadly acceptable option isn't always the centrist.

But everything so far rests on a big assumption: that Senate ballots tell us how people would rank House candidates.

## Checking with real lower-house ballots

Senate ballots rank parties, not local candidates. They miss independents entirely, and they miss any personal vote
a sitting MP has. So is the stand-in any good?

It turns out NSW is (as far as I could find) the one place in Australia that publishes every lower-house ballot. The
NSW Electoral Commission data-enters every Legislative Assembly ballot paper. So I counted all 13.7 million formal
ballots from 2015, 2019 and 2023, and first checked my count against the official 2023 results. It matches
exactly, in every district, at every count. ([Appendix B][appb] has the details.)

Across 279 contests, the preferential count elected the Condorcet winner every time. That includes the 12 contests
where the Condorcet winner was *behind* on first preferences, which is the real test:

![Dumbbell chart of 12 NSW contests where the Condorcet winner trailed on first preferences. Each starts between about 26% and 42% of the vote and finishes above 50% after preferences.](/images/preferential-voting/nsw-trailing.svg)

In fairness, it's a weak test. Most NSW voters only number one box, so the first-preference leader is usually the
Condorcet winner anyway.

The more useful thing NSW gives us is a way to measure the Senate stand-in. NSW's upper-house ballots also record
which lower-house district they were cast in. So I can run the Senate method on them and compare it with the real
lower-house ballots in the same seats.

![Strip chart of 91 NSW districts. Where the Coalition held the seat, every point is right of zero, up to 17 points: the stand-in shows Labor stronger than the real ballots did. Where Labor held it, points straddle zero.](/images/preferential-voting/nsw-proxy.svg)

The stand-in picks the real winner in 72 of 93 districts. Most misses are seats won by independents (which it
simply can't see) or Coalition seats it hands to Labor. Overall it leans towards Labor by 3.3 points, most of all
where a sitting Coalition MP has a personal vote.

What does that mean for the federal results? In the three NSW seats where the Greens and Labor fought it out, the
stand-in was off by 3 to 9 points. That's more than the margins in Macnamara 2022 (52–48) and Brisbane 2022 (51–49)
on the Senate ballots. So those calls could genuinely go either way. Ryan in 2025 (58–42, with a sitting Greens MP)
is within that range too: a *possible* squeeze, not a likely one.

## Conclusion

I went in expecting to find at least a few centre squeezes. I didn't. On every ballot I could get, preferential
voting elected the option a majority preferred to every rival, and it's hard to make a squeeze happen without three
near-equal candidates and the broadly liked one in the middle. Australian seats rarely look like that.

What this *doesn't* tell us is whether preferential voting filters out extremism, because no party usually called
extreme came anywhere near winning one of these contests. That needs a different test, which is the [next
post][post3].

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post3]: https://kaistriega.com/blog/preferential-voting/who-keeps-one-nation-out/
[appb]: https://kaistriega.com/blog/preferential-voting/appendix-b-nsw-ballots/
[appc]: https://kaistriega.com/blog/preferential-voting/appendix-c-bootstrap/
[appd]: https://kaistriega.com/blog/preferential-voting/appendix-d-breaking-it/
