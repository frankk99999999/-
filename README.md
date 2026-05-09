# 🎓 智能校园二手交易平台

基于 AI 推荐的智能校园二手交易平台，使用 Python Flask 开发，支持商品发布、搜索、AI智能推荐、在线交易和私信沟通等功能。

## ✨ 功能特性

### 1. 用户模块
- 用户注册/登录/退出
- 个人信息管理
- 头像上传

### 2. 商品模块
- 发布二手商品（标题、描述、价格、图片、分类）
- 商品列表展示（分页）
- 商品详情页
- 商品搜索（关键词）
- 商品分类筛选（书籍/电子产品/生活用品/运动器材）

### 3. AI智能推荐模块
- 根据用户浏览记录推荐相似商品
- 基于商品描述的 TF-IDF 相似度匹配
- 商品详情页显示相似商品推荐

### 4. 交易模块
- 发起购买意向
- 站内私信联系卖家
- 订单状态管理（待确认/交易中/已完成/已取消）

### 5. 管理后台
- 商品审核上架
- 用户管理
- 数据统计（今日发布数、成交数）

## 🛠️ 技术栈

- **后端**: Python 3.9+ / Flask
- **前端**: HTML5 / Bootstrap 5 / Bootstrap Icons
- **数据库**: SQLite
- **AI模块**: scikit-learn (TF-IDF) / jieba (中文分词)

## 📦 项目结构

```
Smart-campus-second-hand-trading-platform/
├── app.py                 # 主应用文件
├── config.py              # 配置文件
├── models.py              # 数据库模型
├── recommender.py         # AI推荐模块
├── init_db.py             # 数据库初始化脚本
├── requirements.txt       # 依赖列表
├── README.md              # 项目说明
├── static/                # 静态文件
│   ├── css/
│   ├── js/
│   └── uploads/           # 上传文件目录
│       ├── avatars/       # 用户头像
│       └── products/      # 商品图片
└── templates/             # 模板文件
    ├── base.html          # 基础模板
    ├── index.html         # 首页
    ├── user/              # 用户相关模板
    ├── product/           # 商品相关模板
    ├── order/             # 订单相关模板
    ├── message/           # 私信相关模板
    ├── admin/             # 管理后台模板
    └── errors/            # 错误页面模板
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库（含测试数据）

```bash
python init_db.py
```

### 3. 运行应用

```bash
python app.py
```

### 4. 访问应用

打开浏览器访问：http://localhost:12000

## 👤 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | user1 | 123456 |
| 普通用户 | user2 | 123456 |
| 普通用户 | user3 | 123456 |
| 普通用户 | user4 | 123456 |

## 📊 数据库表结构

### users（用户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String(80) | 用户名 |
| email | String(120) | 邮箱 |
| password_hash | String(256) | 密码哈希 |
| avatar | String(200) | 头像文件名 |
| phone | String(20) | 手机号 |
| student_id | String(20) | 学号 |
| is_admin | Boolean | 是否管理员 |
| created_at | DateTime | 注册时间 |

### products（商品表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String(100) | 商品标题 |
| description | Text | 商品描述 |
| price | Float | 价格 |
| original_price | Float | 原价 |
| category | String(20) | 分类 |
| image | String(200) | 商品图片 |
| status | String(20) | 状态 |
| view_count | Integer | 浏览次数 |
| seller_id | Integer | 卖家ID |
| created_at | DateTime | 发布时间 |

### orders（订单表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| product_id | Integer | 商品ID |
| buyer_id | Integer | 买家ID |
| seller_id | Integer | 卖家ID |
| status | String(20) | 状态 |
| created_at | DateTime | 创建时间 |

### messages（私信表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| sender_id | Integer | 发送者ID |
| receiver_id | Integer | 接收者ID |
| product_id | Integer | 相关商品ID |
| content | Text | 消息内容 |
| is_read | Boolean | 是否已读 |
| created_at | DateTime | 发送时间 |

### browse_history（浏览记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID |
| product_id | Integer | 商品ID |
| created_at | DateTime | 浏览时间 |

## 🤖 AI推荐算法说明

本项目使用 **TF-IDF（词频-逆文档频率）** 算法进行商品相似度计算：

1. **文本特征提取**：将商品标题、描述和分类信息组合成文本
2. **中文分词**：使用 jieba 进行中文分词处理
3. **TF-IDF向量化**：将文本转换为 TF-IDF 向量
4. **余弦相似度计算**：计算商品之间的相似度
5. **推荐生成**：
   - 商品详情页：推荐与当前商品最相似的商品
   - 首页：根据用户浏览历史，计算用户兴趣向量，推荐相似商品

## 📝 注意事项

1. 首次运行请先执行 `python init_db.py` 初始化数据库
2. 上传的图片存储在 `static/uploads/` 目录下
3. 数据库文件 `campus_trading.db` 位于项目根目录
4. 修改配置请编辑 `config.py` 文件

## 📄 License

MIT License