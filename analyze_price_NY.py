import pandas as pd

# =============================================================================
# FILE PATH - NYC Snow Market Data
# =============================================================================
filename = "/Users/maxschafer/Downloads/kalshi-price-history-kxnycsnowm-26jan-minute.csv"

# Read the CSV
df = pd.read_csv(filename)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

print("=== NYC SNOW MARKET DATA ===\n")
print(f"Total rows: {len(df)}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}\n")

print("Column names (snowfall amount buckets):")
for col in df.columns:
    print(f"  - {col}")

print("\n=== FIRST 5 ROWS ===")
print(df.head())

print("\n=== LATEST PRICES ===")
latest = df.iloc[-1]
print(f"Timestamp: {latest['timestamp']}")
for col in df.columns:
    if col != 'timestamp':
        value = latest[col]
        if pd.notna(value):  # Check if value is not NaN
            print(f"  {col}: {value:.2f}¢")
        else:
            print(f"  {col}: No data")

# Example: Get all prices for "Above 6.0 inches" bucket
bucket_name = "Above 6.0 inches"
prices = df[bucket_name].dropna().tolist()  # Remove NaN values

print(f"\n=== PRICES FOR '{bucket_name}' ===")
print(f"Total data points: {len(prices)}")
if len(prices) > 0:
    print(f"First 10 prices: {prices[:10]}")
    print(f"Last 10 prices: {prices[-10:]}")
    print(f"Average: {sum(prices)/len(prices):.2f}¢")
    print(f"Min: {min(prices):.2f}¢")
    print(f"Max: {max(prices):.2f}¢")
else:
    print("No data available for this bucket")

# Show statistics for all buckets
print("\n=== SUMMARY STATISTICS FOR ALL BUCKETS ===")
for col in df.columns:
    if col != 'timestamp':
        valid_prices = df[col].dropna()
        if len(valid_prices) > 0:
            print(f"\n{col}:")
            print(f"  Data points: {len(valid_prices)}")
            print(f"  Average: {valid_prices.mean():.2f}¢")
            print(f"  Min: {valid_prices.min():.2f}¢")
            print(f"  Max: {valid_prices.max():.2f}¢")
            print(f"  Latest: {df[col].iloc[-1] if pd.notna(df[col].iloc[-1]) else 'No data'}¢")

print("\n✓ Success! NYC snow market data has been loaded.")
