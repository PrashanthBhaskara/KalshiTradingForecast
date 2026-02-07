"""
Kalshi Prediction Markets vs ERA5 Actual Weather
=================================================
This script compares prediction market prices with actual weather outcomes.
"""

import pandas as pd
import numpy as np

def analyze_temperature_market(kalshi_csv, era5_csv, city_name, temp_buckets):
    """
    Compare Kalshi temperature predictions with ERA5 actual temperatures
    
    Parameters:
    - kalshi_csv: Path to Kalshi price history CSV
    - era5_csv: Path to ERA5 temperature CSV
    - city_name: Name of the city
    - temp_buckets: Dictionary of temperature buckets from Kalshi
    """
    print(f"\n{'='*70}")
    print(f"ANALYSIS: {city_name} Temperature")
    print(f"{'='*70}")
    
    # Load Kalshi data
    kalshi_df = pd.read_csv(kalshi_csv)
    kalshi_df['timestamp'] = pd.to_datetime(kalshi_df['timestamp'])
    
    # Load ERA5 data
    era5_df = pd.read_csv(era5_csv)
    era5_df['time'] = pd.to_datetime(era5_df['time'])
    
    # Get daily maximum temperature from ERA5
    era5_df['date'] = era5_df['time'].dt.date
    daily_max = era5_df.groupby('date')['temperature_f'].max()
    
    print(f"\nActual Daily Maximum Temperatures (ERA5):")
    for date, temp in daily_max.items():
        print(f"  {date}: {temp:.1f}°F")
    
    # Determine which bucket the actual temperature fell into
    for date, actual_temp in daily_max.items():
        print(f"\n--- {date} ---")
        print(f"Actual High: {actual_temp:.1f}°F")
        
        # Find which bucket this falls into
        actual_bucket = None
        for bucket_name, (low, high) in temp_buckets.items():
            if low is None and actual_temp <= high:
                actual_bucket = bucket_name
                break
            elif high is None and actual_temp >= low:
                actual_bucket = bucket_name
                break
            elif low is not None and high is not None and low <= actual_temp <= high:
                actual_bucket = bucket_name
                break
        
        print(f"Actual Outcome: {actual_bucket}")
        
        # Get final Kalshi prices for this date
        date_data = kalshi_df[kalshi_df['timestamp'].dt.date == date]
        if len(date_data) > 0:
            final_prices = date_data.iloc[-1]
            print(f"\nFinal Market Prices (¢):")
            for bucket in temp_buckets.keys():
                if bucket in final_prices:
                    price = final_prices[bucket]
                    if pd.notna(price):
                        is_winner = "✓ WINNER" if bucket == actual_bucket else ""
                        print(f"  {bucket}: {price:.2f}¢ {is_winner}")
            
            # Calculate market's expected outcome (highest price)
            bucket_prices = {bucket: final_prices[bucket] for bucket in temp_buckets.keys() 
                           if bucket in final_prices and pd.notna(final_prices[bucket])}
            if bucket_prices:
                predicted_bucket = max(bucket_prices, key=bucket_prices.get)
                predicted_price = bucket_prices[predicted_bucket]
                
                print(f"\nMarket Prediction: {predicted_bucket} ({predicted_price:.1f}¢)")
                print(f"Actual Outcome: {actual_bucket}")
                
                if predicted_bucket == actual_bucket:
                    print("✓ MARKET WAS CORRECT!")
                else:
                    print("✗ Market was incorrect")

def analyze_snow_market(kalshi_csv, era5_csv, city_name):
    """
    Compare Kalshi snow predictions with ERA5 actual snowfall
    """
    print(f"\n{'='*70}")
    print(f"ANALYSIS: {city_name} Snowfall")
    print(f"{'='*70}")
    
    # Load Kalshi data
    kalshi_df = pd.read_csv(kalshi_csv)
    kalshi_df['timestamp'] = pd.to_datetime(kalshi_df['timestamp'])
    
    # Load ERA5 data
    era5_df = pd.read_csv(era5_csv)
    era5_df['time'] = pd.to_datetime(era5_df['time'])
    
    # Calculate total snowfall (only when temp < 0°C)
    if 'is_snow' in era5_df.columns:
        snow_data = era5_df[era5_df['is_snow'] == True]
        total_snow = snow_data['precipitation_inches'].sum()
    else:
        # Assume all precipitation is snow if temp data not available
        total_snow = era5_df['precipitation_inches'].sum()
    
    print(f"\nActual Total Snowfall (ERA5): {total_snow:.2f} inches")
    
    # Get final market prices
    final_prices = kalshi_df.iloc[-1]
    print(f"\nFinal Market Prices (¢):")
    
    # Get all bucket columns (exclude timestamp)
    bucket_columns = [col for col in kalshi_df.columns if col != 'timestamp']
    
    winning_bucket = None
    for bucket in bucket_columns:
        if bucket in final_prices and pd.notna(final_prices[bucket]):
            price = final_prices[bucket]
            
            # Determine if actual snow fell in this bucket
            # Extract inches from bucket name
            if 'Above' in bucket:
                threshold = float(bucket.split('Above')[1].split('inches')[0].strip())
                is_winner = total_snow >= threshold
                if is_winner and (winning_bucket is None or threshold > winning_bucket[1]):
                    winning_bucket = (bucket, threshold)
            
            winner_mark = "✓ WINNER" if (winning_bucket and bucket == winning_bucket[0]) else ""
            print(f"  {bucket}: {price:.2f}¢ {winner_mark}")
    
    # Market prediction (highest price bucket)
    bucket_prices = {bucket: final_prices[bucket] for bucket in bucket_columns 
                   if bucket in final_prices and pd.notna(final_prices[bucket])}
    if bucket_prices:
        predicted_bucket = max(bucket_prices, key=bucket_prices.get)
        print(f"\nMarket Prediction: {predicted_bucket} ({bucket_prices[predicted_bucket]:.1f}¢)")
        if winning_bucket:
            print(f"Actual Outcome: {winning_bucket[0]}")
            if predicted_bucket == winning_bucket[0]:
                print("✓ MARKET WAS CORRECT!")
            else:
                print("✗ Market was incorrect")

def main():
    """Main analysis function"""
    print("="*70)
    print("KALSHI PREDICTION MARKETS vs ERA5 ACTUAL WEATHER")
    print("="*70)
    
    # Define temperature buckets for each city
    # Format: {bucket_name: (low_temp, high_temp)} where None means no bound
    
    lax_buckets = {
        "64° or below": (None, 64),
        "65° to 66°": (65, 66),
        "67° to 68°": (67, 68),
        "69° to 70°": (69, 70),
        "71° to 72°": (71, 72),
        "73° or above": (73, None)
    }
    
    mia_buckets = {
        "70° or below": (None, 70),
        "71° to 72°": (71, 72),
        "73° to 74°": (73, 74),
        "75° to 76°": (75, 76),
        "77° to 78°": (77, 78),
        "79° or above": (79, None)
    }
    
    nyc_buckets = {
        "25° or below": (None, 25),
        "26° to 27°": (26, 27),
        "28° to 29°": (28, 29),
        "30° to 31°": (30, 31),
        "32° to 33°": (32, 33),
        "34° or above": (34, None)
    }
    
    aus_buckets = {
        "86° or below": (None, 86),
        "87° to 88°": (87, 88),
        "89° to 90°": (89, 90),
        "91° to 92°": (91, 92),
        "93° to 94°": (93, 94),
        "95° or above": (95, None)
    }
    
    chi_buckets = {
        "82° or below": (None, 82),
        "83° to 84°": (83, 84),
        "85° to 86°": (85, 86),
        "87° to 88°": (87, 88),
        "89° to 90°": (89, 90),
        "91° or above": (91, None)
    }
    
    hou_buckets = {
        "85° or below": (None, 85),
        "86° to 87°": (86, 87),
        "88° to 89°": (88, 89),
        "90° to 91°": (90, 91),
        "92° to 93°": (92, 93),
        "94° or above": (94, None)
    }
    
    phil_buckets = {
        "84° or below": (None, 84),
        "85° to 86°": (85, 86),
        "87° to 88°": (87, 88),
        "89° to 90°": (89, 90),
        "91° to 92°": (91, 92),
        "93° or above": (93, None)
    }
    
    # Analyze each city
    try:
        analyze_temperature_market(
            'kalshi-price-history-kxhighlax-25dec15-minute.csv',
            'LA_TEMP_ERA.csv',
            'Los Angeles',
            lax_buckets
        )
    except Exception as e:
        print(f"\n✗ Error analyzing LAX: {e}")
    
    try:
        analyze_temperature_market(
            'kalshi-price-history-kxhighmia-25dec15-minute.csv',
            'MIA_TEMP_ERA.csv',
            'Miami',
            mia_buckets
        )
    except Exception as e:
        print(f"\n✗ Error analyzing MIA: {e}")
    
    try:
        analyze_temperature_market(
            'kalshi-price-history-kxhighny-25dec15-minute.csv',
            'NY_TEMP_ERA.csv',
            'New York City',
            nyc_buckets
        )
    except Exception as e:
        print(f"\n✗ Error analyzing NYC temp: {e}")
    
    try:
        analyze_temperature_market(
            'kalshi-price-history-kxhighaus-25jul26-minute.csv',
            'AUS_TEMP_ERA.csv',
            'Austin',
            aus_buckets
        )
    except Exception as e:
        print(f"\n✗ Error analyzing Austin: {e}")
    
    try:
        analyze_temperature_market(
            'kalshi-price-history-kxhighchi-25jul26-minute.csv',
            'CHI_TEMP_ERA.csv',
            'Chicago',
            chi_buckets
        )
    except Exception as e:
        print(f"\n✗ Error analyzing Chicago: {e}")
    
    try:
        analyze_temperature_market(
            'kalshi-price-history-kxhighhou-25jul26-minute (1).csv',
            'HOU_TEMP_ERA.csv',
            'Houston',
            hou_buckets
        )
    except Exception as e:
        print(f"\n✗ Error analyzing Houston: {e}")
    
    try:
        analyze_temperature_market(
            'kalshi-price-history-kxhighphil-25jul26-minute.csv',
            'PHIL_TEMP_ERA.csv',
            'Philadelphia',
            phil_buckets
        )
    except Exception as e:
        print(f"\n✗ Error analyzing Philadelphia: {e}")
    
    # Snow markets
    try:
        analyze_snow_market(
            'kalshi-price-history-kxnycsnowm-26jan-minute.csv',
            'NY_SNOW_ERA.csv',
            'NYC Snowfall'
        )
    except Exception as e:
        print(f"\n✗ Error analyzing NYC snowfall: {e}")
    
    try:
        analyze_snow_market(
            'kalshi-price-history-kxsnowstorm-26jannyc-minute.csv',
            'NY_SSNOW_ERA.csv',
            'NYC Snowstorm'
        )
    except Exception as e:
        print(f"\n✗ Error analyzing NYC snowstorm: {e}")
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
