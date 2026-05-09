# -*- coding: utf-8 -*-
"""
数据库模型 - 定义所有数据库表结构
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# 创建数据库实例
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户表 - 存储用户基本信息"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='邮箱')
    password_hash = db.Column(db.String(256), nullable=False, comment='密码哈希值')
    avatar = db.Column(db.String(200), default='default.png', comment='头像文件名')
    phone = db.Column(db.String(20), comment='手机号')
    student_id = db.Column(db.String(20), comment='学号')
    is_admin = db.Column(db.Boolean, default=False, comment='是否为管理员')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='注册时间')
    
    # 关系定义
    products = db.relationship('Product', backref='seller', lazy='dynamic')
    orders_as_buyer = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy='dynamic')
    orders_as_seller = db.relationship('Order', foreign_keys='Order.seller_id', backref='seller', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    browse_histories = db.relationship('BrowseHistory', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码（自动哈希）"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Product(db.Model):
    """商品表 - 存储二手商品信息"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, comment='商品标题')
    description = db.Column(db.Text, nullable=False, comment='商品描述')
    price = db.Column(db.Float, nullable=False, comment='价格')
    original_price = db.Column(db.Float, comment='原价')
    category = db.Column(db.String(20), nullable=False, comment='分类：books/electronics/life/sports')
    image = db.Column(db.String(200), default='default_product.png', comment='商品图片')
    status = db.Column(db.String(20), default='pending', comment='状态：pending待审核/approved已上架/sold已售出/rejected已拒绝')
    view_count = db.Column(db.Integer, default=0, comment='浏览次数')
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='卖家ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='发布时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系定义
    orders = db.relationship('Order', backref='product', lazy='dynamic')
    browse_histories = db.relationship('BrowseHistory', backref='product', lazy='dynamic')
    
    def __repr__(self):
        return f'<Product {self.title}>'


class Order(db.Model):
    """订单表 - 存储交易订单信息"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, comment='商品ID')
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='买家ID')
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='卖家ID')
    status = db.Column(db.String(20), default='pending', comment='状态：pending待确认/trading交易中/completed已完成/cancelled已取消')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<Order {self.id}>'


class Message(db.Model):
    """私信表 - 存储用户之间的私信"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='发送者ID')
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='接收者ID')
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), comment='相关商品ID')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='发送时间')
    
    # 关系定义
    product = db.relationship('Product', backref='messages')
    
    def __repr__(self):
        return f'<Message {self.id}>'


class BrowseHistory(db.Model):
    """浏览记录表 - 存储用户浏览商品的历史记录，用于AI推荐"""
    __tablename__ = 'browse_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, comment='商品ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='浏览时间')
    
    def __repr__(self):
        return f'<BrowseHistory {self.id}>'
