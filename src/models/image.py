"""
Image Model for DealerFlow Pro
Handles image storage and metadata
"""

from src.extensions import db
from datetime import datetime

class Image(db.Model):
    __tablename__ = 'images'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    
    # Image source tracking
    source_type = db.Column(db.String(50), nullable=False)  # 'upload', 'dms', 'scraping'
    source_url = db.Column(db.String(500))  # Original URL if scraped
    dms_id = db.Column(db.String(100))  # DMS reference ID
    
    # Vehicle association
    dealership_id = db.Column(db.Integer, db.ForeignKey('dealerships.id'), nullable=False)
    vehicle_year = db.Column(db.String(10))
    vehicle_make = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(50))
    vehicle_vin = db.Column(db.String(17))
    vehicle_stock_number = db.Column(db.String(50))
    
    # Metadata
    alt_text = db.Column(db.Text)
    tags = db.Column(db.Text)  # JSON string of tags
    is_primary = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dealership = db.relationship('Customer', backref='images')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'dms_id': self.dms_id,
            'dealership_id': self.dealership_id,
            'vehicle_year': self.vehicle_year,
            'vehicle_make': self.vehicle_make,
            'vehicle_model': self.vehicle_model,
            'vehicle_vin': self.vehicle_vin,
            'vehicle_stock_number': self.vehicle_stock_number,
            'alt_text': self.alt_text,
            'tags': self.tags,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Image {self.filename} for {self.vehicle_year} {self.vehicle_make} {self.vehicle_model}>'

