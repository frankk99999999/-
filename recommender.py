# -*- coding: utf-8 -*-
"""
AI推荐模块 - 基于TF-IDF算法的商品相似度推荐
"""
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class ProductRecommender:
    """商品推荐器 - 使用TF-IDF算法计算商品相似度"""
    
    def __init__(self):
        # TF-IDF向量化器，使用jieba分词
        self.vectorizer = TfidfVectorizer(tokenizer=self._tokenize)
        self.product_vectors = None
        self.product_ids = []
    
    def _tokenize(self, text):
        """使用jieba进行中文分词"""
        return list(jieba.cut(text))
    
    def _get_product_text(self, product):
        """获取商品的文本特征（标题 + 描述 + 分类）"""
        category_names = {
            'books': '书籍 教材 学习',
            'electronics': '电子 数码 手机 电脑',
            'life': '生活 日用 家居',
            'sports': '运动 健身 体育'
        }
        category_text = category_names.get(product.category, '')
        return f"{product.title} {product.description} {category_text}"
    
    def fit(self, products):
        """
        训练推荐模型
        :param products: 商品列表
        """
        if not products:
            self.product_vectors = None
            self.product_ids = []
            return
        
        # 提取商品文本特征
        texts = [self._get_product_text(p) for p in products]
        self.product_ids = [p.id for p in products]
        
        # 计算TF-IDF向量
        self.product_vectors = self.vectorizer.fit_transform(texts)
    
    def get_similar_products(self, product_id, top_n=6):
        """
        获取与指定商品相似的商品
        :param product_id: 目标商品ID
        :param top_n: 返回的推荐数量
        :return: 相似商品ID列表
        """
        if self.product_vectors is None or product_id not in self.product_ids:
            return []
        
        # 找到目标商品的索引
        idx = self.product_ids.index(product_id)
        
        # 计算与所有商品的相似度
        similarities = cosine_similarity(
            self.product_vectors[idx:idx+1], 
            self.product_vectors
        ).flatten()
        
        # 获取相似度最高的商品（排除自身）
        similar_indices = similarities.argsort()[::-1][1:top_n+1]
        
        return [self.product_ids[i] for i in similar_indices if similarities[i] > 0]
    
    def get_recommendations_by_history(self, browse_history, all_products, top_n=6):
        """
        根据用户浏览历史推荐商品
        :param browse_history: 用户浏览过的商品ID列表
        :param all_products: 所有可推荐的商品
        :param top_n: 返回的推荐数量
        :return: 推荐商品ID列表
        """
        if not browse_history or not all_products:
            return []
        
        # 重新训练模型
        self.fit(all_products)
        
        if self.product_vectors is None:
            return []
        
        # 计算用户兴趣向量（浏览过的商品向量的平均值）
        history_indices = []
        for pid in browse_history:
            if pid in self.product_ids:
                history_indices.append(self.product_ids.index(pid))
        
        if not history_indices:
            return []
        
        # 计算用户兴趣向量
        user_vector = np.asarray(self.product_vectors[history_indices].mean(axis=0))
        
        # 计算与所有商品的相似度
        similarities = cosine_similarity(user_vector, self.product_vectors).flatten()
        
        # 获取相似度最高的商品（排除已浏览的）
        browsed_set = set(browse_history)
        recommendations = []
        
        for idx in similarities.argsort()[::-1]:
            if self.product_ids[idx] not in browsed_set:
                recommendations.append(self.product_ids[idx])
                if len(recommendations) >= top_n:
                    break
        
        return recommendations


# 创建全局推荐器实例
recommender = ProductRecommender()
