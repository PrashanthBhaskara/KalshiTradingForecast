import pandas as pd
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

print("DYNAMIC BTC HEDGING BACKTEST - Option 3")

kalshi = pd.read_csv('/Users/aaditjerfy/Downloads/Implicit Event Forecasting /kalshi-price-history-kxbtcmaxm-aug25-minute.csv')

SELECTED_STRIKE = '$130000 or above'
STRIKE = 130000

kalshi['timestamp'] = pd.to_datetime(kalshi['timestamp']).dt.tz_localize(None)
kalshi['market_price'] = kalshi[SELECTED_STRIKE] / 100
kalshi = kalshi[['timestamp', 'market_price']].dropna()

print(f"\n  Loaded Kalshi data: {len(kalshi)} data points")
print(f"  Selected strike: {SELECTED_STRIKE}")
print(f"  Date range: {kalshi['timestamp'].min()} to {kalshi['timestamp'].max()}")
print(f"  Market: Will BTC max reach ${STRIKE:,} or above in August 2025?")


btc = pd.read_csv('BTC_1min_2025.csv')
btc['timestamp'] = pd.to_datetime(btc['timestamp']).dt.tz_localize(None)
btc = btc[['timestamp', 'close', 'high', 'low']].copy()
btc.columns = ['timestamp', 'btc_price', 'btc_high', 'btc_low']

print(f"\n Loaded BTC data: {len(btc)} data points")
print(f"  Date range: {btc['timestamp'].min()} to {btc['timestamp'].max()}")

# Merge on timestamp (use forward-fill for missing Kalshi data)
df = pd.merge_asof(
    btc.sort_values('timestamp'),
    kalshi.sort_values('timestamp'),
    on='timestamp',
    direction='backward'
)

# After line 38 (after dropping NaN), add:
print(f"  Final merged rows: {len(df)}")

df = df[df['market_price'].notna()].copy()

print(f"\n Merged datasets: {len(df)} aligned data points")
print(f"  Aligned date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

# Black Scholes
def calculate_actual_probability(current_price, strike, days_to_expiry, volatility=0.60):
    """
    Calculate probability that BTC will be above strike at expiry using simplified BSM.
    
    Args:
        current_price: Current BTC spot price
        strike: Strike price ($100,000)
        days_to_expiry: Days until Dec 31, 2025
        volatility: Annualized volatility (default 60% for crypto)
    
    Returns:
        Probability (0-1) that BTC > strike at expiry
    """
    if days_to_expiry <= 0:
        return 1.0 if current_price > strike else 0.0
    
    T = days_to_expiry / 365.0  # Time to expiry in years
    
    # Calculate d2 from Black-Scholes
    #d2 = [ln(S/K) + (r - 0.5*σ²)T] / (σ√T), assume r=0 (risk-neutral, crypto has no risk-free rate)
    d2 = (np.log(current_price / strike) - 0.5 * volatility**2 * T) / (volatility * np.sqrt(T))
    
    prob = norm.cdf(d2) # p(finish ITM)
    
    return prob

EXPIRY_DATE = pd.Timestamp('2025-08-31')
df['days_to_expiry'] = (EXPIRY_DATE - df['timestamp']).dt.total_seconds() / 86400

df['actual_prob'] = df.apply(
    lambda row: calculate_actual_probability(
        row['btc_price'], 
        STRIKE, 
        row['days_to_expiry']
    ), 
    axis=1
)

df['implied_prob'] = df['market_price']

df['prob_mispricing'] = df['actual_prob'] - df['implied_prob']

print(f"\n  Calculated probabilities")
print(f"  Mean implied prob: {df['implied_prob'].mean():.2%}")
print(f"  Mean actual prob: {df['actual_prob'].mean():.2%}")
print(f"  Mean mispricing: {df['prob_mispricing'].mean():.2%}")


STRONG_THRESHOLD = 0.15
WEAK_THRESHOLD = 0.05
NEUTRAL_THRESHOLD = 0.02

df['signal'] = 0  # -2, -1, 0, 1, 2 (scaled position sizing)

# Scaled logic:
# - mispricing > 15% → signal = 2 (strong buy Yes)
# - mispricing > 5% → signal = 1 (weak buy Yes)
# - mispricing between -2% and +2% → signal = 0 (neutral)
# - mispricing < -5% → signal = -1 (weak short Yes)
# - mispricing < -15% → signal = -2 (strong short Yes)

for i in range(1, len(df)):
    mispricing = df.iloc[i]['prob_mispricing']
    
    if mispricing > STRONG_THRESHOLD:
        df.iloc[i, df.columns.get_loc('signal')] = 2
    elif mispricing > WEAK_THRESHOLD:
        df.iloc[i, df.columns.get_loc('signal')] = 1
    elif mispricing < -STRONG_THRESHOLD:
        df.iloc[i, df.columns.get_loc('signal')] = -2
    elif mispricing < -WEAK_THRESHOLD:
        df.iloc[i, df.columns.get_loc('signal')] = -1
    elif abs(mispricing) < NEUTRAL_THRESHOLD:
        df.iloc[i, df.columns.get_loc('signal')] = 0
    else:
        df.iloc[i, df.columns.get_loc('signal')] = df.iloc[i-1]['signal']

df['position_change'] = df['signal'].diff()
df['trade'] = (df['position_change'] != 0) & (df['position_change'].notna())

num_trades = df['trade'].sum()
print(f"\n  Generated trading signals (scaled positions)")
print(f"  Strong threshold: {STRONG_THRESHOLD:.1%} → 2x position")
print(f"  Weak threshold: {WEAK_THRESHOLD:.1%} → 1x position")
print(f"  Neutral zone: ±{NEUTRAL_THRESHOLD:.1%} → 0x position")
print(f"  Total trades: {num_trades}")


INITIAL_CAPITAL = 10000
CONTRACTS = 100

# Strategy A: Unhedged
first_btc_price = df.iloc[0]['btc_price']
last_btc_price = df.iloc[-1]['btc_price']
btc_return = (last_btc_price - first_btc_price) / first_btc_price
strategy_a_pnl = INITIAL_CAPITAL * btc_return

print("STRATEGY A: UNHEDGED BTC (Buy & Hold)")
print(f"  Entry: ${first_btc_price:,.2f}")
print(f"  Exit: ${last_btc_price:,.2f}")
print(f"  Return: {btc_return:.2%}")
print(f"  P&L: ${strategy_a_pnl:,.2f}")

# Strategy B: Static Hedge
first_market_price = df.iloc[0]['market_price']
last_market_price = df.iloc[-1]['market_price']

# BTC P&L (same as Strategy A)
btc_pnl_b = strategy_a_pnl

# Kalshi P&L: Short Yes at start, close at end
# Entry: Sell at first_market_price (receive premium)
# Exit: Buy back at last_market_price (pay to close)
kalshi_pnl_b = (first_market_price - last_market_price) * CONTRACTS

strategy_b_pnl = btc_pnl_b + kalshi_pnl_b

print("STRATEGY B: STATIC HEDGE")
print(f"  BTC P&L: ${btc_pnl_b:,.2f}")
print(f"  Kalshi entry: {first_market_price:.2%} (short Yes)")
print(f"  Kalshi exit: {last_market_price:.2%}")
print(f"  Kalshi P&L: ${kalshi_pnl_b:,.2f}")
print(f"  Total P&L: ${strategy_b_pnl:,.2f}")

# Strategy C: Dynamic Hedge (with scaled positions)
btc_pnl_c = strategy_a_pnl  # Same BTC exposure

# Kalshi P&L: Trade based on signals with position sizing
kalshi_pnl_c = 0
position = 0  # Current position size (-2 to +2)
entry_price = 0

for i in range(len(df)):
    current_signal = df.iloc[i]['signal']
    current_price = df.iloc[i]['market_price']
    
    # Check if position changed
    if i > 0:
        prev_signal = df.iloc[i-1]['signal']
        
        if position != current_signal:
            if position != 0:
                position_delta = current_signal - position                
                close_pnl = (current_price - entry_price) * position * CONTRACTS
                kalshi_pnl_c += close_pnl
            
            position = current_signal
            entry_price = current_price

if position != 0:
    exit_pnl = (last_market_price - entry_price) * position * CONTRACTS
    kalshi_pnl_c += exit_pnl

strategy_c_pnl = btc_pnl_c + kalshi_pnl_c

print("STRATEGY C: DYNAMIC HEDGE (Mispricing Trades)")
print(f"  BTC P&L: ${btc_pnl_c:,.2f}")
print(f"  Kalshi trades: {num_trades}")
print(f"  Kalshi P&L: ${kalshi_pnl_c:,.2f}")
print(f"  Total P&L: ${strategy_c_pnl:,.2f}")


print("FINAL COMPARISON")

results = pd.DataFrame({
    'Strategy': ['A: Unhedged', 'B: Static Hedge', 'C: Dynamic Hedge'],
    'Total P&L': [strategy_a_pnl, strategy_b_pnl, strategy_c_pnl],
    'Return': [
        strategy_a_pnl / INITIAL_CAPITAL,
        strategy_b_pnl / INITIAL_CAPITAL,
        strategy_c_pnl / INITIAL_CAPITAL
    ]
})

print(results.to_string(index=False))

print(f"\n  Best Strategy: {results.loc[results['Total P&L'].idxmax(), 'Strategy']}")
print(f"  Outperformance vs Unhedged: ${results['Total P&L'].max() - strategy_a_pnl:,.2f}")


df.to_csv('dynamic_hedge_backtest_results.csv', index=False)
print(f"\n  Saved detailed results to: dynamic_hedge_backtest_results.csv")

print("BACKTEST COMPLETE")
