"""
market_data.py
==============
Responsável por coletar dados de mercado da Binance via ccxt.
Suporta múltiplos timeframes hierárquicos com paginação automática.
"""

import time
import ccxt
import pandas as pd
from typing import Optional, List, Dict

_exchange: Optional[ccxt.binance] = None

def get_exchange() -> ccxt.binance:
    global _exchange
    if _exchange is None:
        _exchange = ccxt.binance({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"}
        })
    return _exchange

def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
    if timeframe is None:
        return pd.DataFrame()

    exchange  = get_exchange()
    per_page  = 1000
    all_rows  = []

    if limit <= per_page:
        # Requisição única
        try:
            all_rows = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except ccxt.BaseError as e:
            raise ConnectionError(f"Erro ao buscar dados de {symbol} [{timeframe}]: {e}")
    else:
        # Paginação: busca de trás pra frente usando `since`
        tf_ms = exchange.parse_timeframe(timeframe) * 1000  # duração em ms
        since = exchange.milliseconds() - (limit * tf_ms)

        while len(all_rows) < limit:
            try:
                batch = exchange.fetch_ohlcv(
                    symbol, timeframe=timeframe,
                    since=since, limit=per_page
                )
            except ccxt.BaseError as e:
                raise ConnectionError(f"Erro ao buscar dados de {symbol} [{timeframe}]: {e}")

            if not batch:
                break

            all_rows += batch
            since     = batch[-1][0] + tf_ms

            if len(batch) < per_page:
                break

            time.sleep(exchange.rateLimit / 1000)

        # Remove duplicatas e mantém os `limit` candles mais recentes
        seen = set()
        deduped = []
        for row in all_rows:
            if row[0] not in seen:
                seen.add(row[0])
                deduped.append(row)
        all_rows = sorted(deduped, key=lambda x: x[0])[-limit:]

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df

def get_timeframe_hierarchy(primary: str) -> dict:
    hierarchies = {
        "1m":  {"tfs": ["1m", "5m", "15m"],   "mode": "Scalp / Extreme Noise"},
        "15m": {"tfs": ["15m", "1h", "4h"],   "mode": "Intraday / High Noise"},
        "1h":  {"tfs": ["1h", "4h", "1d"],    "mode": "Short-Swing / Tactical"},
        "4h":  {"tfs": ["4h", "1d", "1w"],    "mode": "Swing / Medium Structure"},
        "1d":  {"tfs": ["1d", "1w", "1M"],    "mode": "Position / Structural Swing"},
        "1w":  {"tfs": ["1w", "1M", None],    "mode": "Macro / Long-Term Structure"},
        "1M":  {"tfs": ["1M", None, None],    "mode": "Deep Macro / Cycle Investment"}
    }
    return hierarchies.get(primary, hierarchies["1d"])

def fetch_hierarchical_timeframes(symbol: str, primary_tf: str) -> dict:
    h_data = get_timeframe_hierarchy(primary_tf)
    tfs    = h_data["tfs"]

    result = {}
    result["primary"]   = fetch_ohlcv(symbol, timeframe=tfs[0])
    result["secondary"] = fetch_ohlcv(symbol, timeframe=tfs[1]) if tfs[1] else pd.DataFrame()
    result["tertiary"]  = fetch_ohlcv(symbol, timeframe=tfs[2]) if tfs[2] else pd.DataFrame()
    result["mode"]      = h_data["mode"]
    result["tf_labels"] = tfs

    return result
