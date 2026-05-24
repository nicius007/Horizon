"""
scoring.py
==========
Motor de score usando todos os 15 indicadores calculados.
Direction-neutral: setups bullish e bearish fortes pontuam igualmente.
"""

SCORING_PROFILES = {
    "DEFAULT": {
        "name": "Momentum trend-following",
        "pri_sec_aligned": 20,
        "pri_sec_conflict": -10,
        "ter_aligned": 10,
        "ter_conflict": -5,
        "adx_strong": 15,
        "adx_moderate": 5,
        "adx_weak": -10,
        "macd_expanding": 15,
        "macd_fading": 5,
        "macd_recovering": -5,
        "macd_divergence": -15,
        "macd_neutral": 5,
        "late_momentum_penalty": 0,
    },
    "ETH": {
        "name": "ETH contrarian pullback",
        "pri_sec_aligned": 8,
        "pri_sec_conflict": -5,
        "ter_aligned": 3,
        "ter_conflict": 0,
        "adx_strong": -8,
        "adx_moderate": 3,
        "adx_weak": -5,
        "macd_expanding": -12,
        "macd_fading": 8,
        "macd_recovering": 3,
        "macd_divergence": -10,
        "macd_neutral": 5,
        "late_momentum_penalty": -20,
    },
}


def _asset_key(symbol: str | None) -> str:
    if not symbol:
        return "DEFAULT"

    base = str(symbol).upper().split("/")[0].split("-")[0]
    if base == "ETH":
        return "ETH"
    return "DEFAULT"


def _profile_delta(profile: dict, key: str, fallback: int = 0) -> int:
    return int(profile.get(key, fallback))


def _append_reason(reasons: list, text: str, delta: int):
    sign = "+" if delta > 0 else ""
    reasons.append(f"{text} ({sign}{delta})")


def detect_trend(ind: dict) -> str:
    close = ind.get("close", "N/A")
    ema20 = ind.get("ema_20", "N/A")
    ema50 = ind.get("ema_50", "N/A")
    ema200 = ind.get("ema_200", "N/A")

    if close == "N/A" or ema20 == "N/A" or ema50 == "N/A":
        return "Insufficient Data for Structure"

    if ema200 != "N/A":
        if close > ema20 > ema50 > ema200:
            return "Strong Bullish (Aligned Structure)"
        elif close < ema20 < ema50 < ema200:
            return "Strong Bearish (Aligned Structure)"

    if close > ema50 and ema20 > ema50:
        return "Bullish Structure"
    elif close < ema50 and ema20 < ema50:
        return "Bearish Structure"
    else:
        return "Neutral / Sideways Compression"


def generate_semantic_context(ind: dict, trend: str) -> dict:
    if not ind:
        return {"trend": "N/A", "rsi": "N/A", "adx": "N/A", "atr": "N/A", "macd": "N/A"}

    rsi = ind.get("rsi", "N/A")
    if rsi == "N/A":              rsi_sem = "N/A"
    elif rsi < 30:                rsi_sem = "Oversold condition"
    elif rsi < 45:                rsi_sem = "Weakening momentum"
    elif rsi <= 55:               rsi_sem = "Neutral momentum"
    elif rsi <= 70:               rsi_sem = "Strengthening momentum"
    else:                         rsi_sem = "Overbought condition"

    adx = ind.get("adx", "N/A")
    if adx == "N/A":              adx_sem = "N/A"
    elif adx < 20:                adx_sem = "Weak trend strength / Ranging"
    elif adx <= 25:               adx_sem = "Moderate trend strength"
    else:                         adx_sem = "Strong directional trend"

    atr = ind.get("atr", "N/A")
    avg_atr = ind.get("avg_atr_14", "N/A")
    if atr == "N/A" or avg_atr == "N/A": atr_sem = "N/A"
    elif atr > avg_atr * 1.5:    atr_sem = "Unstable / Explosive Volatility"
    elif atr > avg_atr * 1.1:    atr_sem = "Expanding Volatility"
    elif atr < avg_atr * 0.7:    atr_sem = "Low Volatility / Compression"
    else:                         atr_sem = "Controlled Volatility"

    hist = ind.get("macd_hist", "N/A")
    hist_prev = ind.get("macd_hist_prev", "N/A")
    if hist == "N/A" or hist_prev == "N/A": macd_sem = "N/A"
    elif hist > 0 and hist > hist_prev:  macd_sem = "Bullish momentum strengthening"
    elif hist > 0 and hist <= hist_prev: macd_sem = "Bullish momentum fading"
    elif hist < 0 and hist < hist_prev:  macd_sem = "Bearish momentum strengthening"
    else:                                macd_sem = "Bearish momentum fading"

    return {
        "trend": trend,
        "rsi": rsi_sem,
        "adx": adx_sem,
        "atr": atr_sem,
        "macd": macd_sem,
    }


def calculate_execution_plan(ind: dict, trend: str) -> dict:
    """Calcula Zonas de Entrada, Validação e Invalidação tática."""
    if not ind or ind.get("close", "N/A") == "N/A":
        return {"entry_lower": 0, "entry_upper": 0, "status": "N/A",
                "confirmation": "N/A", "invalidation": "N/A", "ideal_entry": 0}

    close = ind["close"]
    ema20 = ind.get("ema_20", close)
    ema50 = ind.get("ema_50", close)
    sup20 = ind.get("sup_20", close)
    res20 = ind.get("res_20", close)
    atr   = ind.get("atr", close * 0.02)

    if "Bullish" in trend:
        entry_upper = ema20
        entry_lower = max(ema50, sup20)
        if entry_lower > entry_upper:
            entry_upper, entry_lower = entry_lower, entry_upper
        confirmation = "Sustentar suporte na EMA 20 com momentum direcional crescente."
        invalidation = "Perda da EMA 50 e falha na defesa do suporte local."
        if close > entry_upper + (atr * 1.5):
            status = "FOMO Risk / Overextended (Wait for Pullback)"
        elif close < entry_lower:
            status = "Structure Broken / Caution"
        else:
            status = "Optimal Pullback Zone"

    elif "Bearish" in trend:
        entry_lower = ema20
        entry_upper = min(ema50, res20)
        if entry_lower > entry_upper:
            entry_upper, entry_lower = entry_lower, entry_upper
        confirmation = "Rejeição clara na EMA 20 com aumento de pressão vendedora."
        invalidation = "Rompimento e consolidação acima da EMA 50."
        if close < entry_lower - (atr * 1.5):
            status = "FOMO Risk / Overextended (Wait for Retest)"
        elif close > entry_upper:
            status = "Structure Broken / Caution"
        else:
            status = "Optimal Retest Zone"

    else:
        entry_lower = sup20
        entry_upper = res20
        confirmation = "Defesa clara do suporte (compras) ou rejeição na resistência (vendas)."
        invalidation = "Rompimento direcional sólido fora do caixote."
        if close > entry_upper - (atr * 0.5):
            status = "Resistance Proximity (Avoid Longs)"
        elif close < entry_lower + (atr * 0.5):
            status = "Support Proximity (Optimal for Longs)"
        else:
            status = "Middle of Range (Chop Zone)"

    return {
        "entry_lower":  round(entry_lower, 2),
        "entry_upper":  round(entry_upper, 2),
        "ideal_entry":  round((entry_lower + entry_upper) / 2, 2),
        "status":       status,
        "confirmation": confirmation,
        "invalidation": invalidation,
    }


def calculate_risk_reward_projected(ind: dict, ideal_entry: float, trend: str) -> dict:
    """Calcula RR simulando a entrada no preço IDEAL (Projected Entry)."""
    if not ind or ind.get("close", "N/A") == "N/A":
        return {"rr_class": "N/A", "rr_ratio": 0, "tp_price": 0,
                "sl_price": 0, "risk_pct": 0, "reward_pct": 0}

    close  = ind["close"]
    atr    = ind.get("atr",    0)    if ind.get("atr",    "N/A") != "N/A" else close * 0.02
    res_20 = ind.get("res_20", None) if ind.get("res_20", "N/A") != "N/A" else None
    sup_20 = ind.get("sup_20", None) if ind.get("sup_20", "N/A") != "N/A" else None

    if "Bearish" in trend:
        tp_price = (sup_20 if sup_20 and sup_20 < ideal_entry * 0.99
                    else ideal_entry - (atr * 3))
        sl_price = ideal_entry + (atr * 1.5)
        risk     = sl_price - ideal_entry
        reward   = ideal_entry - tp_price
    else:
        tp_price = (res_20 if res_20 and res_20 > ideal_entry * 1.01
                    else ideal_entry + (atr * 3))
        sl_price = ideal_entry - (atr * 1.5)
        risk     = ideal_entry - sl_price
        reward   = tp_price - ideal_entry

    rr_ratio = reward / risk if risk > 0 else 0

    if rr_ratio < 1.0:   rr_class = "Poor"
    elif rr_ratio < 1.5: rr_class = "Weak"
    elif rr_ratio < 2.0: rr_class = "Acceptable"
    else:                rr_class = "Strong"

    return {
        "tp_price":   round(tp_price, 2),
        "sl_price":   round(sl_price, 2),
        "rr_ratio":   round(rr_ratio, 2),
        "rr_class":   rr_class,
        "risk_pct":   round((risk   / ideal_entry) * 100, 2) if risk   > 0 else 0,
        "reward_pct": round((reward / ideal_entry) * 100, 2) if reward > 0 else 0,
    }


def calculate_market_order_plan(
    ind: dict,
    trend: str,
    score: int,
    exec_plan: dict,
    rr_data: dict,
    mode: str,
) -> dict:
    """Monta a melhor decisao possivel para entrada imediata a mercado."""
    if not ind or ind.get("close", "N/A") == "N/A":
        return {
            "action": "AGUARDAR",
            "side": "N/A",
            "enter_now": False,
            "confidence": 0,
            "entry_price": 0,
            "tp_price": 0,
            "sl_price": 0,
            "rr_ratio": 0,
            "risk_pct": 0,
            "reward_pct": 0,
            "urgency": "Baixa",
            "reason": "Dados insuficientes para uma ordem a mercado.",
        }

    close = float(ind["close"])
    atr = ind.get("atr", "N/A")
    if atr == "N/A" or atr <= 0:
        atr = close * 0.02

    is_long = "Bullish" in trend
    is_short = "Bearish" in trend
    is_scalp = "Noise" in mode or "Scalp" in mode or "Intraday" in mode

    if not is_long and not is_short:
        return {
            "action": "AGUARDAR",
            "side": "NEUTRO",
            "enter_now": False,
            "confidence": max(0, min(100, score - 20)),
            "entry_price": round(close, 2),
            "tp_price": 0,
            "sl_price": 0,
            "rr_ratio": 0,
            "risk_pct": 0,
            "reward_pct": 0,
            "urgency": "Baixa",
            "reason": "Sem direcao estrutural clara para entrada a mercado.",
        }

    confidence = score
    status = exec_plan.get("status", "")
    if "FOMO" in status:
        confidence -= 15
    if "Structure Broken" in status:
        confidence -= 25
    if rr_data.get("rr_class") == "Poor":
        confidence -= 20
    elif rr_data.get("rr_class") == "Weak":
        confidence -= 10
    if is_scalp and score >= 70:
        confidence += 5
    confidence = max(0, min(100, int(confidence)))

    min_confidence = 62 if is_scalp else 68
    enter_now = confidence >= min_confidence and "Structure Broken" not in status

    side = "LONG" if is_long else "SHORT"
    action = f"ENTRAR {side} A MERCADO" if enter_now else "AGUARDAR"
    urgency = "Alta" if enter_now and is_scalp else "Media" if enter_now else "Baixa"

    risk_mult = 1.0 if is_scalp else 1.4
    reward_mult = 1.35 if is_scalp else 1.8

    if is_long:
        sl_price = close - (atr * risk_mult)
        tp_price = close + ((close - sl_price) * reward_mult)
        risk = close - sl_price
        reward = tp_price - close
    else:
        sl_price = close + (atr * risk_mult)
        tp_price = close - ((sl_price - close) * reward_mult)
        risk = sl_price - close
        reward = close - tp_price

    rr_ratio = reward / risk if risk > 0 else 0
    reason = (
        "Score e direcao sustentam execucao imediata."
        if enter_now else
        "Edge insuficiente para pagar spread/slippage de uma entrada a mercado."
    )
    if "FOMO" in status and enter_now:
        reason = "Entrada a mercado permitida, mas com risco de chase; reduzir tamanho da posicao."

    return {
        "action": action,
        "side": side,
        "enter_now": enter_now,
        "confidence": confidence,
        "entry_price": round(close, 2),
        "tp_price": round(tp_price, 2),
        "sl_price": round(sl_price, 2),
        "rr_ratio": round(rr_ratio, 2),
        "risk_pct": round((risk / close) * 100, 2) if risk > 0 else 0,
        "reward_pct": round((reward / close) * 100, 2) if reward > 0 else 0,
        "urgency": urgency,
        "reason": reason,
    }


def process_hierarchical_data(hierarchical_data: dict, symbol: str | None = None) -> dict:
    ind_pri = hierarchical_data["inds_primary"]
    ind_sec = hierarchical_data["inds_secondary"]
    ind_ter = hierarchical_data["inds_tertiary"]

    asset_key = _asset_key(symbol or hierarchical_data.get("symbol"))
    profile = SCORING_PROFILES[asset_key]

    score   = 50
    reasons = []
    if asset_key != "DEFAULT":
        reasons.append(f"Perfil de score ativo: {profile['name']} ({asset_key})")

    trend_pri = detect_trend(ind_pri)
    trend_sec = detect_trend(ind_sec) if ind_sec else "N/A"
    trend_ter = detect_trend(ind_ter) if ind_ter else "N/A"

    exec_plan = calculate_execution_plan(ind_pri, trend_pri)
    rr_data   = calculate_risk_reward_projected(ind_pri, exec_plan["ideal_entry"], trend_pri)

    # ── Direção ──────────────────────────────────────────────────────────────
    if "Bullish" in trend_pri:
        direction       = "COMPRA (LONG)"
        direction_color = "green1"
        is_bullish, is_bearish = True, False
    elif "Bearish" in trend_pri:
        direction       = "VENDA (SHORT)"
        direction_color = "red"
        is_bullish, is_bearish = False, True
    else:
        direction       = "NEUTRO (Sem direção clara)"
        direction_color = "yellow"
        is_bullish, is_bearish = False, False

    # ── 1. Alinhamento Primário + Secundário (±20) ────────────────────────
    pri_sec_aligned = (
        ("Bullish" in trend_pri and "Bullish" in trend_sec) or
        ("Bearish" in trend_pri and "Bearish" in trend_sec)
    )
    pri_sec_conflict = (
        ("Bullish" in trend_pri and "Bearish" in trend_sec) or
        ("Bearish" in trend_pri and "Bullish" in trend_sec)
    )
    if pri_sec_aligned:
        delta = _profile_delta(profile, "pri_sec_aligned", 20)
        score += delta
        _append_reason(reasons, "Tendencia alinhada com TF secundario", delta)
    elif pri_sec_conflict:
        delta = _profile_delta(profile, "pri_sec_conflict", -10)
        score += delta
        _append_reason(reasons, "Conflito de tendencia entre TF primario e secundario", delta)

    # ── 2. Alinhamento Terciário (±10) ────────────────────────────────────
    if trend_ter not in ("N/A", "Insufficient Data for Structure"):
        ter_aligned = (
            ("Bullish" in trend_pri and "Bullish" in trend_ter) or
            ("Bearish" in trend_pri and "Bearish" in trend_ter)
        )
        ter_conflict = (
            ("Bullish" in trend_pri and "Bearish" in trend_ter) or
            ("Bearish" in trend_pri and "Bullish" in trend_ter)
        )
        if ter_aligned:
            delta = _profile_delta(profile, "ter_aligned", 10)
            score += delta
            _append_reason(reasons, "Alinhamento triplo confirmado (TF terciario)", delta)
        elif ter_conflict:
            delta = _profile_delta(profile, "ter_conflict", -5)
            score += delta
            if delta:
                _append_reason(reasons, "TF terciario conflita com a direcao primaria", delta)
            else:
                reasons.append("TF terciario conflita com a direcao primaria (neutro no perfil do ativo)")

    # ── 3. ADX — Força da Tendência (±15) ────────────────────────────────
    adx = ind_pri.get("adx", "N/A")
    if adx != "N/A":
        if adx > 25:
            delta = _profile_delta(profile, "adx_strong", 15)
            score += delta
            _append_reason(reasons, f"Tendencia forte detectada (ADX {round(adx,1)})", delta)
        elif adx >= 20:
            delta = _profile_delta(profile, "adx_moderate", 5)
            score += delta
            _append_reason(reasons, f"Tendencia moderada (ADX {round(adx,1)})", delta)
        else:
            delta = _profile_delta(profile, "adx_weak", -10)
            score += delta
            _append_reason(reasons, f"Mercado em lateralizacao (ADX {round(adx,1)} < 20)", delta)

    # ── 4. RSI — Qualidade do Momentum (±15), direction-aware ────────────
    rsi = ind_pri.get("rsi", "N/A")
    if rsi != "N/A":
        if is_bullish:
            if rsi > 70:
                score -= 15
                reasons.append(f"RSI sobrecomprado ({round(rsi,1)}) — entrada em topo (-15)")
            elif rsi >= 60:
                score += 5
                reasons.append(f"RSI em momentum crescente ({round(rsi,1)}) (+5)")
            elif rsi >= 40:
                score += 10
                reasons.append(f"RSI em zona saudável para long ({round(rsi,1)}) (+10)")
            elif rsi >= 30:
                score += 5
                reasons.append(f"RSI recuperando de sobrevenda ({round(rsi,1)}) (+5)")
            else:
                score -= 10
                reasons.append(f"RSI em sobrevenda extrema ({round(rsi,1)}) (-10)")
        elif is_bearish:
            if rsi < 30:
                score -= 15
                reasons.append(f"RSI sobrevendido ({round(rsi,1)}) — entrada em fundo (-15)")
            elif rsi <= 40:
                score += 5
                reasons.append(f"RSI em momentum bearish ({round(rsi,1)}) (+5)")
            elif rsi <= 60:
                score += 10
                reasons.append(f"RSI em zona saudável para short ({round(rsi,1)}) (+10)")
            elif rsi <= 70:
                score += 5
                reasons.append(f"RSI próximo de sobrecompra (favorável para short) ({round(rsi,1)}) (+5)")
            else:
                score -= 10
                reasons.append(f"RSI em sobrecompra extrema ({round(rsi,1)}) (-10)")
        else:
            if 45 <= rsi <= 55:
                score += 5
                reasons.append(f"RSI neutro centralizado ({round(rsi,1)}) (+5)")
            elif rsi > 70 or rsi < 30:
                score -= 10
                reasons.append(f"RSI em extremo ({round(rsi,1)}) em mercado neutro (-10)")

    # ── 5. MACD — Confirmação Direcional (±15) ────────────────────────────
    macd_hist      = ind_pri.get("macd_hist",      "N/A")
    macd_hist_prev = ind_pri.get("macd_hist_prev", "N/A")
    if macd_hist != "N/A" and macd_hist_prev != "N/A":
        hist_growing = macd_hist > macd_hist_prev
        macd_expanding = False
        if is_bullish:
            if macd_hist > 0 and hist_growing:
                macd_expanding = True
                delta = _profile_delta(profile, "macd_expanding", 15)
                score += delta
                _append_reason(reasons, "MACD: momentum bullish em expansao", delta)
            elif macd_hist > 0 and not hist_growing:
                delta = _profile_delta(profile, "macd_fading", 5)
                score += delta
                _append_reason(reasons, "MACD: momentum bullish desacelerando", delta)
            elif macd_hist < 0 and hist_growing:
                delta = _profile_delta(profile, "macd_recovering", -5)
                score += delta
                _append_reason(reasons, "MACD: abaixo do zero, porem se recuperando", delta)
            else:
                delta = _profile_delta(profile, "macd_divergence", -15)
                score += delta
                _append_reason(reasons, "MACD: divergencia bearish contra tendencia alta", delta)
        elif is_bearish:
            if macd_hist < 0 and not hist_growing:
                macd_expanding = True
                delta = _profile_delta(profile, "macd_expanding", 15)
                score += delta
                _append_reason(reasons, "MACD: momentum bearish em expansao", delta)
            elif macd_hist < 0 and hist_growing:
                delta = _profile_delta(profile, "macd_fading", 5)
                score += delta
                _append_reason(reasons, "MACD: momentum bearish desacelerando", delta)
            elif macd_hist > 0 and not hist_growing:
                delta = _profile_delta(profile, "macd_recovering", -5)
                score += delta
                _append_reason(reasons, "MACD: acima do zero, perdendo forca", delta)
            else:
                delta = _profile_delta(profile, "macd_divergence", -15)
                score += delta
                _append_reason(reasons, "MACD: divergencia bullish contra tendencia baixa", delta)
        else:
            if abs(macd_hist) < abs(macd_hist_prev):
                delta = _profile_delta(profile, "macd_neutral", 5)
                score += delta
                _append_reason(reasons, "MACD convergindo para zero em mercado neutro", delta)

        if pri_sec_aligned and adx != "N/A" and adx > 25 and macd_expanding:
            delta = _profile_delta(profile, "late_momentum_penalty", 0)
            if delta:
                score += delta
                _append_reason(
                    reasons,
                    "ETH: setup perfeito de momentum tratado como entrada tardia",
                    delta,
                )

    # ── 6. ATR — Qualidade da Volatilidade (±10) ─────────────────────────
    atr     = ind_pri.get("atr",         "N/A")
    avg_atr = ind_pri.get("avg_atr_14",  "N/A")
    if atr != "N/A" and avg_atr != "N/A":
        if atr > avg_atr * 1.5:
            score -= 10
            reasons.append("Volatilidade explosiva — risco elevado de slippage (-10)")
        elif atr > avg_atr * 1.1:
            score -= 5
            reasons.append("Volatilidade em expansão (-5)")
        elif atr < avg_atr * 0.7:
            reasons.append("Volatilidade comprimida — breakout pendente (neutro)")
        else:
            score += 5
            reasons.append("Volatilidade controlada — condição favorável (+5)")

    # ── 7. Volume — Convicção Operacional (±10) ───────────────────────────
    vol     = ind_pri.get("volume",     "N/A")
    avg_vol = ind_pri.get("avg_volume", "N/A")
    if vol != "N/A" and avg_vol != "N/A":
        if vol > avg_vol * 1.5:
            score += 10
            reasons.append("Volume operacional forte (+10)")
        elif vol > avg_vol * 1.2:
            score += 5
            reasons.append("Volume acima da média (+5)")
        elif vol < avg_vol * 0.7:
            score -= 5
            reasons.append("Volume fraco — baixa convicção (-5)")

    # ── 8. Zona de Execução Tática (±30) ─────────────────────────────────
    if "FOMO" in exec_plan["status"]:
        score -= 30
        reasons.append("FOMO RISK: Preço esticado longe do pullback ideal (-30)")
    elif "Optimal" in exec_plan["status"]:
        score += 10
        reasons.append("Dentro da zona de execução tática ideal (+10)")
    elif "Structure Broken" in exec_plan["status"]:
        score -= 15
        reasons.append("Estrutura rompida — cautela (-15)")

    # ── 9. Risk/Reward (±40) ──────────────────────────────────────────────
    if rr_data["rr_class"] == "Poor":
        score -= 40
        reasons.append("RR < 1.0: risco supera retorno (-40)")
    elif rr_data["rr_class"] == "Weak":
        score -= 15
        reasons.append("RR < 1.5: assimetria fraca (-15)")
    elif rr_data["rr_class"] == "Acceptable":
        score += 5
        reasons.append("RR 1.5–2.0: assimetria aceitável (+5)")
    elif rr_data["rr_class"] == "Strong":
        score += 15
        reasons.append("RR > 2.0: assimetria forte (+15)")

    # ── 10. Penalidade Timeframe Ruidoso (−10) ────────────────────────────
    mode = hierarchical_data["mode"]
    if "Noise" in mode:
        score -= 10
        reasons.append("Penalidade por operar em timeframe ruidoso (-10)")

    score = max(0, min(100, score))

    if score < 40:   classification = "Ruim / No Trade"
    elif score < 60: classification = "Neutro"
    elif score < 80: classification = "Aceitável"
    else:            classification = "Alta Qualidade / Assimetria"

    market_order = calculate_market_order_plan(
        ind=ind_pri,
        trend=trend_pri,
        score=int(score),
        exec_plan=exec_plan,
        rr_data=rr_data,
        mode=mode,
    )

    return {
        "score":          int(score),
        "classification": classification,
        "reasons":        reasons,
        "rr_data":        rr_data,
        "market_order":   market_order,
        "exec_plan":      exec_plan,
        "mode":           mode,
        "asset_profile":  asset_key,
        "profile_name":   profile["name"],
        "direction":      direction,
        "direction_color": direction_color,
        "sem_primary":   generate_semantic_context(ind_pri, trend_pri),
        "sem_secondary": generate_semantic_context(ind_sec, trend_sec) if ind_sec else None,
        "sem_tertiary":  generate_semantic_context(ind_ter, trend_ter) if ind_ter else None,
        "tf_labels":     hierarchical_data["tf_labels"],
    }
