# -*- coding: utf-8 -*-
"""
主应用文件 - Flask应用入口和路由定义
"""
import os
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import or_, func

from config import Config
from models import db, User, Product, Order, Message, BrowseHistory
from recommender import recommender

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'


@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return User.query.get(int(user_id))


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """检查文件类型是否允许上传"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ==================== 首页和基础路由 ====================

@app.route('/')
def index():
    """首页 - 展示商品列表和AI推荐"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    
    # 构建查询
    query = Product.query.filter_by(status='approved')
    
    # 分类筛选
    if category:
        query = query.filter_by(category=category)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Product.title.contains(keyword),
                Product.description.contains(keyword)
            )
        )
    
    # 分页
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False
    )
    
    # AI推荐
    recommendations = []
    if current_user.is_authenticated:
        # 获取用户浏览历史
        history = BrowseHistory.query.filter_by(user_id=current_user.id)\
            .order_by(BrowseHistory.created_at.desc()).limit(10).all()
        history_ids = [h.product_id for h in history]
        
        if history_ids:
            # 获取所有上架商品
            all_products = Product.query.filter_by(status='approved').all()
            recommended_ids = recommender.get_recommendations_by_history(history_ids, all_products, 6)
            recommendations = Product.query.filter(Product.id.in_(recommended_ids)).all() if recommended_ids else []
    
    return render_template('index.html', 
                         products=products,
                         recommendations=recommendations,
                         categories=Config.PRODUCT_CATEGORIES,
                         current_category=category,
                         keyword=keyword)


# ==================== 用户模块 ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证
        if not all([username, email, password]):
            flash('请填写所有必填字段', 'danger')
            return render_template('user/register.html')
        
        if password != confirm_password:
            flash('两次密码输入不一致', 'danger')
            return render_template('user/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('user/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
            return render_template('user/register.html')
        
        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('user/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('登录成功', 'success')
            return redirect(next_page or url_for('index'))
        
        flash('用户名或密码错误', 'danger')
    
    return render_template('user/login.html')


@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人信息管理"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        student_id = request.form.get('student_id', '').strip()
        
        # 检查邮箱是否被其他用户使用
        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            flash('邮箱已被其他用户使用', 'danger')
            return render_template('user/profile.html')
        
        current_user.email = email
        current_user.phone = phone
        current_user.student_id = student_id
        
        # 处理头像上传
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{int(datetime.now().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}")
                file.save(os.path.join(Config.UPLOAD_FOLDER, 'avatars', filename))
                current_user.avatar = filename
        
        db.session.commit()
        flash('个人信息更新成功', 'success')
    
    return render_template('user/profile.html')


# ==================== 商品模块 ====================

@app.route('/product/publish', methods=['GET', 'POST'])
@login_required
def publish_product():
    """发布商品"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        original_price = request.form.get('original_price', type=float)
        category = request.form.get('category', '')
        
        # 验证
        if not all([title, description, price, category]):
            flash('请填写所有必填字段', 'danger')
            return render_template('product/publish.html', categories=Config.PRODUCT_CATEGORIES)
        
        if category not in Config.PRODUCT_CATEGORIES:
            flash('无效的分类', 'danger')
            return render_template('product/publish.html', categories=Config.PRODUCT_CATEGORIES)
        
        # 处理图片上传
        image_filename = 'default_product.png'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"product_{current_user.id}_{int(datetime.now().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}")
                file.save(os.path.join(Config.UPLOAD_FOLDER, 'products', filename))
                image_filename = filename
        
        # 创建商品
        product = Product(
            title=title,
            description=description,
            price=price,
            original_price=original_price,
            category=category,
            image=image_filename,
            seller_id=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        
        flash('商品发布成功，等待审核', 'success')
        return redirect(url_for('my_products'))
    
    return render_template('product/publish.html', categories=Config.PRODUCT_CATEGORIES)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """商品详情页"""
    product = Product.query.get_or_404(product_id)
    
    # 只有已上架的商品才能查看（卖家和管理员除外）
    if product.status != 'approved':
        if not current_user.is_authenticated:
            flash('该商品不存在或已下架', 'warning')
            return redirect(url_for('index'))
        if current_user.id != product.seller_id and not current_user.is_admin:
            flash('该商品不存在或已下架', 'warning')
            return redirect(url_for('index'))
    
    # 增加浏览次数
    product.view_count += 1
    db.session.commit()
    
    # 记录浏览历史
    if current_user.is_authenticated:
        # 检查是否已存在相同记录
        existing = BrowseHistory.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if existing:
            existing.created_at = datetime.now()
        else:
            history = BrowseHistory(user_id=current_user.id, product_id=product_id)
            db.session.add(history)
        db.session.commit()
    
    # 获取相似商品推荐
    all_products = Product.query.filter_by(status='approved').all()
    recommender.fit(all_products)
    similar_ids = recommender.get_similar_products(product_id, 4)
    similar_products = Product.query.filter(Product.id.in_(similar_ids)).all() if similar_ids else []
    
    return render_template('product/detail.html', 
                         product=product,
                         similar_products=similar_products,
                         categories=Config.PRODUCT_CATEGORIES)


@app.route('/my_products')
@login_required
def my_products():
    """我发布的商品"""
    products = Product.query.filter_by(seller_id=current_user.id)\
        .order_by(Product.created_at.desc()).all()
    return render_template('product/my_products.html', 
                         products=products,
                         categories=Config.PRODUCT_CATEGORIES)


@app.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """编辑商品"""
    product = Product.query.get_or_404(product_id)
    
    # 只有卖家可以编辑
    if product.seller_id != current_user.id:
        flash('无权编辑此商品', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        product.title = request.form.get('title', '').strip()
        product.description = request.form.get('description', '').strip()
        product.price = request.form.get('price', type=float)
        product.original_price = request.form.get('original_price', type=float)
        product.category = request.form.get('category', '')
        
        # 处理图片上传
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"product_{current_user.id}_{int(datetime.now().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}")
                file.save(os.path.join(Config.UPLOAD_FOLDER, 'products', filename))
                product.image = filename
        
        # 修改后需要重新审核
        product.status = 'pending'
        db.session.commit()
        
        flash('商品更新成功，等待重新审核', 'success')
        return redirect(url_for('my_products'))
    
    return render_template('product/edit.html', 
                         product=product,
                         categories=Config.PRODUCT_CATEGORIES)


@app.route('/product/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """删除商品"""
    product = Product.query.get_or_404(product_id)
    
    # 只有卖家或管理员可以删除
    if product.seller_id != current_user.id and not current_user.is_admin:
        flash('无权删除此商品', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(product)
    db.session.commit()
    
    flash('商品已删除', 'success')
    return redirect(url_for('my_products'))


# ==================== 交易模块 ====================

@app.route('/buy/<int:product_id>', methods=['POST'])
@login_required
def buy_product(product_id):
    """发起购买意向"""
    product = Product.query.get_or_404(product_id)
    
    # 检查商品状态
    if product.status != 'approved':
        flash('该商品不可购买', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # 不能购买自己的商品
    if product.seller_id == current_user.id:
        flash('不能购买自己的商品', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # 检查是否已有订单
    existing = Order.query.filter_by(
        product_id=product_id,
        buyer_id=current_user.id,
        status='pending'
    ).first()
    
    if existing:
        flash('您已发起过购买意向', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # 创建订单
    order = Order(
        product_id=product_id,
        buyer_id=current_user.id,
        seller_id=product.seller_id
    )
    db.session.add(order)
    db.session.commit()
    
    flash('购买意向已发送，等待卖家确认', 'success')
    return redirect(url_for('my_orders'))


@app.route('/my_orders')
@login_required
def my_orders():
    """我的订单（作为买家）"""
    orders = Order.query.filter_by(buyer_id=current_user.id)\
        .order_by(Order.created_at.desc()).all()
    return render_template('order/my_orders.html', orders=orders)


@app.route('/sell_orders')
@login_required
def sell_orders():
    """我收到的订单（作为卖家）"""
    orders = Order.query.filter_by(seller_id=current_user.id)\
        .order_by(Order.created_at.desc()).all()
    return render_template('order/sell_orders.html', orders=orders)


@app.route('/order/confirm/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    """确认订单（卖家操作）"""
    order = Order.query.get_or_404(order_id)
    
    if order.seller_id != current_user.id:
        flash('无权操作此订单', 'danger')
        return redirect(url_for('sell_orders'))
    
    order.status = 'trading'
    db.session.commit()
    
    flash('订单已确认，进入交易中状态', 'success')
    return redirect(url_for('sell_orders'))


@app.route('/order/complete/<int:order_id>', methods=['POST'])
@login_required
def complete_order(order_id):
    """完成订单"""
    order = Order.query.get_or_404(order_id)
    
    if order.seller_id != current_user.id and order.buyer_id != current_user.id:
        flash('无权操作此订单', 'danger')
        return redirect(url_for('my_orders'))
    
    order.status = 'completed'
    order.product.status = 'sold'
    db.session.commit()
    
    flash('交易已完成', 'success')
    if order.seller_id == current_user.id:
        return redirect(url_for('sell_orders'))
    return redirect(url_for('my_orders'))


@app.route('/order/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """取消订单"""
    order = Order.query.get_or_404(order_id)
    
    if order.seller_id != current_user.id and order.buyer_id != current_user.id:
        flash('无权操作此订单', 'danger')
        return redirect(url_for('my_orders'))
    
    order.status = 'cancelled'
    db.session.commit()
    
    flash('订单已取消', 'info')
    if order.seller_id == current_user.id:
        return redirect(url_for('sell_orders'))
    return redirect(url_for('my_orders'))


# ==================== 私信模块 ====================

@app.route('/message/send/<int:receiver_id>', methods=['GET', 'POST'])
@login_required
def send_message(receiver_id):
    """发送私信"""
    receiver = User.query.get_or_404(receiver_id)
    
    if receiver.id == current_user.id:
        flash('不能给自己发送私信', 'danger')
        return redirect(url_for('index'))
    
    product_id = request.args.get('product_id', type=int)
    product = Product.query.get(product_id) if product_id else None
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('消息内容不能为空', 'danger')
            return render_template('message/send.html', receiver=receiver, product=product)
        
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            product_id=product_id,
            content=content
        )
        db.session.add(message)
        db.session.commit()
        
        flash('消息发送成功', 'success')
        return redirect(url_for('chat', user_id=receiver_id))
    
    return render_template('message/send.html', receiver=receiver, product=product)


@app.route('/messages')
@login_required
def messages():
    """消息列表"""
    # 获取所有与当前用户相关的消息对话
    # 按对话用户分组，显示最新消息
    from sqlalchemy import case
    
    # 获取所有相关消息
    all_messages = Message.query.filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).order_by(Message.created_at.desc()).all()
    
    # 按对话用户分组
    conversations = {}
    for msg in all_messages:
        other_user_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        if other_user_id not in conversations:
            other_user = User.query.get(other_user_id)
            unread_count = Message.query.filter_by(
                sender_id=other_user_id,
                receiver_id=current_user.id,
                is_read=False
            ).count()
            conversations[other_user_id] = {
                'user': other_user,
                'last_message': msg,
                'unread_count': unread_count
            }
    
    return render_template('message/list.html', conversations=conversations.values())


@app.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    """与指定用户的对话"""
    other_user = User.query.get_or_404(user_id)
    
    # 获取双方的所有消息
    chat_messages = Message.query.filter(
        or_(
            (Message.sender_id == current_user.id) & (Message.receiver_id == user_id),
            (Message.sender_id == user_id) & (Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at).all()
    
    # 标记为已读
    Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return render_template('message/chat.html', 
                         other_user=other_user,
                         messages=chat_messages)


@app.route('/message/reply/<int:user_id>', methods=['POST'])
@login_required
def reply_message(user_id):
    """回复消息"""
    content = request.form.get('content', '').strip()
    product_id = request.form.get('product_id', type=int)
    
    if not content:
        flash('消息内容不能为空', 'danger')
        return redirect(url_for('chat', user_id=user_id))
    
    message = Message(
        sender_id=current_user.id,
        receiver_id=user_id,
        product_id=product_id if product_id else None,
        content=content
    )
    db.session.add(message)
    db.session.commit()
    
    return redirect(url_for('chat', user_id=user_id))


# ==================== 管理后台 ====================

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """管理后台首页"""
    # 统计数据
    today = datetime.now().date()
    
    stats = {
        'total_users': User.query.count(),
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'pending_products': Product.query.filter_by(status='pending').count(),
        'today_products': Product.query.filter(
            func.date(Product.created_at) == today
        ).count(),
        'today_completed': Order.query.filter(
            Order.status == 'completed',
            func.date(Order.updated_at) == today
        ).count()
    }
    
    # 最近待审核商品
    pending_products = Product.query.filter_by(status='pending')\
        .order_by(Product.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         pending_products=pending_products,
                         categories=Config.PRODUCT_CATEGORIES)


@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    """商品管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Product.query
    if status:
        query = query.filter_by(status=status)
    
    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/products.html', 
                         products=products,
                         current_status=status,
                         categories=Config.PRODUCT_CATEGORIES)


@app.route('/admin/product/approve/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def approve_product(product_id):
    """审核通过商品"""
    product = Product.query.get_or_404(product_id)
    product.status = 'approved'
    db.session.commit()
    
    flash(f'商品《{product.title}》已上架', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/product/reject/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def reject_product(product_id):
    """拒绝商品上架"""
    product = Product.query.get_or_404(product_id)
    product.status = 'rejected'
    db.session.commit()
    
    flash(f'商品《{product.title}》已拒绝', 'warning')
    return redirect(url_for('admin_products'))


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users)


@app.route('/admin/user/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """切换用户管理员状态"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('不能修改自己的管理员状态', 'danger')
        return redirect(url_for('admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = '设为管理员' if user.is_admin else '取消管理员'
    flash(f'用户 {user.username} 已{status}', 'success')
    return redirect(url_for('admin_users'))


# ==================== API接口 ====================

@app.route('/api/unread_count')
@login_required
def get_unread_count():
    """获取未读消息数量"""
    count = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'count': count})


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# ==================== 模板上下文 ====================

@app.context_processor
def inject_globals():
    """注入全局模板变量"""
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Message.query.filter_by(
            receiver_id=current_user.id,
            is_read=False
        ).count()
    
    return {
        'categories': Config.PRODUCT_CATEGORIES,
        'unread_count': unread_count
    }


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=12000, use_reloader=False)
