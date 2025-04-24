from flask import Blueprint, request, jsonify, Flask
from ..version_service import VersionService

def create_base_routes(version_service: VersionService) -> Blueprint:
    api_bp = Blueprint('api', __name__)

    @api_bp.route('/check-update', methods=['GET'])
    def check_update():
        current_version = request.args.get('version')
        platform = request.args.get('platform')
        result = version_service.check_update(current_version, platform)
        return jsonify(result[0]), result[1] if len(result) > 1 else 200

    return api_bp

def register_base_routes(app: Flask):
    """注册基础路由"""
    @app.route('/')
    def index():
        return {'status': 'ok', 'message': 'API服务正常运行'} 