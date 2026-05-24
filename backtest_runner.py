"""
backtest_runner.py
==================
Ponto de entrada para o backteste do Horizon.
Roda independente do main.py — não consome a API da Groq.
"""

import time
from rich.console import Console
from rich.prompt import IntPrompt, Confirm

from market_data import get_timeframe_hierarchy
from backtest import run_backtest

console = Console()

_TF_MAP = {1: "1m", 2: "15m", 3: "1h", 4: "4h", 5: "1d", 6: "1w", 7: "1M"}

_FW_SUGGESTIONS = {
    "1m": 20, "15m": 16, "1h": 12,
    "4h": 10, "1d": 8,  "1w": 6, "1M": 4,
}

_LOOKBACK_SUGGESTIONS = {
    "1m": 800, "15m": 700, "1h": 600,
    "4h": 500, "1d": 500,  "1w": 400, "1M": 300,
}


def select_timeframe() -> str:
    console.print("\n[bold cyan]Selecione o Timeframe Primário para o Backtest:[/bold cyan]")
    console.print("1 - 1m   (Scalp)")
    console.print("2 - 15m  (Intraday)")
    console.print("3 - 1H   (Short-Swing)")
    console.print("4 - 4H   (Swing)")
    console.print("5 - 1D   (Position)  [dim]← recomendado para começar[/dim]")
    console.print("6 - 1W   (Macro)")
    console.print("7 - 1M   (Deep Macro)")
    choice = IntPrompt.ask("Opção", choices=[str(i) for i in range(1, 8)], default=5)
    return _TF_MAP[int(choice)]


def main():
    console.print("\n[bold blue]🔬 Horizon — Backtest Walk-Forward[/bold blue]\n")
    console.print(
        "[dim]Este módulo testa o motor de score contra histórico real.\n"
        "Não usa a API da Groq — roda apenas indicadores + scoring.[/dim]\n"
    )

    primary_tf = select_timeframe()
    fw_default = _FW_SUGGESTIONS[primary_tf]
    lb_default = _LOOKBACK_SUGGESTIONS[primary_tf]

    console.print(f"\n[dim]Timeframe selecionado: [bold]{primary_tf}[/bold][/dim]")
    console.print(
        f"[dim]Janela forward sugerida: {fw_default} candles "
        f"| Lookback sugerido: {lb_default} candles[/dim]\n"
    )

    forward_window = IntPrompt.ask(
        f"Janela forward (candles a medir após o sinal)",
        default=fw_default
    )
    lookback = IntPrompt.ask(
        f"Lookback total (candles históricos a buscar)",
        default=lb_default
    )

    symbols = ["BTC/USDT", "ETH/USDT"]

    multi = Confirm.ask(
        "\nTestar apenas BTC/USDT e ETH/USDT?",
        default=True
    )
    if not multi:
        raw = console.input("[cyan]Digite os símbolos separados por vírgula: [/cyan]")
        symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]

    console.print(
        f"\n[dim]Iniciando backtest: {symbols} | TF {primary_tf} | "
        f"lookback {lookback} | fw {forward_window}[/dim]\n"
    )

    for symbol in symbols:
        result = run_backtest(
            symbol=symbol,
            primary_tf=primary_tf,
            lookback=lookback,
            forward_window=forward_window,
        )
        if "error" in result:
            console.print(f"[red]Erro em {symbol}: {result['error']}[/red]")
        time.sleep(1)

    console.print("\n[dim]Backtest concluído.[/dim]\n")


if __name__ == "__main__":
    main()
