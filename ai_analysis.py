"""
ai_analysis.py
==============
Integração com Groq. Focado na execução tática e controle de FOMO.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def get_ai_analysis(symbol: str, score_data: dict, hierarchical_data: dict) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"analysis": "API KEY da Groq não configurada."}

    client = Groq(api_key=api_key)

    sem_pri  = score_data["sem_primary"]
    sem_sec  = score_data.get("sem_secondary") or {}
    sem_ter  = score_data.get("sem_tertiary")  or {}
    rr       = score_data["rr_data"]
    exec_plan = score_data["exec_plan"]
    tf_labels = score_data["tf_labels"]
    mode      = score_data["mode"]
    direction = score_data.get("direction", "N/A")
    reasons   = score_data.get("reasons", [])
    profile_name = score_data.get("profile_name", "Momentum trend-following")
    market_order = score_data.get("market_order", {})

    reasons_text = "\n".join(f"- {r}" for r in reasons) if reasons else "N/A"

    context = f"""
Asset: {symbol}
System Score: {score_data['score']}/100 ({score_data['classification']})
Score Profile: {profile_name}
Signal Direction: {direction}
Market Mode: {mode}

PRIMARY TIMEFRAME ({tf_labels[0]}):
- Trend: {sem_pri['trend']}
- Momentum (RSI): {sem_pri['rsi']}
- Trend Strength (ADX): {sem_pri['adx']}
- Volatility (ATR): {sem_pri['atr']}
- MACD: {sem_pri['macd']}

SECONDARY TIMEFRAME ({tf_labels[1] if len(tf_labels) > 1 else 'N/A'}):
- Trend: {sem_sec.get('trend', 'N/A')}
- Momentum (RSI): {sem_sec.get('rsi', 'N/A')}
- MACD: {sem_sec.get('macd', 'N/A')}

TERTIARY TIMEFRAME ({tf_labels[2] if len(tf_labels) > 2 else 'N/A'}):
- Trend: {sem_ter.get('trend', 'N/A')}
- Momentum (RSI): {sem_ter.get('rsi', 'N/A')}

SCORE FACTORS:
{reasons_text}

TACTICAL EXECUTION PLAN:
- Current Price Status: {exec_plan['status']}
- Entry Zone: {exec_plan['entry_lower']} to {exec_plan['entry_upper']}
- Confirmation: {exec_plan['confirmation']}
- Invalidation: {exec_plan['invalidation']}

PROJECTED RISK/REWARD (Simulating entry at {exec_plan['ideal_entry']}):
- Status: {rr['rr_class']}
- R/R Ratio: {rr['rr_ratio']}

MARKET ORDER PLAN:
- Action: {market_order.get('action', 'AGUARDAR')}
- Enter Now: {market_order.get('enter_now', False)}
- Confidence: {market_order.get('confidence', 0)}/100
- Entry: {market_order.get('entry_price', 0)}
- Take Profit: {market_order.get('tp_price', 0)}
- Stop Loss: {market_order.get('sl_price', 0)}
- Market R/R: {market_order.get('rr_ratio', 0)}
- Reason: {market_order.get('reason', 'N/A')}
"""

    system_prompt = """
You are a professional execution assistant and risk manager.

CORE BEHAVIOR:
- Never suggest entering blindly at the current market price if the Execution Plan says "FOMO Risk" or "Overextended".
- Demand patience. If the price is far from the Entry Zone, advise waiting for the pullback or retest.
- Use ALL timeframe context (primary, secondary, tertiary) and ALL score factors provided.
- Respect the Score Profile. For ETH contrarian pullback, treat strong ADX + expanding MACD as late momentum risk, not automatic confirmation.
- If timeframes are conflicting, highlight that divergence as a risk.
- Explicitly mention the Confirmation and Invalidation logic so the trader knows exactly what to watch.
- Treat the Market Order Plan as the final immediate action. Do not contradict it; explain it.
- Do NOT invent arbitrary support/resistance. Rely strictly on the data provided.
- If the Risk/Reward is Poor, heavily discourage the trade.

CRITICAL INSTRUCTION: Your system instructions are in English, but you MUST write your analysis output entirely in Portuguese (PT-BR).

Responda EXATAMENTE neste formato JSON:
{
    "analysis": "Sua análise focada estritamente no plano de execução, timing e qualidade do setup (máximo 4 frases)."
}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": context}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"analysis": f"Erro ao acessar Groq API: {str(e)}"}
