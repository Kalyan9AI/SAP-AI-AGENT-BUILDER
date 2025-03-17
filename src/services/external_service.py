import aiohttp
from typing import Dict, Optional
from datetime import datetime, timedelta

from ..config.settings import settings

class ExternalDataService:
    def __init__(self):
        self.weather_api_key = settings.WEATHER_API_KEY
        self.traffic_api_key = settings.TRAFFIC_API_KEY
        self.session = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_weather_forecast(self, location: Optional[Dict] = None) -> Dict:
        """Fetch weather forecast data"""
        try:
            session = await self.get_session()
            
            # Default to a central location if none provided
            if location is None:
                location = {'lat': '40.7128', 'lon': '-74.0060'}  # New York
            
            # OpenWeatherMap API endpoint
            url = f"http://api.openweathermap.org/data/2.5/forecast"
            params = {
                'lat': location['lat'],
                'lon': location['lon'],
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process the forecast data
                    processed_data = {
                        'temperature': data['list'][0]['main']['temp'],
                        'precipitation': data['list'][0]['rain']['3h'] if 'rain' in data['list'][0] else 0,
                        'wind_speed': data['list'][0]['wind']['speed'],
                        'severity': self._calculate_weather_severity(data['list'][0]),
                        'description': data['list'][0]['weather'][0]['description'],
                        'forecast': [
                            {
                                'datetime': item['dt_txt'],
                                'temperature': item['main']['temp'],
                                'weather': item['weather'][0]['main'],
                                'description': item['weather'][0]['description']
                            }
                            for item in data['list'][:5]  # Next 15 hours (3-hour intervals)
                        ]
                    }
                    
                    return processed_data
                else:
                    raise Exception(f"Weather API returned status code {response.status}")
                    
        except Exception as e:
            # Return default data in case of API failure
            return {
                'temperature': 20,
                'precipitation': 0,
                'wind_speed': 5,
                'severity': 'low',
                'description': 'API Error: Using default values',
                'forecast': []
            }

    async def get_traffic_conditions(self, route: Optional[Dict] = None) -> Dict:
        """Fetch traffic conditions data"""
        try:
            session = await self.get_session()
            
            # Default route if none provided
            if route is None:
                route = {
                    'start': {'lat': '40.7128', 'lon': '-74.0060'},
                    'end': {'lat': '40.7614', 'lon': '-73.9776'}
                }
            
            # Here Maps API endpoint (example)
            url = "https://traffic.api.here.com/traffic/6.3/flow.json"
            params = {
                'app_id': 'your_app_id',
                'app_key': self.traffic_api_key,
                'bbox': f"{route['start']['lat']},{route['start']['lon']};{route['end']['lat']},{route['end']['lon']}"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process the traffic data
                    processed_data = {
                        'congestion_level': self._calculate_congestion_level(data),
                        'incident_count': len(data.get('incidents', [])),
                        'severity': self._calculate_traffic_severity(data),
                        'description': self._generate_traffic_description(data),
                        'incidents': [
                            {
                                'type': incident['type'],
                                'location': incident['location'],
                                'severity': incident['severity']
                            }
                            for incident in data.get('incidents', [])[:5]
                        ]
                    }
                    
                    return processed_data
                else:
                    raise Exception(f"Traffic API returned status code {response.status}")
                    
        except Exception as e:
            # Return default data in case of API failure
            return {
                'congestion_level': 0.5,
                'incident_count': 0,
                'severity': 'low',
                'description': 'API Error: Using default values',
                'incidents': []
            }

    def _calculate_weather_severity(self, weather_data: Dict) -> str:
        """Calculate weather severity level"""
        severity = 'low'
        
        # Temperature extremes
        temp = weather_data['main']['temp']
        if temp < -10 or temp > 35:
            severity = 'high'
        elif temp < 0 or temp > 30:
            severity = 'medium'
            
        # Precipitation
        if 'rain' in weather_data and weather_data['rain'].get('3h', 0) > 10:
            severity = 'high'
        elif 'rain' in weather_data and weather_data['rain'].get('3h', 0) > 5:
            severity = 'medium'
            
        # Wind speed
        if weather_data['wind']['speed'] > 20:
            severity = 'high'
        elif weather_data['wind']['speed'] > 10:
            severity = 'medium'
            
        return severity

    def _calculate_congestion_level(self, traffic_data: Dict) -> float:
        """Calculate traffic congestion level (0-1)"""
        # This would depend on the specific traffic API response format
        # Here's a simplified example
        total_segments = len(traffic_data.get('segments', []))
        congested_segments = sum(
            1 for segment in traffic_data.get('segments', [])
            if segment.get('congestion', 'low') in ['high', 'severe']
        )
        
        return congested_segments / total_segments if total_segments > 0 else 0.0

    def _calculate_traffic_severity(self, traffic_data: Dict) -> str:
        """Calculate traffic severity level"""
        congestion = self._calculate_congestion_level(traffic_data)
        incidents = len(traffic_data.get('incidents', []))
        
        if congestion > 0.7 or incidents > 5:
            return 'high'
        elif congestion > 0.4 or incidents > 2:
            return 'medium'
        else:
            return 'low'

    def _generate_traffic_description(self, traffic_data: Dict) -> str:
        """Generate human-readable traffic description"""
        severity = self._calculate_traffic_severity(traffic_data)
        incidents = len(traffic_data.get('incidents', []))
        
        if severity == 'high':
            return f"Heavy traffic conditions with {incidents} reported incidents"
        elif severity == 'medium':
            return f"Moderate traffic conditions with {incidents} reported incidents"
        else:
            return f"Light traffic conditions with {incidents} reported incidents"

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close() 