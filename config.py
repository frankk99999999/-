# -*- coding: utf-8 -*-
"""
配置文件 - 存储应用程序的配置信息
"""
import os

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """应用配置类"""
    # 密钥，用于会话加密
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campus-trading-secret-key-2024'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'campus_trading.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传文件大小：16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 分页配置
    ITEMS_PER_PAGE = 12
    
    # 商品分类
    PRODUCT_CATEGORIES = {
        'books': '书籍',
        'electronics': '电子产品',
        'life': '生活用品',
        'sports': '运动器材'
    }
