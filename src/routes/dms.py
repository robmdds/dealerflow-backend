"""
DMS Integration API Routes for DealerFlow Pro
Handles DMS configuration and synchronization
"""

from flask import Blueprint, request, jsonify
from services.dms_service import DMSService

dms_bp = Blueprint('dms', __name__)
dms_service = DMSService()

@dms_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'DMS service is running',
        'service': 'DealerFlow Pro DMS Integration'
    })

@dms_bp.route('/supported-systems', methods=['GET'])
def get_supported_dms():
    """Get list of supported DMS systems"""
    try:
        dms_list = dms_service.get_supported_dms_list()
        
        return jsonify({
            'success': True,
            'dms_systems': dms_list,
            'count': len(dms_list)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve DMS systems: {str(e)}'
        }), 500

@dms_bp.route('/validate-credentials', methods=['POST'])
def validate_credentials():
    """Validate DMS API credentials"""
    try:
        data = request.get_json()
        
        dms_type = data.get('dms_type')
        credentials = data.get('credentials', {})
        
        if not dms_type:
            return jsonify({
                'success': False,
                'error': 'dms_type is required'
            }), 400
        
        if not credentials:
            return jsonify({
                'success': False,
                'error': 'credentials are required'
            }), 400
        
        is_valid, message = dms_service.validate_dms_credentials(dms_type, credentials)
        
        return jsonify({
            'success': is_valid,
            'message': message,
            'is_valid': is_valid
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Credential validation failed: {str(e)}'
        }), 500

@dms_bp.route('/fetch-inventory', methods=['POST'])
def fetch_inventory():
    """Fetch inventory data from DMS"""
    try:
        data = request.get_json()
        
        dms_type = data.get('dms_type')
        credentials = data.get('credentials', {})
        dealership_id = data.get('dealership_id')
        filters = data.get('filters', {})
        
        if not all([dms_type, credentials, dealership_id]):
            return jsonify({
                'success': False,
                'error': 'dms_type, credentials, and dealership_id are required'
            }), 400
        
        inventory_data, message = dms_service.fetch_inventory_data(
            dms_type, credentials, dealership_id, filters
        )
        
        if inventory_data is not None:
            return jsonify({
                'success': True,
                'message': message,
                'inventory': inventory_data,
                'count': len(inventory_data)
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Inventory fetch failed: {str(e)}'
        }), 500

@dms_bp.route('/sync-images', methods=['POST'])
def sync_dms_images():
    """Sync images from DMS to local storage"""
    try:
        data = request.get_json()
        
        dms_type = data.get('dms_type')
        credentials = data.get('credentials', {})
        dealership_id = data.get('dealership_id')
        vehicle_filters = data.get('vehicle_filters', {})
        
        if not all([dms_type, credentials, dealership_id]):
            return jsonify({
                'success': False,
                'error': 'dms_type, credentials, and dealership_id are required'
            }), 400
        
        synced_count, error_count, errors = dms_service.sync_dms_images(
            dms_type, credentials, dealership_id, vehicle_filters
        )
        
        return jsonify({
            'success': True,
            'message': f'DMS sync completed. {synced_count} images synced, {error_count} errors.',
            'synced_count': synced_count,
            'error_count': error_count,
            'errors': errors if error_count > 0 else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'DMS image sync failed: {str(e)}'
        }), 500

@dms_bp.route('/schedule-sync', methods=['POST'])
def schedule_sync():
    """Schedule automatic DMS synchronization"""
    try:
        data = request.get_json()
        
        dms_type = data.get('dms_type')
        credentials = data.get('credentials', {})
        dealership_id = data.get('dealership_id')
        sync_frequency = data.get('sync_frequency', 'daily')
        
        if not all([dms_type, credentials, dealership_id]):
            return jsonify({
                'success': False,
                'error': 'dms_type, credentials, and dealership_id are required'
            }), 400
        
        success, message = dms_service.schedule_dms_sync(
            dms_type, credentials, dealership_id, sync_frequency
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'sync_frequency': sync_frequency
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to schedule DMS sync: {str(e)}'
        }), 500

@dms_bp.route('/sync-status/<int:dealership_id>', methods=['GET'])
def get_sync_status(dealership_id):
    """Get DMS synchronization status"""
    try:
        status = dms_service.get_dms_sync_status(dealership_id)
        
        return jsonify({
            'success': True,
            'sync_status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve sync status: {str(e)}'
        }), 500

@dms_bp.route('/configure', methods=['POST'])
def configure_dms():
    """Configure DMS integration for a dealership"""
    try:
        data = request.get_json()
        
        dealership_id = data.get('dealership_id')
        dms_type = data.get('dms_type')
        credentials = data.get('credentials', {})
        sync_settings = data.get('sync_settings', {})
        
        if not all([dealership_id, dms_type, credentials]):
            return jsonify({
                'success': False,
                'error': 'dealership_id, dms_type, and credentials are required'
            }), 400
        
        # Validate credentials first
        is_valid, validation_message = dms_service.validate_dms_credentials(dms_type, credentials)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Invalid credentials: {validation_message}'
            }), 400
        
        # Schedule sync if requested
        sync_frequency = sync_settings.get('frequency', 'daily')
        schedule_success, schedule_message = dms_service.schedule_dms_sync(
            dms_type, credentials, dealership_id, sync_frequency
        )
        
        if schedule_success:
            return jsonify({
                'success': True,
                'message': 'DMS integration configured successfully',
                'dms_type': dms_type,
                'sync_frequency': sync_frequency,
                'validation_message': validation_message,
                'schedule_message': schedule_message
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Configuration failed: {schedule_message}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'DMS configuration failed: {str(e)}'
        }), 500

