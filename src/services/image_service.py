"""
Image Service for DealerFlow Pro
Handles image upload, processing, and management
"""

import os
import uuid
import json
from PIL import Image as PILImage
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from models.image import Image
from extensions import db

class ImageService:
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = 'uploads/images'
    
    def __init__(self):
        # Ensure upload directory exists
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def validate_image(self, file):
        """Validate uploaded image file"""
        if not file or file.filename == '':
            return False, "No file selected"
        
        if not self.allowed_file(file.filename):
            return False, f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB"
        
        return True, "Valid image file"
    
    def process_image(self, file, max_width=1200, max_height=800, quality=85):
        """Process and optimize image"""
        try:
            # Open image with PIL
            img = PILImage.open(file)
            
            # Get original dimensions
            original_width, original_height = img.size
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            if original_width > max_width or original_height > max_height:
                img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
            
            return img, img.size
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")
    
    def save_image(self, file, dealership_id, vehicle_data=None, source_type='upload'):
        """Save uploaded image to filesystem and database"""
        try:
            # Validate file
            is_valid, message = self.validate_image(file)
            if not is_valid:
                return None, message
            
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(self.UPLOAD_FOLDER, unique_filename)
            
            # Process image
            processed_img, (width, height) = self.process_image(file)
            
            # Save processed image
            processed_img.save(file_path, optimize=True, quality=85)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create database record
            image_record = Image(
                filename=unique_filename,
                original_filename=secure_filename(file.filename),
                file_path=file_path,
                file_size=file_size,
                mime_type=f"image/{file_extension}",
                width=width,
                height=height,
                source_type=source_type,
                dealership_id=dealership_id,
                vehicle_year=vehicle_data.get('year') if vehicle_data else None,
                vehicle_make=vehicle_data.get('make') if vehicle_data else None,
                vehicle_model=vehicle_data.get('model') if vehicle_data else None,
                vehicle_vin=vehicle_data.get('vin') if vehicle_data else None,
                vehicle_stock_number=vehicle_data.get('stock_number') if vehicle_data else None,
                alt_text=vehicle_data.get('alt_text') if vehicle_data else None,
                tags=json.dumps(vehicle_data.get('tags', [])) if vehicle_data else None
            )
            
            db.session.add(image_record)
            db.session.commit()
            
            return image_record, "Image uploaded successfully"
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error saving image: {str(e)}"
    
    def get_images_by_dealership(self, dealership_id, vehicle_filters=None):
        """Get all images for a dealership with optional vehicle filters"""
        query = Image.query.filter_by(dealership_id=dealership_id, is_active=True)
        
        if vehicle_filters:
            if vehicle_filters.get('year'):
                query = query.filter_by(vehicle_year=vehicle_filters['year'])
            if vehicle_filters.get('make'):
                query = query.filter_by(vehicle_make=vehicle_filters['make'])
            if vehicle_filters.get('model'):
                query = query.filter_by(vehicle_model=vehicle_filters['model'])
            if vehicle_filters.get('vin'):
                query = query.filter_by(vehicle_vin=vehicle_filters['vin'])
            if vehicle_filters.get('stock_number'):
                query = query.filter_by(vehicle_stock_number=vehicle_filters['stock_number'])
        
        return query.order_by(Image.created_at.desc()).all()
    
    def get_image_by_id(self, image_id, dealership_id=None):
        """Get specific image by ID"""
        query = Image.query.filter_by(id=image_id, is_active=True)
        if dealership_id:
            query = query.filter_by(dealership_id=dealership_id)
        return query.first()
    
    def delete_image(self, image_id, dealership_id=None):
        """Delete image (soft delete)"""
        try:
            image = self.get_image_by_id(image_id, dealership_id)
            if not image:
                return False, "Image not found"
            
            # Soft delete
            image.is_active = False
            db.session.commit()
            
            # Optionally delete physical file
            try:
                if os.path.exists(image.file_path):
                    os.remove(image.file_path)
            except:
                pass  # Don't fail if file deletion fails
            
            return True, "Image deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting image: {str(e)}"
    
    def update_image_metadata(self, image_id, metadata, dealership_id=None):
        """Update image metadata"""
        try:
            image = self.get_image_by_id(image_id, dealership_id)
            if not image:
                return None, "Image not found"
            
            # Update allowed fields
            if 'alt_text' in metadata:
                image.alt_text = metadata['alt_text']
            if 'tags' in metadata:
                image.tags = json.dumps(metadata['tags'])
            if 'vehicle_year' in metadata:
                image.vehicle_year = metadata['vehicle_year']
            if 'vehicle_make' in metadata:
                image.vehicle_make = metadata['vehicle_make']
            if 'vehicle_model' in metadata:
                image.vehicle_model = metadata['vehicle_model']
            if 'vehicle_vin' in metadata:
                image.vehicle_vin = metadata['vehicle_vin']
            if 'vehicle_stock_number' in metadata:
                image.vehicle_stock_number = metadata['vehicle_stock_number']
            if 'is_primary' in metadata:
                image.is_primary = metadata['is_primary']
            
            db.session.commit()
            return image, "Image metadata updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return None, f"Error updating image metadata: {str(e)}"
    
    def get_vehicle_images(self, dealership_id, vehicle_data):
        """Get all images for a specific vehicle"""
        filters = {}
        if vehicle_data.get('vin'):
            filters['vin'] = vehicle_data['vin']
        elif vehicle_data.get('stock_number'):
            filters['stock_number'] = vehicle_data['stock_number']
        else:
            # Fallback to year/make/model matching
            filters.update({
                'year': vehicle_data.get('year'),
                'make': vehicle_data.get('make'),
                'model': vehicle_data.get('model')
            })
        
        return self.get_images_by_dealership(dealership_id, filters)
    
    def get_primary_vehicle_image(self, dealership_id, vehicle_data):
        """Get the primary image for a specific vehicle"""
        images = self.get_vehicle_images(dealership_id, vehicle_data)
        
        # Look for primary image first
        for image in images:
            if image.is_primary:
                return image
        
        # Return first image if no primary set
        return images[0] if images else None

