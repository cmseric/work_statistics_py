from flask import Flask
from .base_routes import register_base_routes
from .version_routes import register_version_routes
from .deepseek_routes import register_deepseek_routes
from ..version_service import VersionService
from ..deepseek_service import DeepSeekService

def register_routes(app, version_service, deepseek_service, ai_chat_service):
    """注册所有路由"""
    register_base_routes(app)
    register_version_routes(app, version_service)
    register_deepseek_routes(app, deepseek_service) 