"""
Image Management API Routes for DealerFlow Pro
Handles image upload, retrieval, and management
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from services.image_service import ImageService
import os

images_bp = Blueprint('images', __name__)
image_service = ImageService()

@images_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Image service is running',
        'service': 'DealerFlow Pro Image Management'
    })

@images_bp.route('/upload', methods=['POST'])
def upload_image():
    """Upload single or multiple images"""
    try:
        dealership_id = request.form.get('dealership_id')
        if not dealership_id:
            return jsonify({
                'success': False,
                'error': 'dealership_id is required'
            }), 400
        
        # Get vehicle data if provided
        vehicle_data = {}
        for field in ['year', 'make', 'model', 'vin', 'stock_number', 'alt_text']:
            if request.form.get(field):
                vehicle_data[field] = request.form.get(field)
        
        # Handle tags
        if request.form.get('tags'):
            vehicle_data['tags'] = request.form.get('tags').split(',')
        
        # Check if files were uploaded
        if 'images' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No images provided'
            }), 400
        
        files = request.files.getlist('images')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': 'No images selected'
            }), 400
        
        uploaded_images = []
        errors = []
        
        for file in files:
            if file.filename != '':
                image_record, message = image_service.save_image(
                    file, 
                    int(dealership_id), 
                    vehicle_data, 
                    'upload'
                )
                
                if image_record:
                    uploaded_images.append(image_record.to_dict())
                else:
                    errors.append(f"{file.filename}: {message}")
        
        if uploaded_images:
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_images)} images',
                'images': uploaded_images,
                'errors': errors if errors else None
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No images could be uploaded',
                'errors': errors
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500

@images_bp.route('/dealership/<int:dealership_id>', methods=['GET'])
def get_dealership_images(dealership_id):
    """Get all images for a dealership"""
    try:
        # Get optional filters
        vehicle_filters = {}
        for field in ['year', 'make', 'model', 'vin', 'stock_number']:
            if request.args.get(field):
                vehicle_filters[field] = request.args.get(field)
        
        images = image_service.get_images_by_dealership(dealership_id, vehicle_filters)
        
        return jsonify({
            'success': True,
            'images': [img.to_dict() for img in images],
            'count': len(images)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve images: {str(e)}'
        }), 500

@images_bp.route('/vehicle', methods=['GET'])
def get_vehicle_images():
    """Get images for a specific vehicle"""
    try:
        dealership_id = request.args.get('dealership_id')
        if not dealership_id:
            return jsonify({
                'success': False,
                'error': 'dealership_id is required'
            }), 400
        
        vehicle_data = {}
        for field in ['year', 'make', 'model', 'vin', 'stock_number']:
            if request.args.get(field):
                vehicle_data[field] = request.args.get(field)
        
        if not vehicle_data:
            return jsonify({
                'success': False,
                'error': 'At least one vehicle identifier is required'
            }), 400
        
        images = image_service.get_vehicle_images(int(dealership_id), vehicle_data)
        primary_image = image_service.get_primary_vehicle_image(int(dealership_id), vehicle_data)
        
        return jsonify({
            'success': True,
            'images': [img.to_dict() for img in images],
            'primary_image': primary_image.to_dict() if primary_image else None,
            'count': len(images)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve vehicle images: {str(e)}'
        }), 500

@images_bp.route('/<int:image_id>', methods=['GET'])
def get_image(image_id):
    """Get specific image by ID"""
    try:
        dealership_id = request.args.get('dealership_id')
        image = image_service.get_image_by_id(image_id, int(dealership_id) if dealership_id else None)
        
        if not image:
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        
        return jsonify({
            'success': True,
            'image': image.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve image: {str(e)}'
        }), 500

@images_bp.route('/<int:image_id>/file', methods=['GET'])
def serve_image_file(image_id):
    """Serve image file"""
    try:
        dealership_id = request.args.get('dealership_id')
        image = image_service.get_image_by_id(image_id, int(dealership_id) if dealership_id else None)
        
        if not image:
            return jsonify({
                'success': False,
                'error': 'Image not found'
            }), 404
        
        if not os.path.exists(image.file_path):
            return jsonify({
                'success': False,
                'error': 'Image file not found'
            }), 404
        
        return send_file(image.file_path, mimetype=image.mime_type)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to serve image: {str(e)}'
        }), 500

@images_bp.route('/<int:image_id>', methods=['PUT'])
def update_image_metadata(image_id):
    """Update image metadata"""
    try:
        dealership_id = request.json.get('dealership_id')
        if not dealership_id:
            return jsonify({
                'success': False,
                'error': 'dealership_id is required'
            }), 400
        
        metadata = request.json.get('metadata', {})
        image, message = image_service.update_image_metadata(image_id, metadata, dealership_id)
        
        if image:
            return jsonify({
                'success': True,
                'message': message,
                'image': image.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update image: {str(e)}'
        }), 500

@images_bp.route('/<int:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete image"""
    try:
        dealership_id = request.args.get('dealership_id')
        success, message = image_service.delete_image(image_id, int(dealership_id) if dealership_id else None)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to delete image: {str(e)}'
        }), 500

@images_bp.route('/bulk-upload', methods=['POST'])
def bulk_upload_images():
    """Bulk upload images with vehicle data"""
    try:
        dealership_id = request.form.get('dealership_id')
        if not dealership_id:
            return jsonify({
                'success': False,
                'error': 'dealership_id is required'
            }), 400
        
        # Get vehicle data from form
        vehicles_data = []
        vehicle_count = int(request.form.get('vehicle_count', 0))
        
        for i in range(vehicle_count):
            vehicle_data = {}
            for field in ['year', 'make', 'model', 'vin', 'stock_number']:
                value = request.form.get(f'vehicle_{i}_{field}')
                if value:
                    vehicle_data[field] = value
            
            if vehicle_data:
                vehicles_data.append(vehicle_data)
        
        # Process uploaded files
        uploaded_images = []
        errors = []
        
        for i, vehicle_data in enumerate(vehicles_data):
            vehicle_files = request.files.getlist(f'vehicle_{i}_images')
            
            for file in vehicle_files:
                if file.filename != '':
                    image_record, message = image_service.save_image(
                        file, 
                        int(dealership_id), 
                        vehicle_data, 
                        'upload'
                    )
                    
                    if image_record:
                        uploaded_images.append(image_record.to_dict())
                    else:
                        errors.append(f"Vehicle {i+1} - {file.filename}: {message}")
        
        return jsonify({
            'success': True,
            'message': f'Bulk upload completed. {len(uploaded_images)} images uploaded.',
            'images': uploaded_images,
            'errors': errors if errors else None,
            'total_uploaded': len(uploaded_images),
            'total_errors': len(errors)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Bulk upload failed: {str(e)}'
        }), 500

