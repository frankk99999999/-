# -*- coding: utf-8 -*-
"""
数据库初始化脚本 - 创建数据库表并插入测试数据
运行方式：python init_db.py
"""
from app import app, db
from models import User, Product, Order, Message, BrowseHistory
from datetime import datetime, timedelta
import random


def init_database():
    """初始化数据库"""
    with app.app_context():
        # 删除所有表并重新创建
        db.drop_all()
        db.create_all()
        print("✓ 数据库表创建成功")
        
        # 创建测试用户
        users = create_test_users()
        print(f"✓ 创建了 {len(users)} 个测试用户")
        
        # 创建测试商品
        products = create_test_products(users)
        print(f"✓ 创建了 {len(products)} 个测试商品")
        
        # 创建测试订单
        orders = create_test_orders(users, products)
        print(f"✓ 创建了 {len(orders)} 个测试订单")
        
        # 创建测试私信
        messages = create_test_messages(users, products)
        print(f"✓ 创建了 {len(messages)} 条测试私信")
        
        # 创建浏览记录
        histories = create_test_browse_history(users, products)
        print(f"✓ 创建了 {len(histories)} 条浏览记录")
        
        print("\n" + "="*50)
        print("数据库初始化完成！")
        print("="*50)
        print("\n测试账号信息：")
        print("-"*50)
        print("管理员账号：admin / admin123")
        print("普通用户：user1 / 123456")
        print("普通用户：user2 / 123456")
        print("普通用户：user3 / 123456")
        print("普通用户：user4 / 123456")
        print("-"*50)


def create_test_users():
    """创建测试用户"""
    users = []
    
    # 管理员
    admin = User(
        username='admin',
        email='admin@campus.edu',
        phone='13800000000',
        student_id='2024000000',
        is_admin=True
    )
    admin.set_password('admin123')
    users.append(admin)
    
    # 普通用户
    user_data = [
        ('user1', 'user1@campus.edu', '13800000001', '2024001001'),
        ('user2', 'user2@campus.edu', '13800000002', '2024001002'),
        ('user3', 'user3@campus.edu', '13800000003', '2024001003'),
        ('user4', 'user4@campus.edu', '13800000004', '2024001004'),
    ]
    
    for username, email, phone, student_id in user_data:
        user = User(
            username=username,
            email=email,
            phone=phone,
            student_id=student_id,
            is_admin=False
        )
        user.set_password('123456')
        users.append(user)
    
    for user in users:
        db.session.add(user)
    db.session.commit()
    
    return users


def create_test_products(users):
    """创建测试商品"""
    products_data = [
        # 书籍类
        {
            'title': '高等数学同济第七版上下册',
            'description': '高等数学同济大学第七版，上下两册合售。书本保存良好，有少量笔记，不影响阅读。适合考研或期末复习使用。',
            'price': 35.00,
            'original_price': 89.00,
            'category': 'books',
            'status': 'approved',
            'view_count': 128
        },
        {
            'title': '计算机网络谢希仁第八版',
            'description': '计算机网络经典教材，谢希仁著第八版。9成新，无笔记无划线。期末考试必备，考研408也可以用。',
            'price': 25.00,
            'original_price': 55.00,
            'category': 'books',
            'status': 'approved',
            'view_count': 86
        },
        {
            'title': '数据结构C语言版严蔚敏',
            'description': '数据结构（C语言版）严蔚敏著，计算机专业必修课教材。书籍完好，有部分重点标注。',
            'price': 20.00,
            'original_price': 45.00,
            'category': 'books',
            'status': 'approved',
            'view_count': 92
        },
        
        # 电子产品类
        {
            'title': 'iPad Pro 11寸 2021款',
            'description': 'iPad Pro 11寸 2021款，M1芯片，128G WiFi版。使用一年，外观完好无划痕，电池健康度95%。配送原装充电器和笔。',
            'price': 4500.00,
            'original_price': 6199.00,
            'category': 'electronics',
            'status': 'approved',
            'view_count': 256
        },
        {
            'title': 'AirPods Pro 2代',
            'description': 'AirPods Pro第二代，购于去年双十一。降噪效果很好，电池续航正常。盒子和配件齐全。',
            'price': 1200.00,
            'original_price': 1899.00,
            'category': 'electronics',
            'status': 'approved',
            'view_count': 178
        },
        {
            'title': '小米显示器27寸2K',
            'description': '小米27寸2K显示器，IPS屏幕，75Hz刷新率。使用半年，无坏点，适合日常学习和办公使用。',
            'price': 650.00,
            'original_price': 1099.00,
            'category': 'electronics',
            'status': 'approved',
            'view_count': 134
        },
        
        # 生活用品类
        {
            'title': '九阳电热水壶1.7L',
            'description': '九阳电热水壶，1.7L容量，304不锈钢内胆。使用一学期，功能正常，送备用防尘盖。',
            'price': 35.00,
            'original_price': 89.00,
            'category': 'life',
            'status': 'approved',
            'view_count': 45
        },
        {
            'title': '宜家台灯学习护眼灯',
            'description': '宜家LED护眼台灯，三档调光，USB供电。很适合宿舍使用，光线柔和不刺眼。',
            'price': 45.00,
            'original_price': 99.00,
            'category': 'life',
            'status': 'approved',
            'view_count': 67
        },
        
        # 运动器材类
        {
            'title': '迪卡侬瑜伽垫加厚款',
            'description': '迪卡侬瑜伽垫，8mm加厚款，防滑耐磨。使用过几次，已清洗干净。附送收纳袋和绑带。',
            'price': 40.00,
            'original_price': 79.00,
            'category': 'sports',
            'status': 'approved',
            'view_count': 56
        },
        {
            'title': '李宁羽毛球拍单拍',
            'description': '李宁羽毛球拍，全碳素材质，进攻型。买来打了几次，现在没时间打了。送球拍袋和手胶。',
            'price': 150.00,
            'original_price': 299.00,
            'category': 'sports',
            'status': 'approved',
            'view_count': 89
        },
        
        # 待审核商品
        {
            'title': '全新未拆封机械键盘',
            'description': '某宝抽奖中的机械键盘，红轴，RGB背光。全新未拆封，用不上所以出掉。',
            'price': 200.00,
            'original_price': 399.00,
            'category': 'electronics',
            'status': 'pending',
            'view_count': 0
        },
        {
            'title': '大学英语四级词汇书',
            'description': '四级词汇红宝书，全新未使用，买多了一本。',
            'price': 15.00,
            'original_price': 35.00,
            'category': 'books',
            'status': 'pending',
            'view_count': 0
        },
    ]
    
    products = []
    for i, data in enumerate(products_data):
        # 轮流分配给不同用户（排除admin）
        seller = users[(i % 4) + 1]
        
        product = Product(
            title=data['title'],
            description=data['description'],
            price=data['price'],
            original_price=data['original_price'],
            category=data['category'],
            status=data['status'],
            view_count=data['view_count'],
            seller_id=seller.id,
            created_at=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        products.append(product)
        db.session.add(product)
    
    db.session.commit()
    return products


def create_test_orders(users, products):
    """创建测试订单"""
    orders = []
    
    # 获取已上架的商品
    approved_products = [p for p in products if p.status == 'approved']
    
    if len(approved_products) >= 3:
        # 订单1：待确认
        order1 = Order(
            product_id=approved_products[0].id,
            buyer_id=users[2].id,  # user2购买
            seller_id=approved_products[0].seller_id,
            status='pending',
            created_at=datetime.now() - timedelta(hours=2)
        )
        orders.append(order1)
        
        # 订单2：交易中
        order2 = Order(
            product_id=approved_products[1].id,
            buyer_id=users[3].id,  # user3购买
            seller_id=approved_products[1].seller_id,
            status='trading',
            created_at=datetime.now() - timedelta(days=1)
        )
        orders.append(order2)
        
        # 订单3：已完成
        order3 = Order(
            product_id=approved_products[2].id,
            buyer_id=users[4].id,  # user4购买
            seller_id=approved_products[2].seller_id,
            status='completed',
            created_at=datetime.now() - timedelta(days=3)
        )
        orders.append(order3)
    
    for order in orders:
        db.session.add(order)
    db.session.commit()
    
    return orders


def create_test_messages(users, products):
    """创建测试私信"""
    messages = []
    
    approved_products = [p for p in products if p.status == 'approved']
    
    if len(approved_products) >= 1 and len(users) >= 3:
        # 对话1：user2和user1关于商品的咨询
        product = approved_products[0]
        
        msg1 = Message(
            sender_id=users[2].id,
            receiver_id=users[1].id,
            product_id=product.id,
            content='你好，这本书还有吗？',
            created_at=datetime.now() - timedelta(hours=5)
        )
        messages.append(msg1)
        
        msg2 = Message(
            sender_id=users[1].id,
            receiver_id=users[2].id,
            product_id=product.id,
            content='在的，还有哦',
            created_at=datetime.now() - timedelta(hours=4, minutes=30)
        )
        messages.append(msg2)
        
        msg3 = Message(
            sender_id=users[2].id,
            receiver_id=users[1].id,
            product_id=product.id,
            content='能便宜点吗？30块可以吗？',
            created_at=datetime.now() - timedelta(hours=4)
        )
        messages.append(msg3)
        
        msg4 = Message(
            sender_id=users[1].id,
            receiver_id=users[2].id,
            product_id=product.id,
            content='可以的，你下单吧',
            is_read=False,
            created_at=datetime.now() - timedelta(hours=3)
        )
        messages.append(msg4)
    
    for msg in messages:
        db.session.add(msg)
    db.session.commit()
    
    return messages


def create_test_browse_history(users, products):
    """创建测试浏览记录"""
    histories = []
    
    approved_products = [p for p in products if p.status == 'approved']
    
    # 为user2创建一些浏览记录（用于AI推荐）
    if len(users) >= 3 and len(approved_products) >= 5:
        user = users[2]  # user2
        
        # 浏览书籍类商品
        for product in approved_products[:3]:
            history = BrowseHistory(
                user_id=user.id,
                product_id=product.id,
                created_at=datetime.now() - timedelta(hours=random.randint(1, 48))
            )
            histories.append(history)
        
        # 为user3创建电子产品浏览记录
        user3 = users[3]
        for product in approved_products[3:6]:
            history = BrowseHistory(
                user_id=user3.id,
                product_id=product.id,
                created_at=datetime.now() - timedelta(hours=random.randint(1, 48))
            )
            histories.append(history)
    
    for history in histories:
        db.session.add(history)
    db.session.commit()
    
    return histories


if __name__ == '__main__':
    init_database()
