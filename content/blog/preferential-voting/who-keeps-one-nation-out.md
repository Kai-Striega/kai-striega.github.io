+++
title = 'Who Keeps One Nation Out?'
date = 2026-11-22T09:30:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* One Nation has never won a House seat on preferences. In 22 years it reached the final two four times, always from
  third place, and lost every time.
* What blocks it is the Labor and Greens vote. Their preferences reach One Nation at about a quarter of the rate a
  Labor candidate of the same size would get.
* Preferences from minor parties and independents reach it at almost three times the Labor rate. So it isn't that
  *everyone* rejects it.
* The block is weakening from the right. In 2016 most Coalition voters ranked Labor above One Nation. By 2025, three
  in four ranked One Nation above Labor.
* That's not just party how-to-vote cards. Coalition voters who number their own order moved too, from 47% to 65%.

## Introduction

[Last time][post2] I couldn't find a single centre squeeze. But that test couldn't say anything about extremism,
because no party usually called extreme ever came close to winning one of those contests. So this post goes after
the "filter" claim directly, with the party it's usually about: One Nation.

For this I switched to the AEC's official House counts. For every division since 2004, the AEC publishes the full
**distribution of preferences**: every candidate's total after every round, and how many votes moved where each time
someone was excluded. That's 1,202 real counts. In parts:

1. Who reaches the final two
2. Where preferences flow
3. Who would let One Nation in?
4. Voters, or how-to-vote cards?

## Who reaches the final two

Every preferential count ends with two candidates. Reaching that final pair is where the filter actually bites.

In 22 years and 1,202 divisions, One Nation reached the final two **four times**: Maranoa in 2016, 2019 and 2025,
and Hunter in 2025. Every time it was third on first preferences. Every time it lost.

For comparison, Clive Palmer won Fairfax in 2013 from second place, and Bob Katter wins Kennedy at every election,
usually leading on first preferences anyway. Independents reached the final two 61 times and won 36 of them.

So yes, something stops One Nation. But what?

## Where preferences flow

When a candidate is excluded, their votes get shared out among everyone still standing. Bigger candidates naturally
pick up more of them, so raw counts aren't much use. Instead I compared every party with a **Labor candidate of the
same size**: a value of 1 means "gets as many of the transferred votes as an equally big Labor candidate would"; 0.25
means a quarter as many.

![Two dot charts with intervals. From Labor and Greens candidates, One Nation receives about 0.26 times what a same-size Labor candidate would, and Trumpet of Patriots less still. From minor parties and independents, One Nation receives almost 3 times as much.](/images/preferential-voting/transfers.svg)

The left panel is the wall. When a Labor or Greens candidate is excluded, their voters' preferences reach One Nation
at about a quarter of the rate they'd reach a same-size Labor candidate. Trumpet of Patriots does even worse.

The right panel is the surprise. When a minor party or independent is excluded, One Nation does *better* than a
Labor candidate, nearly three times better. Coalition preferences flow to it readily too. So the filter isn't some
general hostility from all voters. It's specific: it's the left-of-centre vote that won't preference One Nation.

## Who would let One Nation in?

That raises the obvious question. One Nation's realistic path to a seat is a final against one of the major parties.
When that happens, the *other* major party's voters decide it. So how do they rank One Nation against the rival
major party?

The Senate ballots answer that, election by election:

![Line chart. Coalition voters ranking One Nation above Labor: 41% in 2016, rising to 75% in 2025. Labor voters ranking One Nation above the Coalition: 42% falling to 28%. Greens voters: never above 19%.](/images/preferential-voting/blocs.svg)

In 2016 most Coalition voters ranked Labor above One Nation. By 2025, **three in four** ranked One Nation above
Labor. In a One Nation versus Labor final, the Coalition vote used to block One Nation. Now it carries it. Labor
voters moved the other way, and Greens voters barely moved at all.

### Quick check-in

So far:

* One Nation keeps reaching the final two only from third, and losing;
* what stops it is Labor and Greens preferences;
* Coalition voters have swung from mostly blocking it to mostly preferring it to Labor.

But there's an obvious objection to that last point.

## Voters, or how-to-vote cards?

Most Senate voters number boxes *above the line*, one per party, and plenty of them just copy a party's how-to-vote
card. So maybe Coalition voters didn't change their minds at all. Maybe the Liberal and National parties changed what
they recommended, and their voters followed along.

Luckily there's a way to check. Voters who fill in the ballot *below the line* number individual candidates in their
own order. They aren't copying a card (mostly). Only 3–6% of Coalition voters do it, but that's still well over a
hundred thousand people each election. To stop the result moving just because below-the-line voting is far more
popular in Tasmania than elsewhere, I weighted each state and territory by all of its Coalition voters.

![Line chart. Above the line, Coalition voters ranking One Nation above Labor went from 40% in 2016 to 76% in 2025. Below the line, from 47% to 65%.](/images/preferential-voting/btl.svg)

Coalition voters choosing their own order moved too: from 47% ranking One Nation above Labor in 2016 to 65% in 2025,
and the rise shows up in every state with numbers for both years. So this is a real change in voters, not just in
party instructions.

But the last step looks different. Between 2022 and 2025 the above-the-line number jumped 19 points, while the
below-the-line number moved 4. That's what you'd expect if the parties changed their recommendations in 2025, on top
of a slower shift in what their voters actually think.

One oddity worth flagging: the 2019 below-the-line point is inflated. In NSW that year, a Liberal senator ran a
campaign asking voters to vote below the line for him, and 138,446 of them did. Those voters were following a
campaign, not choosing their own order, so I don't read much into that bump.

## Conclusion

So, does preferential voting filter out One Nation? So far, yes. But not because voters in general reject it. The
wall has been built out of specific voters, Labor and Greens supporters, and the Coalition's voters, who used to help
hold it up, have mostly walked away from it.

There's a flip side to all this. The same rule that blocks One Nation also lets candidates who trail on first
preferences win. That's the [next post][post4].

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post2]: https://kaistriega.com/blog/preferential-voting/squeeze-the-centre/
[post4]: https://kaistriega.com/blog/preferential-voting/winning-from-behind/
