""" fit Markov-switching autoregressions over a range of regime counts """
import time
from datetime import date

import numpy as np
import pandas as pd
import statsmodels.api as sm

from markov_autoreg_report import print_regime_details
from pandas_util import print_first_last, read_csv_date_index
from residual_report import print_residual_stats


def optimizer_count_info(res, k_regimes):
    if k_regimes == 1:
        return ("iters", np.nan)
    mle_retvals = getattr(res, "mle_retvals", {})
    if "iterations" in mle_retvals:
        return ("iters", mle_retvals["iterations"])
    if "fcalls" in mle_retvals:
        return ("fcalls", mle_retvals["fcalls"])
    return ("iters", np.nan)


start = time.time()
pd.set_option("display.float_format", "{:.3f}".format)
np.set_printoptions(precision=3, suppress=True)

infile = "vix.csv"
date_min = date(1900, 1, 1)
date_max = date(2100, 12, 31)
col_use = 0
take_logs = True
min_regimes = 1
max_regimes = 3
order = 1
trend = "c"
switching_ar = False
switching_trend = True
switching_variance = True
em_iter = 20
search_reps = 20
write_probs_csv = False
probs_csv_stem = "temp_markov_probs"
print_regime_ranges = False

print("data file:", infile)
print("date_min:", date_min)
print("date_max:", date_max)
print("take_logs:", take_logs)
print("min_regimes:", min_regimes)
print("max_regimes:", max_regimes)
print("order:", order)
print("trend:", trend)
print("switching_ar:", switching_ar)
print("switching_trend:", switching_trend)
print("switching_variance:", switching_variance)
if write_probs_csv:
    print("probs_csv_stem:", probs_csv_stem)
print("print_regime_ranges:", print_regime_ranges)

df = read_csv_date_index(infile, date_min=date_min, date_max=date_max)
df = df.apply(pd.to_numeric, errors="coerce").astype(float)
ser = df.iloc[:, col_use].dropna()
if take_logs:
    ser_use = np.log(ser.where(ser > 0)).dropna()
    series_title = f"\nlog({ser.name})"
else:
    ser_use = ser.copy()
    series_title = f"\n{ser.name}"
ser_original = ser.loc[ser_use.index]
ser_model = pd.Series(ser_use.to_numpy(), name=ser.name)

print_first_last(ser_use, title=series_title)
print(ser_use.describe())

fit_rows = []
count_label = "iters"
for k_regimes in range(min_regimes, max_regimes + 1):
    fit_start = time.time()
    print(f"\n{'=' * 72}")
    print(f"fit for k_regimes = {k_regimes}")
    if k_regimes == 1:
        mod = sm.tsa.AutoReg(ser_model, lags=order, trend=trend, old_names=False)
        res = mod.fit()
    else:
        mod = sm.tsa.MarkovAutoregression(
            ser_model,
            k_regimes=k_regimes,
            order=order,
            trend=trend,
            switching_ar=switching_ar,
            switching_trend=switching_trend,
            switching_variance=switching_variance,
        )
        res = mod.fit(em_iter=em_iter, search_reps=search_reps, disp=False)
    print("\nmodel fit summary\n")
    print(res.summary())
    print("\nlog-likelihood:", f"{res.llf:.3f}")
    print("AIC:", f"{res.aic:.3f}")
    print("BIC:", f"{res.bic:.3f}")
    print_residual_stats(res, ser_model)
    count_label, optimizer_count = optimizer_count_info(res, k_regimes)
    if np.isnan(optimizer_count):
        print(f"{count_label}:", "n/a")
    else:
        print(f"{count_label}:", int(optimizer_count))
    fit_elapsed = time.time() - fit_start
    print("time elapsed (sec):", f"{fit_elapsed:0.2f}")
    if k_regimes > 1:
        print_regime_details(
            res=res,
            ser_original=ser_original,
            ser_name=ser.name,
            order=order,
            write_probs_csv=write_probs_csv,
            probs_csv_path=f"{probs_csv_stem}_{k_regimes}_regimes.csv",
            print_regime_ranges=print_regime_ranges,
        )
    fit_rows.append({
        "k_regimes": k_regimes,
        "aic": res.aic,
        "bic": res.bic,
        "optimizer_count": optimizer_count,
        "elapsed_sec": fit_elapsed,
    })

fit_df = pd.DataFrame(fit_rows)
aic_idx = fit_df["aic"].idxmin()
bic_idx = fit_df["bic"].idxmin()
fit_df["aic_diff"] = fit_df["aic"] - fit_df["aic"].min()
fit_df["bic_diff"] = fit_df["bic"] - fit_df["bic"].min()

print("\nAIC/BIC by # regimes")
print(
    f"{'#regimes':>10}{'AIC':>14}{'BIC':>14}{'AIC_diff':>12}"
    f"{'BIC_diff':>12}{count_label:>10}{'sec':>10}"
)
for _, row in fit_df.iterrows():
    count_text = "n/a" if pd.isna(row["optimizer_count"]) else str(int(row["optimizer_count"]))
    print(
        f"{int(row['k_regimes']):10d}{row['aic']:14.3f}{row['bic']:14.3f}"
        f"{row['aic_diff']:12.3f}{row['bic_diff']:12.3f}{count_text:>10}"
        f"{row['elapsed_sec']:10.2f}"
    )
print("\n# regimes chosen by AIC:", int(fit_df.loc[aic_idx, "k_regimes"]))
print("# regimes chosen by BIC:", int(fit_df.loc[bic_idx, "k_regimes"]))

print("\ntime elapsed (sec):", f"{time.time() - start:0.2f}")
