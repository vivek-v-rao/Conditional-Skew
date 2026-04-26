"""Generic residual diagnostic reporting helpers."""
import numpy as np
from scipy.stats import kurtosis, skew


def print_residual_stats(res, ser_model):
    fitted = res.fittedvalues
    actual = ser_model.loc[fitted.index]
    resid = actual - fitted
    nresid = len(resid)
    se_mean = resid.std(ddof=1) / np.sqrt(nresid)
    se_sd = resid.std(ddof=1) / np.sqrt(2.0 * max(nresid - 1, 1))
    se_skew = np.sqrt(6.0 / nresid)
    se_ex_kurt = np.sqrt(24.0 / nresid)
    print("\nresidual stats")
    print(f"{'':>8}{'mean':>10}{'sd':>10}{'skew':>10}{'ex kurt':>10}")
    print(
        f"{'est':>8}{resid.mean():10.3f}{resid.std(ddof=1):10.3f}"
        f"{skew(resid, bias=False):10.3f}"
        f"{kurtosis(resid, fisher=True, bias=False):10.3f}"
    )
    print(
        f"{'se':>8}{se_mean:10.3f}{se_sd:10.3f}"
        f"{se_skew:10.3f}{se_ex_kurt:10.3f}"
    )

