from flask import Flask, request, jsonify
from ..version_service import VersionService

def register_version_routes(app: Flask, version_service: VersionService):
    """注册版本相关路由"""
    @app.route('/api/versions', methods=['GET'])
    def get_versions():
        versions = version_service.get_all_versions()
        return jsonify({'success': True, 'data': versions})

    @app.route('/api/versions', methods=['POST'])
    def create_version():
        data = request.get_json()
        version = version_service.create_version(
            version=data.get('version'),
            description=data.get('description'),
            release_date=data.get('release_date')
        )
        return jsonify({'success': True, 'data': version})

    @app.route('/api/versions/<int:version_id>', methods=['PUT'])
    def update_version(version_id):
        data = request.get_json()
        version = version_service.update_version(
            version_id=version_id,
            version=data.get('version'),
            description=data.get('description'),
            release_date=data.get('release_date')
        )
        return jsonify({'success': True, 'data': version})

    @app.route('/api/versions/<int:version_id>', methods=['DELETE'])
    def delete_version(version_id):
        version_service.delete_version(version_id)
        return jsonify({'success': True}) 