"""
backtest.py
===========
Motor de backtesting walk-forward para o Horizon.

Metodologia:
  - Para cada barra i do histórico (a partir de min_history):
      * Usa APENAS df[:i+1] — zero look-ahead bias
      * Calcula indicadores e score como se fosse "agora"
      * Mede o que aconteceu nos próximos forward_window candles
  - Agrega resultados por bucket de score e exibe relatório

Limitação conhecida:
  - TFs secundário/terciário são gerados por resample do primário.
    A última barra do resample pode estar incompleta (candle em formação).
    Isso introduz ruído marginal aceitável para fins de calibração.
"""

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

from market_data import fetch_ohlcv, get_timeframe_hierarchy
from indicators import calculate_all
from scoring import process_hierarchical_data, detect_trend

console = Console()

# ─── Resample ────────────────────────────────────────────────────────────────

_TF_TO_PANDAS = {
    "1m": "1min", "5m": "5min", "15m": "15min",
    "1h": "1h",   "4h": "4h",   "1d": "1D",
    "1w": "1W",   "1M": "1ME",
}

def _resample(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    rule = _TF_TO_PANDAS.get(target_tf)
    if not rule or df.empty:
        return pd.DataFrame()
    try:
        resampled = (
            df.resample(rule, closed="left", label="left")
            .agg({"open": "first", "high": "max",
                  "low": "min",  "close": "last", "volume": "sum"})
            .dropna()
        )
        # Drop last bar — may be an incomplete (forming) candle
        return resampled.iloc[:-1] if len(resampled) > 1 else resampled
    except Exception:
        return pd.DataFrame()


# ─── Walk-Forward Engine ──────────────────────────────────────────────────────

def run_backtest(
    symbol: str,
    primary_tf: str,
    lookback: int = 600,
    forward_window: int = 10,
    min_history: int = 220,
) -> dict:
    """
    Executa o backteste walk-forward.

    Args:
        symbol:         Par a testar, ex: "BTC/USDT"
        primary_tf:     Timeframe primário, ex: "1h"
        lookback:       Quantos candles históricos buscar
        forward_window: Janela futura para medir resultado (em candles do TF primário)
        min_history:    Mínimo de candles antes de começar a pontuar (aquece indicadores)

    Returns:
        dict com summary por bucket, DataFrame bruto e métricas globais
    """

    h_meta = get_timeframe_hierarchy(primary_tf)
    tfs    = h_meta["tfs"]
    mode   = h_meta["mode"]

    console.print(f"\n[dim]Buscando {lookback + forward_window} candles de "
                  f"[bold]{symbol}[/bold] [{primary_tf}]...[/dim]")

    df_raw = fetch_ohlcv(symbol, primary_tf, limit=lookback + forward_window + 50)

    if df_raw.empty:
        return {"error": "Sem dados da API."}

    needed = min_history + forward_window + 5
    if len(df_raw) < needed:
        return {"error": f"Histórico insuficiente ({len(df_raw)} candles, precisa de {needed})."}

    # Pré-calcula secondary e tertiary completos (serão fatiados por timestamp)
    df_sec_full = _resample(df_raw, tfs[1]) if tfs[1] else pd.DataFrame()
    df_ter_full = _resample(df_raw, tfs[2]) if tfs[2] else pd.DataFrame()

    results      = []
    total_bars   = len(df_raw) - forward_window
    scan_range   = range(min_history, total_bars)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        BarColumn(),
        TextColumn("[cyan]{task.completed}/{task.total} barras"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Walk-forward {symbol} [{primary_tf}]",
            total=len(scan_range)
        )

        for i in scan_range:
            progress.advance(task)

            # ── Slice sem look-ahead ──────────────────────────────────────
            df_slice   = df_raw.iloc[:i + 1]
            current_ts = df_slice.index[-1]

            df_sec_slice = (df_sec_full[df_sec_full.index <= current_ts]
                            if not df_sec_full.empty else pd.DataFrame())
            df_ter_slice = (df_ter_full[df_ter_full.index <= current_ts]
                            if not df_ter_full.empty else pd.DataFrame())

            hierarchical = {
                "inds_primary":   calculate_all(df_slice),
                "inds_secondary": calculate_all(df_sec_slice) if not df_sec_slice.empty else {},
                "inds_tertiary":  calculate_all(df_ter_slice) if not df_ter_slice.empty else {},
                "symbol":         symbol,
                "mode":           mode,
                "tf_labels":      tfs,
            }

            try:
                score_data = process_hierarchical_data(hierarchical, symbol=symbol)
            except Exception:
                continue

            entry_price = float(df_raw.iloc[i]["close"])

            # ── Janela futura ─────────────────────────────────────────────
            future = df_raw.iloc[i + 1: i + 1 + forward_window]
            if len(future) < forward_window:
                continue

            trend = detect_trend(hierarchical["inds_primary"])
            is_long  = "Bullish" in trend
            is_short = "Bearish" in trend

            hi  = future["high"].max()
            lo  = future["low"].min()
            end = float(future.iloc[-1]["close"])

            if is_long:
                mfe          = (hi  - entry_price) / entry_price * 100
                mae          = (lo  - entry_price) / entry_price * 100
                final_return = (end - entry_price) / entry_price * 100
            elif is_short:
                mfe          = (entry_price - lo)  / entry_price * 100
                mae          = (entry_price - hi)  / entry_price * 100
                final_return = (entry_price - end) / entry_price * 100
            else:
                # Neutro: mede excursão sem direção
                mfe          =  max(abs(hi - entry_price), abs(lo - entry_price)) / entry_price * 100
                mae          = -mfe * 0.5
                final_return = (end - entry_price) / entry_price * 100

            results.append({
                "timestamp":      current_ts,
                "score":          score_data["score"],
                "classification": score_data["classification"],
                "direction":      score_data.get("direction", "N/A"),
                "rr_class":       score_data["rr_data"]["rr_class"],
                "entry":          entry_price,
                "return_pct":     round(final_return, 4),
                "mfe_pct":        round(mfe, 4),
                "mae_pct":        round(mae, 4),
                "won":            final_return > 0,
            })

    if not results:
        return {"error": "Nenhuma barra processada."}

    df_results = pd.DataFrame(results)
    return _analyze(df_results, symbol, primary_tf, forward_window)


# ─── Análise & Relatório ──────────────────────────────────────────────────────

_BUCKETS = [
    ("Ruim  (0–39)",        lambda df: df[df["score"] <  40]),
    ("Neutro (40–59)",      lambda df: df[(df["score"] >= 40) & (df["score"] < 60)]),
    ("Aceitável (60–79)",   lambda df: df[(df["score"] >= 60) & (df["score"] < 80)]),
    ("Alta Qual. (80–100)", lambda df: df[df["score"] >= 80]),
]

def _bucket_stats(group: pd.DataFrame) -> dict:
    if group.empty:
        return dict(count=0, win_rate=0, avg_ret=0, avg_mfe=0,
                    avg_mae=0, expectancy=0, sharpe=0)

    wins   = group[group["won"]]
    losses = group[~group["won"]]

    win_rate   = group["won"].mean() * 100
    avg_ret    = group["return_pct"].mean()
    avg_mfe    = group["mfe_pct"].mean()
    avg_mae    = group["mae_pct"].mean()
    avg_win    = wins["return_pct"].mean()   if not wins.empty   else 0.0
    avg_loss   = losses["return_pct"].mean() if not losses.empty else 0.0
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

    std = group["return_pct"].std()
    sharpe = (avg_ret / std * np.sqrt(252)) if std > 0 else 0.0

    return dict(
        count=len(group),
        win_rate=round(win_rate, 1),
        avg_ret=round(avg_ret, 3),
        avg_mfe=round(avg_mfe, 3),
        avg_mae=round(avg_mae, 3),
        expectancy=round(expectancy, 3),
        sharpe=round(sharpe, 2),
    )


def _analyze(df: pd.DataFrame, symbol: str, primary_tf: str, fw: int) -> dict:
    summary = [
        {"bucket": label, **_bucket_stats(fn(df))}
        for label, fn in _BUCKETS
    ]
    _render(summary, df, symbol, primary_tf, fw)
    return {
        "symbol": symbol, "primary_tf": primary_tf,
        "forward_window": fw, "total_bars": len(df),
        "summary": summary, "raw": df,
    }


_BUCKET_COLORS = {
    "Ruim  (0–39)":        "red",
    "Neutro (40–59)":      "yellow",
    "Aceitável (60–79)":   "green",
    "Alta Qual. (80–100)": "green1",
}

def _render(summary: list, df: pd.DataFrame, symbol: str, primary_tf: str, fw: int):
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", padding=(0, 1))
    cols = [
        ("Bucket de Score",  "bold white", False),
        ("N",                "white",       True),
        ("Win Rate",         "white",       True),
        ("Retorno Médio",    "white",       True),
        ("MFE Médio",        "white",       True),
        ("MAE Médio",        "white",       True),
        ("Expectativa",      "white",       True),
        ("Sharpe*",          "white",       True),
    ]
    for name, style, right in cols:
        table.add_column(name, style=style, justify="right" if right else "left", min_width=14)

    for row in summary:
        c   = _BUCKET_COLORS.get(row["bucket"], "white")
        ret_c = "green" if row["avg_ret"]    > 0 else "red"
        exp_c = "green" if row["expectancy"] > 0 else "red"

        table.add_row(
            f"[{c}]{row['bucket']}[/{c}]",
            str(row["count"]),
            f"[{c}]{row['win_rate']}%[/{c}]",
            f"[{ret_c}]{row['avg_ret']:+.3f}%[/{ret_c}]",
            f"{row['avg_mfe']:+.3f}%",
            f"{row['avg_mae']:+.3f}%",
            f"[{exp_c}]{row['expectancy']:+.3f}%[/{exp_c}]",
            f"{row['sharpe']:+.2f}",
        )

    global_wr  = df["won"].mean() * 100
    global_ret = df["return_pct"].mean()
    ret_c      = "green" if global_ret > 0 else "red"

    insight = _insight(summary, df)

    header = (
        f"[dim]Símbolo:[/dim] [bold yellow]{symbol}[/bold yellow]  "
        f"[dim]TF:[/dim] [bold cyan]{primary_tf}[/bold cyan]  "
        f"[dim]Janela:[/dim] {fw} candles  "
        f"[dim]Amostras:[/dim] {len(df)}\n"
        f"[dim]Win Rate global:[/dim] [bold]{global_wr:.1f}%[/bold]  "
        f"[dim]Retorno médio global:[/dim] [{ret_c}]{global_ret:+.3f}%[/{ret_c}]"
    )

    console.print(Panel(
        header,
        title="[bold blue]Horizon — Backtest Report[/bold blue]",
        box=box.DOUBLE_EDGE,
        border_style="blue",
        padding=(1, 2),
    ))
    console.print(table)
    console.print("[dim]  * Sharpe anualizado aproximado (assume 252 períodos/ano)[/dim]")
    console.print(f"\n  [bold yellow]► Diagnóstico:[/bold yellow] {insight}\n")


def _insight(summary: list, df: pd.DataFrame) -> str:
    msgs = []

    high = next((s for s in summary if "Alta" in s["bucket"]), None)
    low  = next((s for s in summary if "Ruim"  in s["bucket"]), None)
    valid = [s for s in summary if s["count"] >= 10]

    # Verifica se score alto performa melhor
    if high and high["count"] >= 10:
        if high["win_rate"] >= 60 and high["expectancy"] > 0:
            msgs.append(
                f"Score 80+ mostra [green]edge real[/green]: "
                f"{high['win_rate']}% win rate, expectativa {high['expectancy']:+.3f}%."
            )
        elif high["win_rate"] < 50:
            msgs.append(
                f"[red]Alerta:[/red] Score 80+ tem win rate de apenas {high['win_rate']}% — "
                f"pesos precisam de recalibração."
            )

    # Filro de baixa qualidade invertido?
    if low and low["count"] >= 10 and low["win_rate"] > 55:
        msgs.append(
            f"[yellow]Atenção:[/yellow] Score <40 tem {low['win_rate']}% win rate — "
            f"o filtro de baixa qualidade pode estar [bold]invertido[/bold]."
        )

    # Monotonicidade: score crescente → win rate crescente?
    if len(valid) >= 3:
        wrs = [s["win_rate"] for s in valid]
        monotonic = all(wrs[i] <= wrs[i + 1] for i in range(len(wrs) - 1))
        msgs.append(
            "Score [green]monotonicamente crescente[/green] — sistema discrimina qualidade de setup."
            if monotonic else
            "[yellow]Score não-monotônico[/yellow] — algum bucket com comportamento inesperado."
        )

    # RR class distribution
    rr_dist = df["rr_class"].value_counts(normalize=True) * 100
    poor_pct = rr_dist.get("Poor", 0)
    if poor_pct > 40:
        msgs.append(
            f"[red]{poor_pct:.0f}% dos setups têm RR Poor[/red] — "
            f"o cálculo de TP/SL pode estar muito conservador para este TF."
        )

    return " ".join(msgs) if msgs else "Amostras insuficientes para diagnóstico robusto."
