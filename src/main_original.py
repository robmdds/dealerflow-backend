import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.extensions import db
from src.models.user import User
from src.models.dealership import Dealership, SocialMediaAccount, ContentTemplate, Post
from src.models.image import Image
from src.routes.user import user_bp
from src.routes.dealership import dealership_bp
from src.routes.content import content_bp
from src.routes.social_accounts import social_accounts_bp
from src.routes.automation import automation_bp
from src.routes.images import images_bp
from src.routes.dms import dms_bp
from src.routes.scraping import scraping_bp
from src.routes.auth import auth_bp
from src.routes.payments import payments_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'dealerflow-pro-secret-key-2024'

# Enable CORS for all routes
CORS(app, origins=["https://postflowpro.com"])

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(dealership_bp, url_prefix='/api/dealerships')
app.register_blueprint(content_bp, url_prefix='/api/content')
app.register_blueprint(social_accounts_bp, url_prefix='/api/social-accounts')
app.register_blueprint(automation_bp, url_prefix='/api/automation')
app.register_blueprint(images_bp, url_prefix='/api/images')
app.register_blueprint(dms_bp, url_prefix='/api/dms')
app.register_blueprint(scraping_bp, url_prefix='/api/scraping')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(payments_bp, url_prefix='/api/payments')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create all database tables
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'DealerFlow Pro API'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

