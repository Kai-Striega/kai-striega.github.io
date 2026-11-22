+++
title = 'Not More Partisan, Just More Rejecting'
date = 2026-11-22T09:10:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

*Part of a series of back-of-the-envelope calculations by someone who knows almost nothing about politics. The
[introduction][intro] explains why; please use your own judgement.*

## TLDR

* Australians don't dislike the other side more than they used to. The partisan gap hasn't grown in 32 years.
* What has grown is outright rejection. Half of voters now rate some party 0 out of 10. The Greens' zeros rose most.
* Some parties are disliked *beyond* their politics. At the same left–right distance from a voter, the Liberals are
  liked less than Labor in every survey since 1998.
* One Nation most of all. Voters placed it closer to the centre than the Liberals, yet rated it lowest by a mile.
* The ballots agree with the surveys. The parties Senate voters most often put last are the Greens, Trumpet of
  Patriots and the Liberals, then Labor and One Nation.

## Introduction

In the [last post][intro] I showed that Australians are no more partisan than they were in the 1990s, but much more
willing to give a party a flat 0. This post digs into that. Who gets the zeros? Is it just the parties at the
extremes of the left–right spectrum, or is something else going on? And does what people tell a survey match what
they actually do on a ballot paper?

I'll do this in a few parts:

1. Who dislikes whom
2. Separating dislike from ideology
3. The Liberals
4. One Nation
5. Who voters put last

## Who dislikes whom

The data is the Australian Election Study (AES): twelve surveys, from 1993 to 2025, each asking a couple of
thousand people to rate every major party from 0 to 10, place themselves on a left–right scale, and place each
party on the same scale.

One thing to sort out before anything else: whose ratings count? A party's own supporters will like it whatever it
does, so they tell us nothing about rejection. So I only use each party's **outsiders**, the people who identify
with some other party or with none. (Liberal and National supporters count as one Coalition bloc. Otherwise the
Liberals' friendliness towards their coalition partner makes the Nationals look more popular than they are.)

Among outsiders, the zeros have climbed since 2001, and they've climbed most for the Greens. That was my first
surprise: the party getting rejected fastest isn't on the right.

## Separating dislike from ideology

The obvious explanation for a low rating is distance. A voter on the left will rate a right-wing party low, and
vice versa. So the interesting question isn't "who is disliked?" but "who is disliked *more than their position
explains?*"

Here's the idea, without any maths. For every outsider and every party, I know two numbers: how much they like the
party, and how far they see it from themselves on the left–right scale. Across thousands of these pairs, ratings
fall in a pretty straight line as distance grows: each extra point of distance costs a party about 0.44 points of
rating. So I can ask what every party's rating would be if every voter saw it from the *same* distance. Call that
the **adjusted rating**. If one party's adjusted rating sits below the others, it's disliked for something other
than how far away it is.

(The regression behind this, the exact split of a rating gap into "distance" and "dislike", and all the ways it
could be wrong are in [Appendix A][appa].)

## The Liberals

![Line chart of adjusted ratings by party, 1996 to 2025, with 95% intervals. The Liberal line sits below Labor's in every survey from 1998 on; in 1996 Labor was lower.](/images/preferential-voting/adjusted-ratings.svg)

The Liberals come out as the least-liked party among outsiders, and for two separate reasons.

The first is distance. Most of the Liberals' outsiders are left-of-centre voters, and from where *they* sit, the
Liberals are a long way off. That's a fair reason to dislike a party, and it accounts for about a quarter of the gap
with Labor in 2025 (0.22 of 0.85 rating points).

The second reason is everything else. Even at the same distance, outsiders rate the Liberals below Labor in every
survey since 1998: 10 of the 11 surveys that ask people to place the parties. The exception is interesting. In
1996, after 13 years of Labor government, it was *Labor* that outsiders disliked beyond its distance. So it isn't
something baked into the Liberal brand. It moves.

## One Nation

The AES only asked about One Nation in 1998, 2001 and 2004. In those three surveys, it's in a league of its own.

![Three dot charts, one each for 1998, 2001 and 2004. In each, One Nation's adjusted rating sits far to the left of every other party, with no overlap between the intervals.](/images/preferential-voting/one-nation-adjusted.svg)

At the same distance as every other party, One Nation is rated 0.75 to 1.84 points below each of them, in all three
surveys. That gap is bigger than the gap between the Liberals and Labor in any survey ever.

Now the bit that genuinely surprised me. Ask voters where One Nation sits on the left–right scale and they put it
*closer to the centre than the Liberals*: about 0.8 points right of the median voter, against 1.3 to 1.9 for the
Liberals. By the usual definition, that makes it less extreme than a major party. And yet it's the most disliked
party in the data, by a wide margin, and few people rated it 5 ("neutral or don't know"), so it isn't that nobody
had heard of it.

That's worth sitting with. If "extreme" means "far from the median voter", One Nation wasn't. If it means "most
voters will put it last", it absolutely was.

### Quick check-in

So far we've seen that:

* rejection, not partisanship, is what has grown;
* a party's position doesn't explain how much it's disliked;
* the Liberals, and One Nation even more, are disliked beyond their distance.

But all of this is what people *tell a survey*. What do they actually do when they vote?

## Who voters put last

Senate ballots are perfect for this. Voters who number every box on the Senate paper have to put *someone* last,
and the AEC publishes every ballot. So I can count how often each party lands in last place.

There's a catch. Voters who number every box put the parties at the *edges* of the ballot paper last far more often
than chance, whoever happens to be there. Luckily the AEC draws the column order by lot, separately in each state
and territory, so the same party sits in different columns in different places. That lets me work out how much
last-placing each column causes on its own, and compare each party's real last places with what its column alone
would produce.

One more wrinkle: only about 3% of voters number every box, and far more of them live in the ACT (43%) than in
Victoria (0.7%). So I weight each state and territory by its voters. Otherwise Canberra would decide the answer.

![Dot chart of last places relative to ballot position, 2025: Greens 4.0 times, Trumpet of Patriots 3.9, Liberals 3.4, Labor 2.4, One Nation 2.4, then three minor parties below 1.](/images/preferential-voting/senate-last-place.svg)

The Greens are put last four times as often as their ballot position explains, closely followed by Trumpet of
Patriots and the Liberals, then Labor and One Nation. Every minor party that ran in more than one state or territory
sits below 1: voters who don't know a small party just leave it somewhere in the middle.

And here's the nice part. For the three parties the survey and the Senate both score nationally (Greens, Liberals,
Labor), the order of last places matches the order of *zeros* in the survey. Putting a party last on a ballot is the
ballot's version of giving it a 0.

## Conclusion

The picture I came away with is that Australian voters aren't splitting into two hostile tribes. They're
increasingly willing to rule individual parties out entirely, and which parties they rule out isn't just a matter of
left and right. That's exactly what a preferential system is supposed to be good at handling. Whether it actually
is, is the subject of the [next post][post2].

[intro]: https://kaistriega.com/blog/preferential-voting/back-of-the-envelope-politics/
[post2]: https://kaistriega.com/blog/preferential-voting/squeeze-the-centre/
[appa]: https://kaistriega.com/blog/preferential-voting/appendix-a-measuring/
