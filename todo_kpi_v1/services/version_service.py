from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import pytz

# 平台类型枚举
class PlatformType:
    WINDOWS = 'windows'
    MACOS = 'macos'

# 获取本地时区
local_tz = pytz.timezone('Asia/Shanghai')

class VersionService:
    def __init__(self, app: Flask):
        self.app = app
        self.db = SQLAlchemy(app)
        self._setup_database()
        self._setup_config()

    def _setup_database(self):
        # 版本模型
        class Version(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            version = self.db.Column(self.db.String(20), unique=True, nullable=False)
            platform = self.db.Column(self.db.String(20), nullable=False)
            description = self.db.Column(self.db.Text)
            is_active = self.db.Column(self.db.Boolean, default=True)
            created_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(local_tz))
            updated_at = self.db.Column(self.db.DateTime, default=lambda: datetime.now(local_tz), onupdate=lambda: datetime.now(local_tz))

            def to_dict(self):
                suffix = '.exe' if self.platform == PlatformType.WINDOWS else '.dmg'
                return {
                    'id': self.id,
                    'version': self.version,
                    'platform': self.platform,
                    'description': self.description,
                    'download_url': f"{self.app.config['DOWNLOAD_URL_PREFIX']}{self.version}{suffix}",
                    'is_active': self.is_active,
                    'created_at': self.created_at.astimezone(local_tz).isoformat(),
                    'updated_at': self.updated_at.astimezone(local_tz).isoformat()
                }

        self.Version = Version

    def _setup_config(self):
        # 获取当前文件所在目录的上级目录中的packages文件夹路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        packages_dir = os.path.join(parent_dir, 'packages')
        # 确保packages目录存在
        os.makedirs(packages_dir, exist_ok=True)
        # 设置下载地址前缀为file://协议
        self.app.config['DOWNLOAD_URL_PREFIX'] = f'file://{packages_dir}/TodoTracker_release_'

    def create_tables(self):
        with self.app.app_context():
            self.db.create_all()

    def check_update(self, current_version: str, platform: str):
        if not current_version or not platform:
            return {'error': 'Missing version or platform parameter'}, 400

        if platform not in [PlatformType.WINDOWS, PlatformType.MACOS]:
            return {'error': 'Invalid platform'}, 400

        latest_version = self.Version.query.filter_by(
            platform=platform
        ).order_by(self.Version.version.desc()).first()
        
        if not latest_version:
            return {
                'has_update': False,
                'message': 'No version found for this platform'
            }

        has_update = latest_version.version > current_version
        suffix = '.exe' if platform == PlatformType.WINDOWS else '.dmg'
        
        return {
            'has_update': has_update,
            'version': latest_version.version if has_update else current_version,
            'download_url': f"{self.app.config['DOWNLOAD_URL_PREFIX']}{latest_version.version}{suffix}" if has_update else None,
            'description': latest_version.description if has_update else None
        }

    def get_versions(self, platform: str = None):
        query = self.Version.query
        
        if platform:
            if platform not in [PlatformType.WINDOWS, PlatformType.MACOS]:
                return {'error': 'Invalid platform'}, 400
            query = query.filter_by(platform=platform)
        
        versions = query.order_by(self.Version.id.desc()).all()
        return [version.to_dict() for version in versions]

    def get_version(self, version_id: int):
        version = self.Version.query.get_or_404(version_id)
        return version.to_dict()

    def create_version(self, data: dict):
        required_fields = ['version', 'platform']
        
        if not all(field in data for field in required_fields):
            return {'error': 'Missing required fields'}, 400
            
        if data['platform'] not in [PlatformType.WINDOWS, PlatformType.MACOS]:
            return {'error': 'Invalid platform'}, 400
            
        try:
            version = self.Version(
                version=data['version'],
                platform=data['platform'],
                description=data.get('description', ''),
                is_active=data.get('is_active', True)
            )
            self.db.session.add(version)
            self.db.session.commit()
            return version.to_dict(), 201
        except Exception as e:
            self.db.session.rollback()
            return {'error': str(e)}, 400

    def update_version(self, version_id: int, data: dict):
        version = self.Version.query.get_or_404(version_id)
        
        try:
            if 'version' in data:
                version.version = data['version']
            if 'platform' in data:
                if data['platform'] not in [PlatformType.WINDOWS, PlatformType.MACOS]:
                    return {'error': 'Invalid platform'}, 400
                version.platform = data['platform']
            if 'description' in data:
                version.description = data['description']
            if 'is_active' in data:
                version.is_active = data['is_active']
                
            self.db.session.commit()
            return version.to_dict()
        except Exception as e:
            self.db.session.rollback()
            return {'error': str(e)}, 400

    def delete_version(self, version_id: int):
        version = self.Version.query.get_or_404(version_id)
        try:
            self.db.session.delete(version)
            self.db.session.commit()
            return 'success', 204
        except Exception as e:
            self.db.session.rollback()
            return {'error': str(e)}, 400 