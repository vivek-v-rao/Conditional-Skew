"""Reporting helpers specific to Markov autoregression fits."""
from pathlib import Path

import numpy as np
import pandas as pd


def print_regime_details(res, ser_original, ser_name, order, write_probs_csv,
        probs_csv_path, print_regime_ranges):
    if not hasattr(res, "smoothed_marginal_probabilities"):
        return
    probs = res.smoothed_marginal_probabilities
    print("\nsmoothed regime probabilities, first and last rows")
    print(pd.concat([probs.head(3), probs.tail(3)]).to_string())
    print("\nsample-average regime probabilities and probability-weighted series levels")
    avg_probs = probs.mean(axis=0)
    ser_original_fit = ser_original.iloc[order:].to_numpy()
    print(f"{'state':>8}{'prob':>12}{'avg level':>14}")
    state_order = np.argsort(-avg_probs.to_numpy())
    for ireg in state_order:
        prob = avg_probs.iloc[ireg]
        weights = probs.iloc[:, ireg].to_numpy()
        avg_level = np.sum(weights * ser_original_fit) / np.sum(weights)
        print(f"{ireg:8d}{prob:12.4f}{avg_level:14.3f}")
    if write_probs_csv:
        probs_path = Path(probs_csv_path)
        df_probs = pd.DataFrame(index=ser_original.index[order:])
        df_probs.index.name = "Date"
        df_probs[ser_name] = ser_original_fit
        for ireg in range(probs.shape[1]):
            df_probs[f"prob_state_{ireg}"] = probs.iloc[:, ireg].to_numpy()
        df_probs.to_csv(probs_path)
        print("\nwrote regime probabilities to:", str(probs_path))
    if not print_regime_ranges:
        return
    dates_fit = ser_original.index[order:]
    probs_np = probs.to_numpy()
    assigned_state = np.argmax(probs_np, axis=1)
    ranges = []
    start_idx = 0
    for i in range(1, len(assigned_state)):
        if assigned_state[i] != assigned_state[start_idx]:
            ranges.append((start_idx, i - 1))
            start_idx = i
    ranges.append((start_idx, len(assigned_state) - 1))
    print("\nregime date ranges")
    header = (
        f"{'date0':>12} {'dateT':>12} {'n':>5} {'reg':>5} {'x0':>10} "
        f"{'xT':>10} {'xmean':>10} {'xmin':>10} {'xmax':>10}"
    )
    for ireg in range(probs.shape[1]):
        header += f" {'p' + str(ireg + 1):>8}"
    print(header)
    durations_by_state = {ireg: [] for ireg in range(probs.shape[1])}
    for istart, iend in ranges:
        xseg = ser_original_fit[istart:iend + 1]
        prow = probs_np[istart]
        state = assigned_state[istart]
        durations_by_state[state].append(iend - istart + 1)
        row = (
            f"{str(dates_fit[istart]):>12} {str(dates_fit[iend]):>12} "
            f"{iend - istart + 1:5d} {state:5d} {xseg[0]:10.3f} "
            f"{xseg[-1]:10.3f} {np.mean(xseg):10.3f} {np.min(xseg):10.3f} "
            f"{np.max(xseg):10.3f}"
        )
        for prob in prow:
            row += f" {prob:8.3f}"
        print(row)
    print("\nregime duration stats")
    print(f"{'state':>8}{'mean':>10}{'median':>10}{'min':>10}{'max':>10}")
    for ireg in range(probs.shape[1]):
        durations = np.array(durations_by_state[ireg], dtype=float)
        if len(durations) == 0:
            print(f"{ireg:8d}{'n/a':>10}{'n/a':>10}{'n/a':>10}{'n/a':>10}")
        else:
            print(
                f"{ireg:8d}{np.mean(durations):10.2f}{np.median(durations):10.2f}"
                f"{np.min(durations):10.0f}{np.max(durations):10.0f}"
            )
