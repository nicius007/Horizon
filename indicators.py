"""
indicators.py
=============
Calcula indicadores técnicos sobre DataFrames de candles OHLCV.
Tolerante a histórico curto (útil para timeframe mensal).
"""

import pandas as pd
import numpy as np
import ta

def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
    if len(df) < period:
        return pd.Series([np.nan] * len(df), index=df.index)
    return ta.trend.ema_indicator(df["close"], window=period)

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if len(df) <= period:
        return pd.Series([np.nan] * len(df), index=df.index)
    return ta.momentum.rsi(df["close"], window=period)

def calculate_macd(df: pd.DataFrame) -> dict:
    if len(df) < 26:
        nans = pd.Series([np.nan] * len(df), index=df.index)
        return {"macd": nans, "signal": nans, "hist": nans}
    macd_obj = ta.trend.MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
    return {
        "macd":   macd_obj.macd(),
        "signal": macd_obj.macd_signal(),
        "hist":   macd_obj.macd_diff(),
    }

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if len(df) <= period:
        return pd.Series([np.nan] * len(df), index=df.index)
    return ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=period)

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if len(df) <= period * 2:
        return pd.Series([np.nan] * len(df), index=df.index)
    try:
        return ta.trend.adx(df["high"], df["low"], df["close"], window=period)
    except Exception:
        return pd.Series([np.nan] * len(df), index=df.index)

def calculate_all(df: pd.DataFrame) -> dict:
    if df is None or df.empty or len(df) < 30:
        return {}

    try:
        macd_data  = calculate_macd(df)
        atr_series = calculate_atr(df)

        resistance_20 = df["high"].rolling(min(20, len(df))).max()
        support_20    = df["low"].rolling(min(20, len(df))).min()

        def get_last(series):
            try:
                if series is None or (hasattr(series, 'empty') and series.empty):
                    return "N/A"
                val = series.iloc[-1]
                return "N/A" if pd.isna(val) else round(float(val), 4)
            except Exception:
                return "N/A"

        def get_prev(series):
            try:
                if series is None or len(series) < 2:
                    return "N/A"
                val = series.iloc[-2]
                return "N/A" if pd.isna(val) else round(float(val), 4)
            except Exception:
                return "N/A"

        return {
            "ema_20":         get_last(calculate_ema(df, 20)),
            "ema_50":         get_last(calculate_ema(df, 50)),
            "ema_200":        get_last(calculate_ema(df, 200)),
            "rsi":            get_last(calculate_rsi(df)),
            "macd":           get_last(macd_data["macd"]),
            "macd_signal":    get_last(macd_data["signal"]),
            "macd_hist":      get_last(macd_data["hist"]),
            "macd_hist_prev": get_prev(macd_data["hist"]),
            "atr":            get_last(atr_series),
            "avg_atr_14":     get_last(atr_series.rolling(min(14, len(atr_series))).mean()),
            "adx":            get_last(calculate_adx(df)),
            "close":          get_last(df["close"]),
            "volume":         get_last(df["volume"]),
            "avg_volume":     get_last(df["volume"].rolling(min(20, len(df))).mean()),
            "res_20":         get_last(resistance_20),
            "sup_20":         get_last(support_20),
        }
    except Exception:
        return {}
