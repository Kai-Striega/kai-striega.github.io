+++
title = 'Back of the Envelope Politics'
date = 2026-11-22T09:00:00+11:00
tags = ['politics', 'elections', 'statistics', 'r']
+++

## TLDR

* I know almost nothing about politics. This series is me playing with public election data, not expert analysis.
  Please use your own judgement before relying on, quoting or sharing any of it.
* Australians aren't becoming more tribal. The gap between how much partisans like their own side and the other
  side is no wider than it was in 1993.
* What has grown is outright rejection: half of voters now give at least one party a 0 out of 10, up from under a
  quarter in 2001.
* Preferential voting doesn't seem to squeeze out the centre. On every ballot I could get my hands on, it elected
  the option a majority preferred to every rival.
* It has kept One Nation out of the House, but the wall is made of particular voters, and some of them have left.
* The same rule overturns the first-preference leader in about one seat in twelve, nearly always at the Coalition's
  expense.

## Introduction

Let me get the important bit out of the way first: **I have almost no background in politics or political
science.** I write software. I like data. A while ago I noticed that the Australian Electoral Commission publishes
every single Senate ballot paper, all 15.8 million of them in 2025, with every number every voter wrote on it.
That's an absurd amount of data about how people actually rank parties, and I couldn't stop myself from poking at
it.

Everything in this series is a back-of-the-envelope calculation. The numbers come from real ballots and real
surveys, and I've checked them as carefully as I know how. But the framing and the interpretation are mine, and a
political scientist would almost certainly spot things I've missed. Treat it as a curious outsider's notebook, not
as a finding you can quote at a dinner party without double checking.

With that out of the way, here's the question that got me started.

## Why care how people rank parties?

Australia uses *preferential voting* for the House of Representatives. You don't just pick one candidate: you
number every box, from your favourite to your least favourite. If nobody has a majority of first preferences, the
candidate with the fewest votes is excluded and their ballots move to each voter's next choice. Repeat until
someone has a majority.

That means a candidate's chances depend on how many voters put them *last*, not just how many put them first.
There are two popular stories about what that does:

1. **It filters out extremists.** To win you need a majority once preferences are counted, so a candidate most
   voters rank at the bottom can't get there.
2. **It squeezes out the centre.** A moderate who is lots of people's second choice, but few people's first, can be
   excluded early and never get counted.

Both can't be the whole truth. So I went looking.

## How Australians feel about the parties

The first thing I wanted to know was whether Australians actually feel more strongly about parties than they used
to. Every Australian Election Study since 1993 has asked people to rate each party from 0 (strongly dislike) to 10
(strongly like). Here are two things you can measure with that:

![Two line charts. Left: the partisan gap stays between about 4 and 5.5 rating points from 1993 to 2025 with no upward trend. Right: the share of voters giving some party 0 falls from 41% in 1993 to 23% in 2001, then rises to 50% in 2025.](/images/preferential-voting/intro-trends.svg)

On the left is the usual measure of "affective polarisation": how much more Labor and Liberal supporters like their
own party than the other one. It hasn't grown. If anything it's drifted down a little.

On the right is the share of people who give at least one party a 0. That fell through the late 1990s, then climbed
steadily to *half of all voters* in 2025. So we're not becoming tribal in the American sense. We're becoming more
willing to rule a party out completely. That's exactly the kind of thing a preferential system should care about.

## The plan

I've split the series into two halves. The posts make the argument with as little maths and code as I could manage.
The appendices are for anyone who wants to see how the sausage got made, and they're full of R.

The argument:

1. **This post.** The why, and the disclaimer.
2. **[Not More Partisan, Just More Rejecting][post1].** Who voters dislike, and who they put last on the ballot.
3. **[Does Preferential Voting Squeeze the Centre?][post2].** Recounting every House seat with Senate ballots, and
   checking it against real NSW ballots.
4. **[Who Keeps One Nation Out?][post3].** Whose preferences block the party most often called extreme, and
   whether that's changing.
5. **[Winning From Behind][post4].** The seats where preferences overturned the first-preference leader.
6. **[So, Does It Filter Out Extremists?][post5].** Putting it together.

The working:

* **[Appendix A][appa]:** measuring left–right position, dislike and rejection (both regressions, in full).
* **[Appendix B][appb]:** counting every NSW lower-house ballot, and checking it against the official count.
* **[Appendix C][appc]:** the bootstrap, from first principles.
* **[Appendix D][appd]:** every way I could think of to break the results.
* **[Appendix E][appe]:** where the data comes from.

A couple of terms that turn up everywhere. **First preferences** are the votes numbered 1. The **Condorcet winner**
of a contest is the candidate a majority prefers to each rival in a head-to-head comparison, if there is one. And
because the ACT and NT are territories rather than states, I'll say "states and territories" whenever I mean all
eight.

## Conclusion

That's the setup. I'll say it one more time, because it matters: I'm an amateur having fun with a very large pile
of ballots. If you know this field and something looks wrong, I'd genuinely love to hear about it.

[post1]: https://kaistriega.com/blog/preferential-voting/not-more-partisan/
[post2]: https://kaistriega.com/blog/preferential-voting/squeeze-the-centre/
[post3]: https://kaistriega.com/blog/preferential-voting/who-keeps-one-nation-out/
[post4]: https://kaistriega.com/blog/preferential-voting/winning-from-behind/
[post5]: https://kaistriega.com/blog/preferential-voting/does-it-filter-out-extremists/
[appa]: https://kaistriega.com/blog/preferential-voting/appendix-a-measuring/
[appb]: https://kaistriega.com/blog/preferential-voting/appendix-b-nsw-ballots/
[appc]: https://kaistriega.com/blog/preferential-voting/appendix-c-bootstrap/
[appd]: https://kaistriega.com/blog/preferential-voting/appendix-d-breaking-it/
[appe]: https://kaistriega.com/blog/preferential-voting/appendix-e-data/
