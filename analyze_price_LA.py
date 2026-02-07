import pandas as pd

# =============================================================================
# FILE PATH - Points directly to your Downloads folder
# =============================================================================
filename = "/Users/maxschafer/Downloads/kalshi-price-history-kxhighlax-25dec15-minute.csv"

# Read the CSV
df = pd.read_csv(filename)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

print("=== YOUR CSV DATA ===\n")
print(f"Total rows: {len(df)}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}\n")

print("Column names (temperature buckets):")
for col in df.columns:
    print(f"  - {col}")

print("\n=== FIRST 5 ROWS ===")
print(df.head())

print("\n=== LATEST PRICES ===")
latest = df.iloc[-1]
print(f"Timestamp: {latest['timestamp']}")
for col in df.columns:
    if col != 'timestamp':
        print(f"  {col}: {latest[col]:.2f}¢")

# Example: Get all prices for one bucket
bucket_name = "69° to 70°"
prices = df[bucket_name].tolist()

print(f"\n=== PRICES FOR '{bucket_name}' ===")
print(f"Total data points: {len(prices)}")
print(f"First 10 prices: {prices[:10]}")
print(f"Last 10 prices: {prices[-10:]}")
print(f"Average: {sum(prices)/len(prices):.2f}¢")
print(f"Min: {min(prices):.2f}¢")
print(f"Max: {max(prices):.2f}¢")

print("\n✓ Success! Your data has been loaded.")
