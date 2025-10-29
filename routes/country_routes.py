from flask import Blueprint, request, jsonify, send_file, current_app
from services.country_service import CountryService
country_db = Blueprint('country_db', __name__)

@country_db.route('/countries', methods=['POST'])
def add_country():
    data = request.get_json()
    response, status = CountryService.create_country(data)
    return jsonify(response), status

@country_db.route('/countries', methods=['GET'])
def get_all_countries():
    response, status = CountryService.get_all_countries()
    return jsonify(response), status

@country_db.route('/countries/<int:country_id>', methods=['GET'])
def get_country(country_id):
    response, status = CountryService.get_country_by_id_service(country_id)
    return jsonify(response), status

@country_db.route('/countries/<int:country_id>', methods=['PUT'])
def update_country(country_id):
    data = request.get_json()
    response, status = CountryService.update_country_service(country_id, data)
    return jsonify(response), status

@country_db.route('/countries/<int:country_id>', methods=['DELETE'])
def delete_country(country_id):
    response, status = CountryService.delete_country_service(country_id)
    return jsonify(response), status
@country_db.route('/countries/refresh', methods=['POST'])
def refresh_countries():
    response, status = CountryService.refresh_countries()
    return jsonify(response), status

@country_db.route('/status', methods=['GET'])
def status():
    response, status = CountryService.get_status()
    return jsonify(response), status

@country_db.route('/countries/image', methods=['GET'])
def get_country_image():
    image_path = CountryService.get_summary_image_path()
    if not image_path:
        return jsonify({"message": "summary image not found"}), 404
    return send_file(image_path, mimetype='image/jpeg')