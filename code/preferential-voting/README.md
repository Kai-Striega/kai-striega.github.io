# preferential-voting

The figures behind the [Polarisation and the Preferential Vote](https://kaistriega.com/blog/preferential-voting/)
series: back-of-the-envelope calculations on how Australians rate and rank their parties, and what preferential
voting does with those rankings.

The analysis itself (reading 15.8 million Senate ballots, the NSW ballots, the surveys and the House counts) is a
separate R project that isn't published here. What is here is everything needed to redraw the posts' charts:

- [`data/`](data/): copies of the analysis's output files that the charts and posts quote.
- [`charts.py`](charts.py): draws every chart as a house-style SVG (the site's palette, font and dark-mode block)
  into `static/images/preferential-voting/`.

Standard library only:

```shell
python3 code/preferential-voting/charts.py
```

| File | What it is |
|---|---|
| `trends.csv` | Survey trend measures with bootstrap intervals (partisan gap, share rating some party 0, ...) |
| `regression.csv` | Every survey-regression estimate: intercepts, slopes, adjusted ratings, by year and specification |
| `isolation_national.csv` | 2025 Senate last places relative to ballot position, by party |
| `position_effects.csv` | The ballot-column effects from the conditional logit |
| `squeeze_contests.csv` | Every House contest counted with Senate ballots, 2016–2025 |
| `fptp_sensitivity.csv` | Inputs for the first-past-the-post tactical-voting check |
| `nsw_contests.csv`, `nsw_proxy.csv` | NSW lower-house contests, and the Senate-style stand-in test |
| `transfer_model.csv` | Preference attraction relative to a same-size Labor candidate |
| `bloc_preferences.csv` | How each bloc ranks One Nation, by ballot type, state and year |
| `house_final_two.csv`, `house_overturns.csv`, `house_overturn_flows.csv` | Final twos and seats won from behind |
| `bootstrap_replicates.csv`, `bootstrap_summary.csv`, `squeeze_bootstrap.csv` | Booth and single-ballot resampling |
