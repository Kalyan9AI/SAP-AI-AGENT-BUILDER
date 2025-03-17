from pyrfc import Connection
from typing import List, Optional, Dict
import pandas as pd
from datetime import datetime, timedelta

from ..config.settings import settings

class SAPService:
    def __init__(self):
        self.connection_params = {
            'ashost': settings.SAP_ASHOST,
            'sysnr': settings.SAP_SYSNR,
            'client': settings.SAP_CLIENT,
            'user': settings.SAP_USER,
            'passwd': settings.SAP_PASSWD
        }

    async def connect(self) -> Connection:
        """Establish connection to SAP system"""
        try:
            return Connection(**self.connection_params)
        except Exception as e:
            raise Exception(f"Failed to connect to SAP: {str(e)}")

    def check_connection(self) -> bool:
        """Check if SAP connection is available"""
        try:
            conn = Connection(**self.connection_params)
            conn.close()
            return True
        except:
            return False

    async def get_delivery_data(self, supplier_id: Optional[str] = None) -> List[Dict]:
        """Fetch delivery data from SAP"""
        try:
            conn = await self.connect()
            
            # Define the RFC function module name
            function_name = 'BAPI_DELIVERY_GETLIST'
            
            # Prepare parameters for the function module
            params = {
                'DELIVERY_DATE': datetime.now().strftime('%Y%m%d'),
                'TO_DATE': (datetime.now() + timedelta(days=30)).strftime('%Y%m%d')
            }
            
            if supplier_id:
                params['VENDOR'] = supplier_id
            
            # Call the RFC function module
            result = conn.call(function_name, **params)
            
            # Process the result
            deliveries = []
            for delivery in result['DELIVERY_LIST']:
                deliveries.append({
                    'delivery_id': delivery['DELIV_NUMB'],
                    'supplier_id': delivery['VENDOR'],
                    'scheduled_date': delivery['DELIV_DATE'],
                    'origin': delivery['SHIP_POINT'],
                    'destination': delivery['DEST_POINT'],
                    'status': delivery['DLV_STATUS'],
                    'items': delivery['ITEMS']
                })
            
            conn.close()
            return deliveries
        
        except Exception as e:
            raise Exception(f"Failed to fetch delivery data: {str(e)}")

    async def get_supplier_performance(self, supplier_id: str) -> Dict:
        """Fetch historical supplier performance metrics"""
        try:
            conn = await self.connect()
            
            # Define the RFC function module name
            function_name = 'Z_GET_SUPPLIER_PERFORMANCE'  # Custom function module
            
            # Call the RFC function module
            result = conn.call(function_name, VENDOR=supplier_id)
            
            # Process the result
            performance = {
                'on_time_delivery_rate': result['ON_TIME_RATE'],
                'average_delay': result['AVG_DELAY'],
                'total_deliveries': result['TOTAL_DELIVERIES'],
                'delayed_deliveries': result['DELAYED_DELIVERIES'],
                'performance_score': result['PERFORMANCE_SCORE']
            }
            
            conn.close()
            return performance
        
        except Exception as e:
            raise Exception(f"Failed to fetch supplier performance: {str(e)}")

    async def update_delivery_status(self, delivery_id: str, status: str) -> bool:
        """Update delivery status in SAP"""
        try:
            conn = await self.connect()
            
            # Define the RFC function module name
            function_name = 'BAPI_DELIVERY_CHANGE'
            
            # Call the RFC function module
            result = conn.call(
                function_name,
                DELIVERY=delivery_id,
                DELIVERY_STATUS=status
            )
            
            conn.close()
            return result['RETURN']['TYPE'] == 'S'  # Success
        
        except Exception as e:
            raise Exception(f"Failed to update delivery status: {str(e)}")

    async def get_delivery_routes(self, delivery_ids: List[str]) -> List[Dict]:
        """Fetch delivery route information"""
        try:
            conn = await self.connect()
            
            routes = []
            for delivery_id in delivery_ids:
                # Call RFC function to get route details
                result = conn.call(
                    'Z_GET_DELIVERY_ROUTE',  # Custom function module
                    DELIVERY_ID=delivery_id
                )
                
                routes.append({
                    'delivery_id': delivery_id,
                    'route_points': result['ROUTE_POINTS'],
                    'distance': result['TOTAL_DISTANCE'],
                    'estimated_duration': result['EST_DURATION']
                })
            
            conn.close()
            return routes
        
        except Exception as e:
            raise Exception(f"Failed to fetch delivery routes: {str(e)}") 