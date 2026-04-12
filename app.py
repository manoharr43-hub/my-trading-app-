//@version=5
indicator("🔥 SMC PRO MAX V20 - Intraday AI Scanner", overlay=true, max_boxes_count=500)

// =============================
// 1. CORE CALCULATIONS
// =============================
ema9  = ta.ema(close, 9)
ema21 = ta.ema(close, 21)
ema50 = ta.ema(close, 50)
vwapVal = ta.vwap(hlc3)

rsiVal = ta.rsi(close, 14)
[plusDI, minusDI, adxVal] = ta.dmi(14, 14)
volMA = ta.sma(volume, 20)

// =============================
// 2. MULTI-TIMEFRAME CONFIRMATION
// =============================
htf_close = request.security(syminfo.tickerid, "15", close)
htf_ema50 = request.security(syminfo.tickerid, "15", ta.ema(close, 50))

htfBull = htf_close > htf_ema50

// =============================
// 3. SMC LOGIC (BOS + LIQUIDITY)
// =============================
swingHigh = ta.highest(high, 10)
swingLow  = ta.lowest(low, 10)

bosBull = close > swingHigh[1]
bosBear = close < swingLow[1]

// Liquidity Grab (Fake Break)
liqGrabBull = low < swingLow and close > swingLow
liqGrabBear = high > swingHigh and close < swingHigh

// =============================
// 4. SUPPORT & RESISTANCE ZONES
// =============================
hi = ta.highest(high, 20)
lo = ta.lowest(low, 20)

if ta.change(hi)
    box.new(bar_index[10], hi, bar_index, hi,
     bgcolor=color.new(color.red, 85), border_color=color.red)

if ta.change(lo)
    box.new(bar_index[10], lo, bar_index, lo,
     bgcolor=color.new(color.green, 85), border_color=color.green)

// =============================
// 5. SMART SIGNAL ENGINE
// =============================
trendBull = close > ema50 and ema9 > ema21
trendBear = close < ema50 and ema9 < ema21

volStrong = volume > volMA

// Strong Buy Conditions
strongBuy = trendBull and volStrong and bosBull and htfBull and close > vwapVal

// Strong Sell Conditions
strongSell = trendBear and volStrong and bosBear and not htfBull and close < vwapVal

// =============================
// 6. CONFIDENCE SCORE
// =============================
score = 0
score += trendBull or trendBear ? 20 : 0
score += volStrong ? 20 : 0
score += (bosBull or bosBear) ? 20 : 0
score += (close > vwapVal ? 20 : 0)
score += (adxVal > 20 ? 20 : 0)

confidence = str.tostring(score) + "%"

// =============================
// 7. DASHBOARD (UPGRADED)
// =============================
var table dash = table.new(position.top_right, 8, 2, border_width=1)

if barstate.islast
    table.cell(dash, 0, 0, "TF", bgcolor=color.black, text_color=color.white)
    table.cell(dash, 1, 0, "Trend", bgcolor=color.black, text_color=color.white)
    table.cell(dash, 2, 0, "Conf", bgcolor=color.black, text_color=color.white)
    table.cell(dash, 3, 0, "Vol", bgcolor=color.black, text_color=color.white)
    table.cell(dash, 4, 0, "ADX", bgcolor=color.black, text_color=color.white)
    table.cell(dash, 5, 0, "RSI", bgcolor=color.black, text_color=color.white)
    table.cell(dash, 6, 0, "HTF", bgcolor=color.black, text_color=color.white)
    table.cell(dash, 7, 0, "Signal", bgcolor=color.black, text_color=color.white)

    table.cell(dash, 0, 1, timeframe.period, bgcolor=color.gray)
    table.cell(dash, 1, 1, trendBull ? "BULL" : trendBear ? "BEAR" : "SIDE",
         bgcolor=trendBull ? color.green : trendBear ? color.red : color.orange)

    table.cell(dash, 2, 1, confidence, bgcolor=color.blue)
    table.cell(dash, 3, 1, volStrong ? "STRONG" : "WEAK",
         bgcolor=volStrong ? color.green : color.orange)

    table.cell(dash, 4, 1, str.tostring(math.round(adxVal)))
    table.cell(dash, 5, 1, str.tostring(math.round(rsiVal)))
    table.cell(dash, 6, 1, htfBull ? "BULL" : "BEAR",
         bgcolor=htfBull ? color.green : color.red)

    table.cell(dash, 7, 1,
         strongBuy ? "🔥 BUY" :
         strongSell ? "🔴 SELL" : "WAIT",
         bgcolor=strongBuy ? color.green :
         strongSell ? color.red : color.orange)

// =============================
// 8. SIGNAL LABELS
// =============================
if strongBuy
    label.new(bar_index, low, "🔥 STRONG BUY",
     style=label.style_label_up, color=color.green, textcolor=color.white)

if strongSell
    label.new(bar_index, high, "🔴 STRONG SELL",
     style=label.style_label_down, color=color.red, textcolor=color.white)

// =============================
// 9. PLOTS
// =============================
plot(vwapVal, color=color.purple, title="VWAP")
plot(ema9, color=color.blue)
plot(ema21, color=color.orange)
plot(ema50, color=color.red)
