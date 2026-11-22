+++
title = 'So, Does It Filter Out Extremists?'
date = 2026-11-22T09:50:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* Australian polarisation, as the surveys measure it, is about rejection, not tribalism.
* Preferential voting doesn't squeeze out the broadly acceptable option. But that option isn't always the centrist.
* It has kept One Nation out of the House, because Labor and Greens voters rank it near the bottom. Coalition voters
  have stopped doing the same.
* Preferential voting doesn't filter out "extremes" as such. It filters out whoever a majority ranks below some
  rival.
* That means the filter is only as strong as the rankings behind it, and those rankings are moving.

## Introduction

Four posts in, it's time to answer the question I started with: does preferential voting filter out extremists, or
does it squeeze out the centre? I'll go through what each post found, then try to put it together, and finish with
the things all of this *can't* tell us.

## What we found

**[Rejection, not tribalism][post1].** Partisans like their own side about as much more than the other as they did in
1993. What's grown is the willingness to rule a party out entirely: half of voters now give some party a 0. And that
rejection isn't just about left and right. The Liberals are disliked more than Labor at the same distance from each
voter, and One Nation, which voters placed *nearer the centre* than the Liberals, was disliked most of all.

**[No centre squeeze][post2].** On 602 federal contests counted with Senate ballots, and 279 counted with real NSW
lower-house ballots, the preferential count elected the Condorcet winner every time there was one. Squeezes need
three near-equal candidates with the broadly liked one in the middle, and Australian seats rarely look like that.

**[The One Nation wall][post3].** One Nation has reached the final two four times since 2004 and lost every time. What
stopped it was Labor and Greens preferences, which reach it at about a quarter of a comparable Labor candidate's
rate. Coalition voters used to help too. By 2025, three in four ranked One Nation above Labor, and that shift shows
up even among voters filling in their own order.

**[Winning from behind][post4].** About one seat in twelve goes to someone who trailed on first preferences, and the
leader who loses is nearly always a Coalition candidate, overtaken on Labor and Greens preferences.

## The filter is whoever a majority ranks lower

Put those together and here's where I've landed. Preferential voting doesn't filter "extremes" in any deep sense. It
filters out *any* candidate whom a majority ranks below some rival.

In Australia, that has meant One Nation, because the Labor and Greens voters who rank it near the bottom have
outnumbered everyone who ranks it above Labor. It has *also* meant Coalition candidates who lead on first preferences
but whom most voters rank below a Labor, Greens or independent rival. Same rule, two very different-looking
outcomes.

Which means the filter is only as strong as the rankings behind it. And those are moving. Rejection of the Greens has
risen faster than for any other party, and the Coalition's voters have stopped ranking One Nation below Labor. If
those trends keep going, preferential voting will keep electing whoever a majority prefers. It's just that the
majority it finds might not be one that keeps the populist right out.

## What all this can't tell us

I promised at the start that I'd be upfront about the limits. Here are the big ones:

* **House ballots are never published.** Everything about full rankings in federal seats leans on Senate ballots as a
  stand-in. The NSW check says that stand-in picks the right winner about three times in four, and can be several
  points out in exactly the Greens versus Labor seats that matter most.
* **One Nation was only asked about in 1998–2004**, and Trumpet of Patriots never, so I can't directly link dislike to
  last places for either in 2025.
* **How-to-vote cards muddy everything.** Below-the-line ballots help separate voters' own views from party
  instructions, but only partly: they come from a small, engaged group.
* **I'm not a political scientist.** I've tried to check every number, and the appendices show the working, but the
  interpretation is a hobbyist's.

## Conclusion

When I started, I expected to find a messier story about preferential voting than "it works". Instead, on these
ballots, it does exactly what it says on the tin: elects whoever a majority prefers. The interesting part turned out
to be the voters, not the system: who they reject, and how quickly that's changing.

If you want to see how any of this was actually done, the appendices go through it, code and all, starting with
[Appendix A][appa]. And if you know this field and think I've got something wrong, please tell me.

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post1]: https://kaistriega.com/blog/preferential-voting/not-more-partisan/
[post2]: https://kaistriega.com/blog/preferential-voting/squeeze-the-centre/
[post3]: https://kaistriega.com/blog/preferential-voting/who-keeps-one-nation-out/
[post4]: https://kaistriega.com/blog/preferential-voting/winning-from-behind/
[appa]: https://kaistriega.com/blog/preferential-voting/appendix-a-measuring/
