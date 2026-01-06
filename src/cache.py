"""
缓存管理模块
支持基于Hash和语义相似度的缓存
"""
import hashlib
import pickle
import json
from pathlib import Path
from typing import Optional, Any
import numpy as np
from sentence_transformers import SentenceTransformer


class CacheManager:
    """基于Hash的简单缓存"""
    
    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_key(self, text: str, prefix: str = "") -> str:
        """生成缓存key"""
        combined = f"{prefix}:{text}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"⚠️ 缓存读取失败: {e}")
                return None
        return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            print(f"⚠️ 缓存写入失败: {e}")
    
    def clear(self) -> None:
        """清空所有缓存"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        print("✅ 缓存已清空")


class SemanticCache:
    """基于语义相似度的智能缓存"""
    
    def __init__(self, threshold: float = 0.85):
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.cache = []  # [(embedding, query, result), ...]
        self.threshold = threshold
        self.max_size = 100
    
    def get(self, query: str) -> Optional[Any]:
        """基于语义相似度查找缓存"""
        if not self.cache:
            return None
        
        query_embedding = self.model.encode([query])[0]
        
        for cached_embedding, cached_query, cached_result in self.cache:
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > self.threshold:
                print(f"✅ 语义缓存命中 (相似度: {similarity:.2f})")
                print(f"   原始查询: {cached_query[:50]}...")
                return cached_result
        
        return None
    
    def set(self, query: str, result: Any) -> None:
        """保存到语义缓存"""
        embedding = self.model.encode([query])[0]
        self.cache.append((embedding, query, result))
        
        # 限制缓存大小
        if len(self.cache) > self.max_size:
            self.cache.pop(0)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))