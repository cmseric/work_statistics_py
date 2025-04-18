from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///versions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 获取当前文件所在目录的上级目录中的packages文件夹路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
packages_dir = os.path.join(parent_dir, 'packages')
# 确保packages目录存在
os.makedirs(packages_dir, exist_ok=True)
# 设置下载地址前缀为file://协议
app.config['DOWNLOAD_URL_PREFIX'] = f'file://{packages_dir}/TodoTracker_release_'

# 平台类型枚举
class PlatformType:
    WINDOWS = 'windows'
    MACOS = 'macos'

db = SQLAlchemy(app)

# 获取本地时区
local_tz = pytz.timezone('Asia/Shanghai')

# 版本模型
class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), unique=True, nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # 新增平台字段
    description = db.Column(db.Text)
    download_url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(local_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(local_tz), onupdate=lambda: datetime.now(local_tz))

    def to_dict(self):
        # 根据平台添加对应的后缀
        suffix = '.exe' if self.platform == PlatformType.WINDOWS else '.app'
        return {
            'id': self.id,
            'version': self.version,
            'platform': self.platform,
            'description': self.description,
            'download_url': f"{app.config['DOWNLOAD_URL_PREFIX']}{self.version}{suffix}",
            'is_active': self.is_active,
            'created_at': self.created_at.astimezone(local_tz).isoformat(),
            'updated_at': self.updated_at.astimezone(local_tz).isoformat()
        }

# 创建数据库表
with app.app_context():
    db.create_all()

# 检查版本更新
@app.route('/api/check-update', methods=['GET'])
def check_update():
    current_version = request.args.get('version')
    platform = request.args.get('platform')  # 新增平台参数
    
    if not current_version or not platform:
        return jsonify({'error': 'Missing version or platform parameter'}), 400

    if platform not in [PlatformType.WINDOWS, PlatformType.MACOS]:
        return jsonify({'error': 'Invalid platform'}), 400

    # 获取指定平台的最新活跃版本
    latest_version = Version.query.filter_by(
        is_active=True,
        platform=platform
    ).order_by(Version.id.desc()).first()
    
    if not latest_version:
        return jsonify({
            'has_update': False,
            'message': 'No active version found'
        })

    # 比较版本号
    has_update = latest_version.version > current_version
    
    # 根据平台添加对应的后缀
    suffix = '.exe' if platform == PlatformType.WINDOWS else '.app'
    
    return jsonify({
        'has_update': has_update,
        'version': latest_version.version if has_update else current_version,
        'download_url': f"{app.config['DOWNLOAD_URL_PREFIX']}{latest_version.version}{suffix}" if has_update else None,
        'description': latest_version.description if has_update else None
    })

# 获取所有版本
@app.route('/api/versions', methods=['GET'])
def get_versions():
    platform = request.args.get('platform')  # 新增平台参数
    query = Version.query
    
    if platform:
        if platform not in [PlatformType.WINDOWS, PlatformType.MACOS]:
            return jsonify({'error': 'Invalid platform'}), 400
        query = query.filter_by(platform=platform)
    
    versions = query.order_by(Version.id.desc()).all()
    return jsonify([version.to_dict() for version in versions])

# 获取单个版本
@app.route('/api/versions/<int:version_id>', methods=['GET'])
def get_version(version_id):
    version = Version.query.get_or_404(version_id)
    return jsonify(version.to_dict())

# 创建新版本
@app.route('/api/versions', methods=['POST'])
def create_version():
    data = request.json
    required_fields = ['version', 'platform']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
        
    if data['platform'] not in [PlatformType.WINDOWS, PlatformType.MACOS]:
        return jsonify({'error': 'Invalid platform'}), 400
        
    try:
        version = Version(
            version=data['version'],
            platform=data['platform'],
            description=data.get('description', ''),
            download_url=data['version'],
            is_active=data.get('is_active', True)
        )
        db.session.add(version)
        db.session.commit()
        return jsonify(version.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# 更新版本
@app.route('/api/versions/<int:version_id>', methods=['PUT'])
def update_version(version_id):
    version = Version.query.get_or_404(version_id)
    data = request.json
    
    try:
        if 'version' in data:
            version.version = data['version']
            version.download_url = data['version']
        if 'platform' in data:
            if data['platform'] not in [PlatformType.WINDOWS, PlatformType.MACOS]:
                return jsonify({'error': 'Invalid platform'}), 400
            version.platform = data['platform']
        if 'description' in data:
            version.description = data['description']
        if 'is_active' in data:
            version.is_active = data['is_active']
            
        db.session.commit()
        return jsonify(version.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# 删除版本
@app.route('/api/versions/<int:version_id>', methods=['DELETE'])
def delete_version(version_id):
    version = Version.query.get_or_404(version_id)
    try:
        db.session.delete(version)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True) 