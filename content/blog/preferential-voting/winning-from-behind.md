+++
title = 'Winning From Behind'
date = 2026-11-22T09:40:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* The most common complaint about preferential voting: someone who came *second* on first preferences can win.
* It happens in about one seat in twelve: 102 of 1,202 House divisions since 2004.
* The leader who loses is nearly always a Coalition candidate (96 of those 102).
* Labor's comebacks run on Greens preferences. The independents' comebacks (the teals and others) run on Labor and
  Greens preferences.
* Right-populist comebacks are rare: two in 22 years, both in 2013.

## Introduction

[Last time][post3] we saw preferences keeping One Nation out of the House. There's a mirror image of that, and it's
the thing people complain about most: preferences letting a candidate who trailed on first preferences overtake the
leader. Is that a flaw? Who does it help? And whose preferences do the overtaking?

First, one thing that makes this much less strange than it sounds. In the House, every ballot has to number every
box. So when the count gets down to the last two candidates, every single ballot ranks one of them above the other.
The final count *is* a straight head-to-head. A candidate who wins from behind is, by definition, preferred to the
first-preference leader by a majority of voters. First past the post would have elected the leader anyway.

In parts:

1. How often, and against whom
2. Whose preferences

## How often, and against whom

Using the AEC's official counts, I found every division where the winner wasn't the first-preference leader:

![Stacked bar chart of seats won from behind each election: 8 in 2004, 9 in 2007, 11 in 2010, 15 in 2013, 16 in 2016, 12 in 2019, 16 in 2022 and 15 in 2025. Labor wins most of them; independents won 7 in 2022 and 5 in 2025.](/images/preferential-voting/overturns.svg)

That's 102 seats in 22 years, about one in twelve. It's crept up from 8 to 11 an election in the 2000s to 12 to 16
since. Labor won 78 of them, independents 15 and the Greens 4.

Now look at who *loses*. When a Coalition candidate led on first preferences, they went on to lose 96 times out of
664 (about one in seven). When a Labor candidate led, they lost 4 times out of 504. That's a huge asymmetry, and it
has a pretty simple explanation, which we'll get to.

## Whose preferences

Every time a candidate is excluded, their votes move. So for each comeback I can add up what each source of
preferences passed to the eventual winner, minus what it passed to the leader. Those net flows add up exactly to how
far behind the winner started plus their final winning margin, which is a nice check that nothing has gone missing.

![Two bar charts of each source's share of the winners' net preference gain. In Labor's comebacks the Greens supply 107% of it, with One Nation and other minor parties slightly negative. In independents' comebacks Labor supplies 59% and the Greens 23%.](/images/preferential-voting/overturn-sources.svg)

**Labor's comebacks run on Greens preferences.** Across Labor's 78 comebacks, Greens preferences supplied *more than
all* of Labor's net gain (107%). How can it be more than 100%? Because One Nation's and other minor parties'
preferences flowed back towards the leader. In 72 of those 78 seats, the Greens' preferences alone were bigger than
the final margin.

**The independents' comebacks run on Labor and Greens preferences.** Labor's preferences supplied 59% of their net
gain and decided 10 of the 15. There are three interesting exceptions, all independents who overtook a *Labor*
leader (Denison in 2010, Fowler in 2022 and 2025), and all carried by Coalition preferences.

**Right-populist comebacks are rare.** Two in 22 years, both in 2013: Clive Palmer in Fairfax (by 53 votes!) and Bob
Katter in Kennedy, both carried mainly by Labor preferences. One Nation's own preferences, meanwhile, flowed on
balance to the leader rather than the comeback candidate.

And the margins range from a knife's edge to comfortable. Bradfield in 2025 was won from 11 points behind by **26
votes**. At the other end, there are seats where the winner finished so far ahead that no single source of
preferences decided it on its own.

### So why always the Coalition?

Here's my best guess at the asymmetry. The Coalition vote starts out concentrated in one candidate. The centre-left
vote starts out split, between Labor and the Greens, and in teal seats between an independent, Labor and the Greens.
Preferences reunite the split vote, and Labor and Greens preferences rarely reach the Coalition. So a Coalition
candidate can lead comfortably on first preferences and still be behind once the split vote recombines.

## Conclusion

Winning from behind isn't a quirk. It's the same rule we saw in the last post seen from the other side. A candidate
needs a majority in the final count, which blocks a party most voters rank low, *and* lets a candidate whom most
voters rank above the leader overtake. In practice, that has mostly meant Coalition leaders losing to candidates
carried by Labor and Greens preferences.

Time to put the whole thing together, in the [final post][post5].

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post3]: https://kaistriega.com/blog/preferential-voting/who-keeps-one-nation-out/
[post5]: https://kaistriega.com/blog/preferential-voting/does-it-filter-out-extremists/
