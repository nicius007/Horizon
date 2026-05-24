"""
dashboard.py
============
Renderiza o painel do Horizon com Execução Tática e Fatores de Score.
"""

from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()

def render_dashboard(symbol: str, score_data: dict, ai_data: dict, hierarchical_data: dict):
    ind_pri        = hierarchical_data["inds_primary"]
    rr             = score_data["rr_data"]
    exec_plan      = score_data["exec_plan"]
    market_order   = score_data.get("market_order", {})
    tf_labels      = score_data["tf_labels"]
    direction      = score_data.get("direction", "N/A")
    direction_color = score_data.get("direction_color", "white")
    reasons        = score_data.get("reasons", [])
    profile_name   = score_data.get("profile_name", "Momentum trend-following")

    score_val = score_data["score"]
    if score_val >= 80:   score_color = "green1"
    elif score_val >= 60: score_color = "green3"
    elif score_val >= 40: score_color = "yellow"
    else:                 score_color = "red"

    if "FOMO" in exec_plan["status"]:       status_color = "red bold"
    elif "Optimal" in exec_plan["status"]:  status_color = "green1 bold"
    else:                                   status_color = "yellow"

    rr_class = rr["rr_class"]
    if rr_class == "Poor":       rr_color = "red"
    elif rr_class == "Weak":     rr_color = "yellow"
    elif rr_class == "Acceptable": rr_color = "green"
    else:                        rr_color = "green1 bold"

    market_action = market_order.get("action", "AGUARDAR")
    market_color = "green1 bold" if market_order.get("enter_now") else "yellow bold"

    # Fatores de score formatados
    reasons_lines = "\n".join(f"  [dim]•[/dim] {r}" for r in reasons) if reasons else "  [dim]N/A[/dim]"

    content = f"""[bold blue]Primary Timeframe:[/bold blue] [bold cyan]{tf_labels[0]}[/bold cyan]  |  [bold blue]Market Mode:[/bold blue] [bold magenta]{score_data['mode']}[/bold magenta]  |  [bold blue]Score Profile:[/bold blue] [bold magenta]{profile_name}[/bold magenta]

[bold cyan]Score:[/bold cyan] [{score_color}]{score_val}/100 — {score_data['classification']}[/{score_color}]
[bold cyan]Direção:[/bold cyan] [{direction_color}]{direction}[/{direction_color}]

[bold green]=== OPERACAO A MERCADO ===[/bold green]
[bold]Acao:[/bold] [{market_color}]{market_action}[/{market_color}]
[bold]Confianca:[/bold] {market_order.get('confidence', 0)}/100  |  [bold]Urgencia:[/bold] {market_order.get('urgency', 'Baixa')}
[bold]Entrada agora:[/bold] ${market_order.get('entry_price', 0)}
[bold]Take Profit:[/bold] ${market_order.get('tp_price', 0)} (+{market_order.get('reward_pct', 0)}%)
[bold]Stop Loss:[/bold]   ${market_order.get('sl_price', 0)} (-{market_order.get('risk_pct', 0)}%)
[bold]RR mercado:[/bold] {market_order.get('rr_ratio', 0)}
[dim]{market_order.get('reason', 'N/A')}[/dim]

[bold white]=== FATORES DO SCORE ===[/bold white]
{reasons_lines}

[bold yellow]=== TACTICAL EXECUTION PLAN ===[/bold yellow]
[bold]Status:[/bold] [{status_color}]{exec_plan['status']}[/{status_color}]
[bold]Entry Zone:[/bold] {exec_plan['entry_lower']} — {exec_plan['entry_upper']}
[bold]Confirmation:[/bold] {exec_plan['confirmation']}
[bold]Invalidation:[/bold] {exec_plan['invalidation']}

[bold magenta]=== PROJECTED RISK / REWARD ===[/bold magenta]
[dim](Simulating entry at {exec_plan['ideal_entry']})[/dim]
Ratio: [{rr_color}]{rr['rr_ratio']}[/{rr_color}] ([{rr_color}]{rr_class}[/{rr_color}])
Take Profit: ${rr['tp_price']} (+{rr['reward_pct']}%)
Stop Loss:   ${rr['sl_price']} (-{rr['risk_pct']}%)

[bold blue]=== HORIZON COPILOT ADVICE ===[/bold blue]
"{ai_data.get('analysis', 'Sem análise gerada.')}"
"""

    panel = Panel(
        content,
        title=f"[bold blue]Horizon V4[/bold blue] | [bold yellow]{symbol}[/bold yellow] | Current Price: ${ind_pri.get('close', 'N/A')}",
        box=box.DOUBLE_EDGE,
        border_style="blue",
        padding=(1, 2)
    )

    console.print(panel)
