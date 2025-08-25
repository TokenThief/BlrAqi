import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
import time
import os
from dotenv import load_dotenv
load_dotenv()


API_KEY = '7382c9f8be4c724ba34051031c536cda'
#os.getenv('OPENWEATHER_KEY') # Get from https://openweathermap.org/api

def get_aqi_data(lat, lon, days=10):
    """
    Fetch AQI data for the last N days from OpenWeatherMap API
    
    Args:
        lat (float): Latitude
        lon (float): Longitude  
        days (int): Number of days to fetch (default: 10)
    
    Returns:
        list: Daily averaged AQI data
    """
    try:
        # Calculate timestamps for the specified number of days
        end_time = int(time.time())  # Current timestamp
        start_time = end_time - (days * 24 * 60 * 60)  # N days ago
        
        # Fetch historical air pollution data
        url = f"http://api.openweathermap.org/data/2.5/air_pollution/history"
        params = {
            'lat': lat,
            'lon': lon,
            'start': start_time,
            'end': end_time,
            'appid': API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses
        
        data = response.json()
        
        # Process and format the data
        processed_data = []
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            processed_data.append({
                'date': dt.strftime('%Y-%m-%d'),
                'datetime': dt.isoformat(),
                'aqi': item['main']['aqi'],
                'pollutants': {
                    'co': item['components']['co'],
                    'no': item['components']['no'],
                    'no2': item['components']['no2'],
                    'o3': item['components']['o3'],
                    'so2': item['components']['so2'],
                    'pm2_5': item['components']['pm2_5'],
                    'pm10': item['components']['pm10'],
                    'nh3': item['components']['nh3']
                }
            })
        
        # Group by date and calculate daily averages
        daily_data = defaultdict(lambda: {
            'aqi_values': [],
            'pollutants': defaultdict(list)
        })
        
        for item in processed_data:
            date = item['date']
            daily_data[date]['aqi_values'].append(item['aqi'])
            
            for pollutant, value in item['pollutants'].items():
                daily_data[date]['pollutants'][pollutant].append(value)
        
        # Calculate averages and format final data
        final_data = []
        for date, data_dict in daily_data.items():
            # Calculate average AQI
            avg_aqi = round(sum(data_dict['aqi_values']) / len(data_dict['aqi_values']))
            
            # Calculate average pollutants
            avg_pollutants = {}
            for pollutant, values in data_dict['pollutants'].items():
                avg_pollutants[pollutant] = round(sum(values) / len(values), 2)
            
            final_data.append({
                'date': date,
                'aqi': avg_aqi,
                'aqi_description': get_aqi_description(avg_aqi),
                'pollutants': avg_pollutants
            })
        
        # Sort by date
        final_data.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'))
        
        return final_data
        
    except requests.RequestException as e:
        print(f"HTTP error occurred: {e}")
        raise
    except KeyError as e:
        print(f"Unexpected API response format: {e}")
        raise
    except Exception as e:
        print(f"Error fetching AQI data: {e}")
        raise

def get_aqi_description(aqi):
    """Convert AQI numeric value to description"""
    descriptions = {
        1: 'Good',
        2: 'Fair',
        3: 'Moderate', 
        4: 'Poor',
        5: 'Very Poor'
    }
    return descriptions.get(aqi, 'Unknown')

def print_aqi_summary(aqi_data):
    """Print a nicely formatted summary of AQI data"""
    print(f"AQI Data Summary ({len(aqi_data)} days):")
    print("=" * 50)
    
    for day in aqi_data:
        print(f"{day['date']}: AQI {day['aqi']} ({day['aqi_description']})")
        print(f"  PM2.5: {day['pollutants']['pm2_5']} μg/m³")
        print(f"  PM10: {day['pollutants']['pm10']} μg/m³")
        print(f"  O3: {day['pollutants']['o3']} μg/m³")
        print(f"  NO2: {day['pollutants']['no2']} μg/m³")
        print("-" * 30)

def save_to_json(aqi_data, filename='aqi_data.json'):
    """Save AQI data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(aqi_data, f, indent=2)
    print(f"Data saved to {filename}")

# Usage example
if __name__ == "__main__":
    try:
        lat = 77.7128
        lon = 13.0060
        
        print("Fetching AQI data for the last 10 days...")
        aqi_data = get_aqi_data(lat, lon, days=10)
        
        # Display results
        print_aqi_summary(aqi_data)
        
        # Optionally save to file
        # save_to_json(aqi_data)
        
        # Calculate some basic statistics
        aqi_values = [day['aqi'] for day in aqi_data]
        pm25_values = [day['pollutants']['pm2_5'] for day in aqi_data]
        
        print(f"\nStatistics:")
        print(f"Average AQI: {sum(aqi_values) / len(aqi_values):.1f}")
        print(f"Average PM2.5: {sum(pm25_values) / len(pm25_values):.1f} μg/m³")
        print(f"Best day: {min(aqi_data, key=lambda x: x['aqi'])['date']} (AQI {min(aqi_values)})")
        print(f"Worst day: {max(aqi_data, key=lambda x: x['aqi'])['date']} (AQI {max(aqi_values)})")
        
    except Exception as e:
        print(f"Failed to fetch AQI data: {e}")
