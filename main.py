"""
main.py
=======
Ponto de entrada do Horizon. Interativo e Timeframe-Aware.
"""

import time
from rich.console import Console
from rich.prompt import IntPrompt

from market_data import fetch_hierarchical_timeframes
from indicators import calculate_all
from scoring import process_hierarchical_data
from ai_analysis import get_ai_analysis
from dashboard import render_dashboard

console = Console()

def select_timeframe() -> str:
    console.print("\n[bold cyan]Selecione o Timeframe Primário Operacional:[/bold cyan]")
    console.print("1 - 1m  (Scalp)")
    console.print("2 - 15m (Intraday)")
    console.print("3 - 1H  (Short-Swing)")
    console.print("4 - 4H  (Swing)")
    console.print("5 - 1D  (Position)")
    console.print("6 - 1W  (Macro)")
    console.print("7 - 1M  (Deep Macro)")
    
    choice = IntPrompt.ask("Escolha uma opção", choices=["1", "2", "3", "4", "5", "6", "7"], default=5)
    
    tf_map = {1: "1m", 2: "15m", 3: "1h", 4: "4h", 5: "1d", 6: "1w", 7: "1M"}
    return tf_map[int(choice)]

def run_analysis_for_symbol(symbol: str, primary_tf: str):
    with console.status(f"[bold green]Analisando hierarquia para {symbol} em {primary_tf}...", spinner="dots"):
        try:
            raw_hierarchical = fetch_hierarchical_timeframes(symbol, primary_tf)
            
            hierarchical_data = {
                "inds_primary": calculate_all(raw_hierarchical["primary"]),
                "inds_secondary": calculate_all(raw_hierarchical["secondary"]) if not raw_hierarchical["secondary"].empty else {},
                "inds_tertiary": calculate_all(raw_hierarchical["tertiary"]) if not raw_hierarchical["tertiary"].empty else {},
                "symbol": symbol,
                "mode": raw_hierarchical["mode"],
                "tf_labels": raw_hierarchical["tf_labels"]
            }
            
            score_data = process_hierarchical_data(hierarchical_data, symbol=symbol)
            
            ai_data = get_ai_analysis(symbol, score_data, hierarchical_data)
            
        except Exception as e:
            console.print(f"[bold red]Erro ao processar {symbol}: {e}[/bold red]")
            return
            
    render_dashboard(symbol, score_data, ai_data, hierarchical_data)

def main():
    console.print("\n[bold blue]🚀 Iniciando Horizon - O seu Copiloto de Mesa de Operações[/bold blue]\n")
    
    primary_tf = select_timeframe()
    console.print(f"\n[dim]Iniciando análise com foco em {primary_tf}...[/dim]\n")
    
    symbols = ["BTC/USDT", "ETH/USDT"]
    for symbol in symbols:
        run_analysis_for_symbol(symbol, primary_tf)
        time.sleep(2)
        
    console.print("\n[dim]Análise concluída. Proteja seu capital.[/dim]\n")

if __name__ == "__main__":
    main()
