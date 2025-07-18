"""
Website Scraping API Routes for DealerFlow Pro
Handles automated website scraping for vehicle images
"""

from flask import Blueprint, request, jsonify
from services.scraping_service import ScrapingService

scraping_bp = Blueprint('scraping', __name__)
scraping_service = ScrapingService()

@scraping_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Scraping service is running',
        'service': 'DealerFlow Pro Website Scraping'
    })

@scraping_bp.route('/detect-platform', methods=['POST'])
def detect_platform():
    """Detect website platform/CMS"""
    try:
        data = request.get_json()
        website_url = data.get('website_url')
        
        if not website_url:
            return jsonify({
                'success': False,
                'error': 'website_url is required'
            }), 400
        
        platform = scraping_service.detect_website_platform(website_url)
        
        return jsonify({
            'success': True,
            'website_url': website_url,
            'platform_detected': platform,
            'message': f'Detected platform: {platform}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Platform detection failed: {str(e)}'
        }), 500

@scraping_bp.route('/find-inventory', methods=['POST'])
def find_inventory_pages():
    """Find inventory pages on a website"""
    try:
        data = request.get_json()
        website_url = data.get('website_url')
        
        if not website_url:
            return jsonify({
                'success': False,
                'error': 'website_url is required'
            }), 400
        
        inventory_urls = scraping_service.find_inventory_pages(website_url)
        
        return jsonify({
            'success': True,
            'website_url': website_url,
            'inventory_pages': inventory_urls,
            'count': len(inventory_urls),
            'message': f'Found {len(inventory_urls)} inventory pages'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Inventory page discovery failed: {str(e)}'
        }), 500

@scraping_bp.route('/scrape-listings', methods=['POST'])
def scrape_vehicle_listings():
    """Scrape vehicle listings from a specific page"""
    try:
        data = request.get_json()
        inventory_url = data.get('inventory_url')
        
        if not inventory_url:
            return jsonify({
                'success': False,
                'error': 'inventory_url is required'
            }), 400
        
        vehicles = scraping_service.scrape_vehicle_listings(inventory_url)
        
        return jsonify({
            'success': True,
            'inventory_url': inventory_url,
            'vehicles': vehicles,
            'count': len(vehicles),
            'message': f'Scraped {len(vehicles)} vehicle listings'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Vehicle listing scraping failed: {str(e)}'
        }), 500

@scraping_bp.route('/scrape-website', methods=['POST'])
def scrape_dealership_website():
    """Scrape entire dealership website for vehicle images"""
    try:
        data = request.get_json()
        
        dealership_id = data.get('dealership_id')
        website_url = data.get('website_url')
        max_vehicles = data.get('max_vehicles', 50)
        
        if not all([dealership_id, website_url]):
            return jsonify({
                'success': False,
                'error': 'dealership_id and website_url are required'
            }), 400
        
        scraped_count, error_count, errors, platform = scraping_service.scrape_dealership_website(
            dealership_id, website_url, max_vehicles
        )
        
        return jsonify({
            'success': True,
            'message': f'Website scraping completed. {scraped_count} images scraped, {error_count} errors.',
            'website_url': website_url,
            'platform_detected': platform,
            'scraped_count': scraped_count,
            'error_count': error_count,
            'errors': errors if error_count > 0 else None,
            'max_vehicles': max_vehicles
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Website scraping failed: {str(e)}'
        }), 500

@scraping_bp.route('/schedule-scraping', methods=['POST'])
def schedule_scraping():
    """Schedule automatic website scraping"""
    try:
        data = request.get_json()
        
        dealership_id = data.get('dealership_id')
        website_url = data.get('website_url')
        scrape_frequency = data.get('scrape_frequency', 'weekly')
        
        if not all([dealership_id, website_url]):
            return jsonify({
                'success': False,
                'error': 'dealership_id and website_url are required'
            }), 400
        
        success, message = scraping_service.schedule_website_scraping(
            dealership_id, website_url, scrape_frequency
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'website_url': website_url,
                'scrape_frequency': scrape_frequency
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to schedule website scraping: {str(e)}'
        }), 500

@scraping_bp.route('/scraping-status/<int:dealership_id>', methods=['GET'])
def get_scraping_status(dealership_id):
    """Get website scraping status"""
    try:
        status = scraping_service.get_scraping_status(dealership_id)
        
        return jsonify({
            'success': True,
            'scraping_status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve scraping status: {str(e)}'
        }), 500

@scraping_bp.route('/configure', methods=['POST'])
def configure_scraping():
    """Configure website scraping for a dealership"""
    try:
        data = request.get_json()
        
        dealership_id = data.get('dealership_id')
        website_url = data.get('website_url')
        scraping_settings = data.get('scraping_settings', {})
        
        if not all([dealership_id, website_url]):
            return jsonify({
                'success': False,
                'error': 'dealership_id and website_url are required'
            }), 400
        
        # Detect platform first
        platform = scraping_service.detect_website_platform(website_url)
        
        # Find inventory pages
        inventory_pages = scraping_service.find_inventory_pages(website_url)
        
        # Schedule scraping if requested
        scrape_frequency = scraping_settings.get('frequency', 'weekly')
        schedule_success, schedule_message = scraping_service.schedule_website_scraping(
            dealership_id, website_url, scrape_frequency
        )
        
        if schedule_success:
            return jsonify({
                'success': True,
                'message': 'Website scraping configured successfully',
                'website_url': website_url,
                'platform_detected': platform,
                'inventory_pages_found': len(inventory_pages),
                'inventory_pages': inventory_pages,
                'scrape_frequency': scrape_frequency,
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
            'error': f'Scraping configuration failed: {str(e)}'
        }), 500

@scraping_bp.route('/test-scraping', methods=['POST'])
def test_scraping():
    """Test scraping on a website without saving images"""
    try:
        data = request.get_json()
        website_url = data.get('website_url')
        
        if not website_url:
            return jsonify({
                'success': False,
                'error': 'website_url is required'
            }), 400
        
        # Detect platform
        platform = scraping_service.detect_website_platform(website_url)
        
        # Find inventory pages
        inventory_pages = scraping_service.find_inventory_pages(website_url)
        
        # Test scraping on first inventory page
        test_results = []
        if inventory_pages:
            vehicles = scraping_service.scrape_vehicle_listings(inventory_pages[0])
            test_results = vehicles[:5]  # Return first 5 vehicles as test
        
        return jsonify({
            'success': True,
            'message': 'Scraping test completed',
            'website_url': website_url,
            'platform_detected': platform,
            'inventory_pages_found': len(inventory_pages),
            'test_vehicles': test_results,
            'test_vehicle_count': len(test_results),
            'estimated_total_images': sum(len(v.get('images', [])) for v in test_results) * (len(inventory_pages) if inventory_pages else 1)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Scraping test failed: {str(e)}'
        }), 500



@scraping_bp.route('/setup', methods=['POST'])
def setup_scraping():
    """Setup website scraping for a dealership (frontend compatibility endpoint)"""
    try:
        data = request.get_json()
        
        dealership_id = data.get('dealership_id')
        website_url = data.get('website_url')
        
        if not all([dealership_id, website_url]):
            return jsonify({
                'success': False,
                'error': 'dealership_id and website_url are required'
            }), 400
        
        # Detect platform first
        platform = scraping_service.detect_website_platform(website_url)
        
        # Find inventory pages
        inventory_pages = scraping_service.find_inventory_pages(website_url)
        
        # Schedule weekly scraping by default
        schedule_success, schedule_message = scraping_service.schedule_website_scraping(
            dealership_id, website_url, 'weekly'
        )
        
        if schedule_success:
            return jsonify({
                'success': True,
                'message': 'Website scraping setup completed successfully',
                'website_url': website_url,
                'platform_detected': platform,
                'inventory_pages_found': len(inventory_pages),
                'status': 'configured',
                'last_sync': None,
                'url': website_url
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Setup failed: {schedule_message}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Scraping setup failed: {str(e)}'
        }), 500

