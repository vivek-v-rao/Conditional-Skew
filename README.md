# Conditional-Skew

This project fits autoregressive and regime-switching time-series models with non-Gaussian noise, starting from plain AR models and extending to GED, SGED, and level-dependent SGED specifications.

The current examples focus on `VIX` and `SPY`, with particular attention to whether the conditional distribution of noise changes as `VIX` changes, and whether latent Markov regimes improve fit relative to a single-regime AR model.

In terms of prior literature, there is extensive work on fitting GED innovations to financial returns and a smaller literature on fitting SGED distributions to returns or conditional-volatility models. By contrast, there appears to be comparatively little work on SGED models in which the scale, skewness, and tail-shape parameters are explicit functions of a lagged state variable such as the level or log-level of `VIX`. That is the main direction explored here.

A useful reference for the SGED itself is Panayiotis Theodossiou, [Skewed Generalized Error Distribution of Financial Assets and Option Pricing](https://ssrn.com/abstract=2693070)

## Files

From simplest to most complex:

- [xxar.py](/c:/python/liquids/xxar.py:1)  
  Fits ordinary autoregressive models to each time series in a CSV file, prints autocorrelations, and reports residual diagnostics.

- [ar_noise_report.py](/c:/python/liquids/ar_noise_report.py:1)  
  Shared reporting helpers for residual standard deviation, skew, excess kurtosis, and bin-by-bin summaries based on the previous level.

- [xar_ged.py](/c:/python/liquids/xar_ged.py:1)  
  Fits AR models with GED innovations. This allows heavy tails but not skewness.

- [ar_ged_model.py](/c:/python/liquids/ar_ged_model.py:1)  
  Core GED fitting utilities used by `xar_ged.py`.

- [xar_sged.py](/c:/python/liquids/xar_sged.py:1)  
  Fits AR models with skewed GED innovations, adds standard errors, implied skew and excess kurtosis, and supports analytic or numerical Hessians.

- [ar_sged_model.py](/c:/python/liquids/ar_sged_model.py:1)  
  Core SGED fitting code for constant-parameter models.

- [xar_sged_level.py](/c:/python/liquids/xar_sged_level.py:1)  
  Fits AR models where SGED noise parameters vary with the previous level or log-level of the series. This is the main single-series script.

- [ar_sged_level_model.py](/c:/python/liquids/ar_sged_level_model.py:1)  
  Core level-dependent SGED fitting utilities used by `xar_sged_level.py`.

- [xmarkov_autoreg_n_regimes.py](/c:/python/liquids/xmarkov_autoreg_n_regimes.py:1)  
  Fits Gaussian Markov-switching autoregressions using `statsmodels` over a range of regime counts, reports residual moment diagnostics, smoothed regime probabilities, probability-weighted regime levels, and compares AIC and BIC across `k_regimes`.

- [xvix_spy_sged.py](/c:/python/liquids/xvix_spy_sged.py:1)  
  Two-series application for `vix_spy.csv`. The first column is treated as the driver series (`VIX`), while the second column (`SPY`) is analyzed through returns and returns divided by lagged `VIX`.

## Model progression

The scripts reflect a progression in modeling assumptions:

1. `xxar.py`  
   Mean dynamics only. Residuals are examined after fitting a standard AR model.

2. `xar_ged.py`  
   Keeps the AR mean but replaces Gaussian noise with GED noise, allowing tail thickness to differ from normality.

3. `xar_sged.py`  
   Adds skewness to the innovation distribution. This allows the noise to be both heavy-tailed and asymmetric.

4. `xar_sged_level.py`  
   Allows the SGED parameters themselves to vary with the previous level. In practice this means volatility, skewness, and tail behavior can all change as the state variable changes.

5. `xmarkov_autoreg_n_regimes.py`  
   Lets the number of Markov regimes vary and selects the preferred count by information criteria.

6. `xvix_spy_sged.py`  
   Uses `VIX` as the state variable and studies both `SPY` returns and `SPY` returns normalized by lagged `VIX`.

## Main result from `xar_sged_level.py`

The key result is that a constant-noise SGED model is not enough for `log(VIX)`. A model in which the SGED noise parameters vary with the previous `log(VIX)` fits materially better.

### Setup

- Data file: `vix.csv`
- Date range: `1990-01-02` to `2026-04-24`
- Number of observations: `9145`
- AR order selected: `1`
- Trend specification: constant only (`trend = "c"`)
- Driver for time-varying noise parameters: previous `log(VIX)`

### Basic properties of the series

The autocorrelation function is extremely persistent:

- lag 1 ACF: `0.980`
- lag 12 ACF: `0.863`

So a persistent AR(1) structure is a reasonable baseline.

### Constant-parameter SGED benchmark

The benchmark AR(1)-SGED fit is:

- BIC: `-24735.690`
- AR coefficients: `[0.051, 0.977]`
- `beta = 1.111`
- `xi = 1.173`
- `scale = 0.054`

Interpretation:

- `beta < 2` implies heavier tails than Gaussian.
- `beta = 1.111` is also fairly close to the Laplace case `beta = 1`, so the fitted innovation density is much closer to Laplace-like than Gaussian.
- `xi > 1` implies positive skew in the fitted noise.
- The test for `xi = 1` gives `z = 11.712`, `p = 1.108e-31`, so the fitted skew is decisively nonzero.

The implied innovation moments from this constant-SGED fit are:

- implied skew: `0.565`
- implied excess kurtosis: `2.427`

### Level-dependent SGED model

The richer model lets the SGED parameters depend on a standardized previous-level driver `z`:

- `log(scale_t) = a0 + a1*z`
- `log(beta_t) = b0 + b1*z`
- `log(xi_t) = c0 + c1*z`

Estimated coefficients:

- AR coefficients: `[0.032, 0.984]`
- `a0 = -2.892`, `a1 = 0.167`
- `b0 = 0.142`, `b1 = 0.018`
- `c0 = 0.167`, `c1 = -0.036`

Interpretation:

- `a1 > 0`: the noise scale rises as `VIX` rises.
- `b1 > 0`: the GED shape parameter rises mildly with `VIX`.
- `c1 < 0`: the skew parameter falls as `VIX` rises.

### How the implied noise distribution changes with VIX

Across previous-VIX quantiles:

| q | VIX level | scale | beta | xi | implied skew | implied excess kurtosis |
|---|---:|---:|---:|---:|---:|---:|
| 1% | 10.160 | 0.042 | 1.116 | 1.258 | 0.779 | 2.591 |
| 5% | 11.430 | 0.044 | 1.123 | 1.243 | 0.735 | 2.504 |
| 10% | 12.140 | 0.045 | 1.127 | 1.235 | 0.713 | 2.461 |
| 25% | 13.960 | 0.049 | 1.135 | 1.217 | 0.661 | 2.365 |
| 50% | 17.620 | 0.054 | 1.150 | 1.187 | 0.574 | 2.214 |
| 75% | 22.763 | 0.062 | 1.166 | 1.155 | 0.479 | 2.063 |
| 90% | 28.597 | 0.069 | 1.180 | 1.127 | 0.395 | 1.942 |
| 95% | 32.989 | 0.074 | 1.189 | 1.110 | 0.343 | 1.872 |
| 99% | 46.766 | 0.088 | 1.212 | 1.070 | 0.218 | 1.721 |

The pattern is clear:

- higher `VIX` is associated with larger innovation scale
- higher `VIX` is associated with lower positive skew
- higher `VIX` is associated with lower implied excess kurtosis

So the conditional noise distribution changes meaningfully with the level of `VIX`, not just its variance.

### Model comparison

The BIC comparison is decisive:

- constant-parameter SGED BIC: `-24735.690`
- level-dependent SGED BIC: `-24925.226`
- delta BIC (level - constant): `-189.537`

Since lower BIC is better, BIC strongly favors the level-dependent noise model.

## Markov AR results from `vix_markov.txt`

The Markov-switching results give a different route to non-Gaussian behavior. Instead of making the innovation law depend explicitly on lagged `VIX`, they treat the series as switching across latent regimes with regime-specific intercepts and variances.

### Setup

- Data file: `vix.csv`
- Date range: `1990-01-02` to `2026-04-24`
- Series: `log(VIX)`
- AR order: `1`
- Trend: constant
- Switching AR coefficient: `False`
- Switching trend: `True`
- Switching variance: `True`
- Regime counts compared: `1`, `2`, and `3`

### Information-criterion comparison

The model comparison in `vix_markov.txt` is:

| # regimes | AIC | BIC |
|---|---:|---:|
| 1 | -23254.593 | -23233.231 |
| 2 | -25392.322 | -25342.476 |
| 3 | -25713.231 | -25620.660 |

Both AIC and BIC choose `3` regimes.

So a latent-regime Gaussian model substantially improves fit relative to a plain AR(1), and a 3-state version improves further on the 2-state version.

### Three-regime fit

For the preferred `3`-regime model:

- log-likelihood: `12869.616`
- AIC: `-25713.231`
- BIC: `-25620.660`
- AR coefficient: `0.9875`

The average regime probabilities and probability-weighted levels are:

| state | probability | avg level |
|---|---:|---:|
| 2 | 0.5564 | 17.925 |
| 1 | 0.3525 | 20.340 |
| 0 | 0.0911 | 25.480 |

This suggests:

- one dominant lower-level regime
- one medium-probability mid-level regime
- one relatively rare high-level regime

The regimes therefore line up reasonably well with low-, medium-, and high-VIX states.

### Residual moments

The residual moment diagnostics from `vix_markov.txt` are:

| # regimes | sd | skew | excess kurtosis |
|---|---:|---:|---:|
| 1 | 0.068 | 1.057 | 6.806 |
| 2 | 0.061 | 0.976 | 8.080 |
| 3 | 0.051 | 1.346 | 14.106 |

Two points matter here:

1. These moments show that the pooled one-step residuals remain strongly non-Gaussian.
2. In a Markov-switching Gaussian model, pooled residuals need not look Gaussian even when the regime-conditional errors are Gaussian, because they are a mixture over latent states.

So these residual moments are useful descriptively, but they are not a clean specification test for the Markov model in the same way they are for a single-regime Gaussian AR fit.

The right interpretation is:

- the Gaussian AR(1) model is plainly inadequate
- latent Markov regimes improve fit a great deal
- the pooled forecast errors still show large positive skew and excess kurtosis
- this is consistent with either remaining misspecification or simply the fact that a latent-state Gaussian mixture is non-Gaussian when pooled over time

### Markov AR versus level-dependent SGED

The two main approaches in the repository address non-Gaussian behavior differently:

- `xar_sged_level.py` uses an observed state variable, lagged `VIX`, to let the innovation law change deterministically with the previous level.
- `xmarkov_autoreg_n_regimes.py` uses latent regimes to let intercepts and variances change probabilistically over time.

So the Markov AR results do not replace the level-dependent SGED results. They provide a second lens on the same broad fact: `log(VIX)` is highly persistent, and its conditional distribution is not well described by a single Gaussian AR(1) innovation law.

## Using the scripts

The scripts are simple command-line programs with parameters set near the top of each file.

Typical controls include:

- input file name
- AR lag range
- trend specification
- date range
- whether to use logs
- whether to show AIC and/or BIC
- number of previous-level bins
- whether to fit constant or level-dependent SGED models
- number of Markov regimes to fit or compare
- whether to export regime probabilities

For the two-series `VIX`/`SPY` script, there are also toggles to turn the `SPY returns` and `SPY returns / VIX(t-1)` sections on or off.

## Summary

The main empirical message of this project is that for `VIX`, and for `SPY` returns conditioned on `VIX`, the distribution of innovations is not well described by a fixed Gaussian law. The codebase explores two complementary ways to capture that:

- observed-state models, where SGED parameters vary with lagged `VIX`
- latent-state models, where AR dynamics switch across hidden Markov regimes

Both approaches reject the idea that a single-regime Gaussian AR(1) is adequate for `log(VIX)`.
