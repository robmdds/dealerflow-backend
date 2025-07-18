"""
DMS Integration Service for DealerFlow Pro
Handles integration with popular Dealer Management Systems
"""

import requests
import json
import time
from datetime import datetime, timedelta
from services.image_service import ImageService
from models.image import Image
from extensions import db

class DMSService:
    
    def __init__(self):
        self.image_service = ImageService()
        self.supported_dms = {
            'dealersocket': {
                'name': 'DealerSocket',
                'api_version': 'v1',
                'base_url': 'https://api.dealersocket.com',
                'auth_type': 'api_key'
            },
            'cdk': {
                'name': 'CDK Global',
                'api_version': 'v2',
                'base_url': 'https://api.cdkglobal.com',
                'auth_type': 'oauth2'
            },
            'reynolds': {
                'name': 'Reynolds & Reynolds',
                'api_version': 'v1',
                'base_url': 'https://api.reyrey.com',
                'auth_type': 'api_key'
            },
            'automate': {
                'name': 'Automate',
                'api_version': 'v1',
                'base_url': 'https://api.automate.com',
                'auth_type': 'api_key'
            },
            'dealertrack': {
                'name': 'DealerTrack',
                'api_version': 'v1',
                'base_url': 'https://api.dealertrack.com',
                'auth_type': 'oauth2'
            }
        }
    
    def get_supported_dms_list(self):
        """Get list of supported DMS systems"""
        return [
            {
                'id': dms_id,
                'name': dms_info['name'],
                'api_version': dms_info['api_version'],
                'auth_type': dms_info['auth_type']
            }
            for dms_id, dms_info in self.supported_dms.items()
        ]
    
    def validate_dms_credentials(self, dms_type, credentials):
        """Validate DMS API credentials"""
        try:
            if dms_type not in self.supported_dms:
                return False, f"Unsupported DMS type: {dms_type}"
            
            dms_config = self.supported_dms[dms_type]
            
            # Simulate credential validation (replace with actual API calls)
            if dms_config['auth_type'] == 'api_key':
                if not credentials.get('api_key'):
                    return False, "API key is required"
                
                # Test API connection
                test_result = self._test_api_connection(dms_type, credentials)
                return test_result, "Credentials validated" if test_result else "Invalid credentials"
                
            elif dms_config['auth_type'] == 'oauth2':
                required_fields = ['client_id', 'client_secret']
                for field in required_fields:
                    if not credentials.get(field):
                        return False, f"{field} is required for OAuth2"
                
                # Test OAuth2 flow
                test_result = self._test_oauth2_connection(dms_type, credentials)
                return test_result, "Credentials validated" if test_result else "Invalid OAuth2 credentials"
            
            return False, "Unknown authentication type"
            
        except Exception as e:
            return False, f"Credential validation error: {str(e)}"
    
    def _test_api_connection(self, dms_type, credentials):
        """Test API connection with credentials"""
        try:
            # This is a simulation - replace with actual DMS API calls
            dms_config = self.supported_dms[dms_type]
            
            # Simulate API call
            headers = {
                'Authorization': f"Bearer {credentials['api_key']}",
                'Content-Type': 'application/json'
            }
            
            # For demo purposes, return True if API key looks valid
            return len(credentials['api_key']) > 10
            
        except Exception:
            return False
    
    def _test_oauth2_connection(self, dms_type, credentials):
        """Test OAuth2 connection"""
        try:
            # This is a simulation - replace with actual OAuth2 flow
            client_id = credentials['client_id']
            client_secret = credentials['client_secret']
            
            # For demo purposes, return True if credentials look valid
            return len(client_id) > 5 and len(client_secret) > 10
            
        except Exception:
            return False
    
    def fetch_inventory_data(self, dms_type, credentials, dealership_id, filters=None):
        """Fetch vehicle inventory data from DMS"""
        try:
            if dms_type not in self.supported_dms:
                return None, f"Unsupported DMS type: {dms_type}"
            
            # Simulate inventory data fetch (replace with actual DMS API calls)
            inventory_data = self._simulate_inventory_fetch(dms_type, filters)
            
            return inventory_data, "Inventory data fetched successfully"
            
        except Exception as e:
            return None, f"Error fetching inventory: {str(e)}"
    
    def _simulate_inventory_fetch(self, dms_type, filters=None):
        """Simulate inventory data fetch for demo purposes"""
        # This would be replaced with actual DMS API calls
        sample_inventory = [
            {
                'vin': '1HGBH41JXMN109186',
                'stock_number': 'A12345',
                'year': '2023',
                'make': 'Honda',
                'model': 'Civic',
                'trim': 'LX',
                'exterior_color': 'Silver',
                'interior_color': 'Black',
                'mileage': 15000,
                'price': 22995,
                'status': 'available',
                'images': [
                    'https://example-dms.com/images/A12345_1.jpg',
                    'https://example-dms.com/images/A12345_2.jpg',
                    'https://example-dms.com/images/A12345_3.jpg'
                ]
            },
            {
                'vin': '2T1BURHE0JC123456',
                'stock_number': 'B67890',
                'year': '2022',
                'make': 'Toyota',
                'model': 'Camry',
                'trim': 'LE',
                'exterior_color': 'Blue',
                'interior_color': 'Gray',
                'mileage': 35000,
                'price': 24995,
                'status': 'available',
                'images': [
                    'https://example-dms.com/images/B67890_1.jpg',
                    'https://example-dms.com/images/B67890_2.jpg'
                ]
            }
        ]
        
        # Apply filters if provided
        if filters:
            filtered_inventory = []
            for vehicle in sample_inventory:
                match = True
                for key, value in filters.items():
                    if key in vehicle and str(vehicle[key]).lower() != str(value).lower():
                        match = False
                        break
                if match:
                    filtered_inventory.append(vehicle)
            return filtered_inventory
        
        return sample_inventory
    
    def sync_dms_images(self, dms_type, credentials, dealership_id, vehicle_filters=None):
        """Sync images from DMS to local storage"""
        try:
            # Fetch inventory data
            inventory_data, message = self.fetch_inventory_data(dms_type, credentials, dealership_id, vehicle_filters)
            
            if not inventory_data:
                return 0, 0, f"Failed to fetch inventory: {message}"
            
            synced_count = 0
            error_count = 0
            errors = []
            
            for vehicle in inventory_data:
                try:
                    # Download and save images for each vehicle
                    vehicle_synced, vehicle_errors = self._sync_vehicle_images(
                        vehicle, dealership_id, dms_type
                    )
                    synced_count += vehicle_synced
                    error_count += len(vehicle_errors)
                    errors.extend(vehicle_errors)
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Vehicle {vehicle.get('stock_number', 'unknown')}: {str(e)}")
            
            return synced_count, error_count, errors
            
        except Exception as e:
            return 0, 0, [f"DMS sync error: {str(e)}"]
    
    def _sync_vehicle_images(self, vehicle_data, dealership_id, dms_type):
        """Sync images for a single vehicle"""
        synced_count = 0
        errors = []
        
        try:
            image_urls = vehicle_data.get('images', [])
            
            for i, image_url in enumerate(image_urls):
                try:
                    # Download image from DMS
                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()
                    
                    # Create a file-like object from the response content
                    from io import BytesIO
                    image_file = BytesIO(response.content)
                    image_file.name = f"{vehicle_data['stock_number']}_{i+1}.jpg"
                    
                    # Prepare vehicle data for image service
                    vehicle_metadata = {
                        'year': vehicle_data.get('year'),
                        'make': vehicle_data.get('make'),
                        'model': vehicle_data.get('model'),
                        'vin': vehicle_data.get('vin'),
                        'stock_number': vehicle_data.get('stock_number'),
                        'alt_text': f"{vehicle_data.get('year')} {vehicle_data.get('make')} {vehicle_data.get('model')}",
                        'tags': [vehicle_data.get('make', '').lower(), vehicle_data.get('model', '').lower(), 'dms-sync']
                    }
                    
                    # Save image using image service
                    image_record, save_message = self.image_service.save_image(
                        image_file, dealership_id, vehicle_metadata, 'dms'
                    )
                    
                    if image_record:
                        # Update with DMS-specific data
                        image_record.source_url = image_url
                        image_record.dms_id = f"{dms_type}_{vehicle_data['stock_number']}_{i+1}"
                        if i == 0:  # Set first image as primary
                            image_record.is_primary = True
                        db.session.commit()
                        
                        synced_count += 1
                    else:
                        errors.append(f"Image {i+1}: {save_message}")
                        
                except Exception as e:
                    errors.append(f"Image {i+1} from {image_url}: {str(e)}")
            
        except Exception as e:
            errors.append(f"Vehicle sync error: {str(e)}")
        
        return synced_count, errors
    
    def schedule_dms_sync(self, dms_type, credentials, dealership_id, sync_frequency='daily'):
        """Schedule automatic DMS synchronization"""
        try:
            # This would integrate with a task scheduler like Celery
            # For now, we'll store the sync configuration
            
            sync_config = {
                'dms_type': dms_type,
                'credentials': credentials,  # Should be encrypted in production
                'dealership_id': dealership_id,
                'sync_frequency': sync_frequency,
                'last_sync': None,
                'next_sync': self._calculate_next_sync(sync_frequency),
                'is_active': True
            }
            
            # In a real implementation, this would be stored in a database
            # and processed by a background task scheduler
            
            return True, f"DMS sync scheduled for {sync_frequency} frequency"
            
        except Exception as e:
            return False, f"Failed to schedule DMS sync: {str(e)}"
    
    def _calculate_next_sync(self, frequency):
        """Calculate next sync time based on frequency"""
        now = datetime.utcnow()
        
        if frequency == 'hourly':
            return now + timedelta(hours=1)
        elif frequency == 'daily':
            return now + timedelta(days=1)
        elif frequency == 'weekly':
            return now + timedelta(weeks=1)
        else:
            return now + timedelta(days=1)  # Default to daily
    
    def get_dms_sync_status(self, dealership_id):
        """Get DMS synchronization status"""
        try:
            # This would query the database for sync status
            # For demo purposes, return sample status
            
            return {
                'is_configured': True,
                'dms_type': 'dealersocket',
                'last_sync': '2025-07-12T20:00:00Z',
                'next_sync': '2025-07-13T20:00:00Z',
                'sync_frequency': 'daily',
                'total_synced': 156,
                'last_sync_results': {
                    'vehicles_processed': 12,
                    'images_synced': 48,
                    'errors': 2
                },
                'is_active': True
            }
            
        except Exception as e:
            return {
                'is_configured': False,
                'error': str(e)
            }

