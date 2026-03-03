#!/usr/bin/env python3
"""
Web Search Tool - 网络搜索和内容提取
使用 DuckDuckGo 搜索 + trafilatura 网页提取
"""

from ddgs import DDGS
import trafilatura
import json
from typing import List, Dict, Optional

def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """
    使用 DuckDuckGo 进行全网搜索
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数量
        
    Returns:
        搜索结果列表，每个结果包含 title, href, body
    """
    print(f"🔍 搜索：{query}")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        print(f"✅ 找到 {len(results)} 条结果")
        return results
        
    except Exception as e:
        print(f"❌ 搜索失败：{e}")
        return []

def read_webpage(url: str, max_length: int = 8000) -> Optional[str]:
    """
    读取并提取网页正文内容
    
    Args:
        url: 网页 URL
        max_length: 最大返回字符数
        
    Returns:
        提取的文本内容，失败返回 None
    """
    print(f"📖 读取：{url}")
    
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            print(f"⚠️  无法访问该网页")
            return None
            
        text = trafilatura.extract(
            downloaded,
            include_links=False,
            include_images=False,
            with_metadata=False
        )
        
        if text:
            if len(text) > max_length:
                text = text[:max_length] + "\n\n...[内容截断]..."
            print(f"✅ 提取成功 ({len(text)} 字符)")
            return text
        else:
            print(f"⚠️  提取失败：可能为动态页面")
            return None
            
    except Exception as e:
        print(f"❌ 读取异常：{e}")
        return None

def search_and_read(query: str, read_count: int = 1) -> Dict:
    """
    搜索并读取结果网页
    
    Args:
        query: 搜索关键词
        read_count: 读取前 N 个结果的全文
        
    Returns:
        包含搜索结果和全文的字典
    """
    print("=" * 60)
    print(f"查询：{query}")
    print("=" * 60 + "\n")
    
    # 搜索
    results = search_web(query, max_results=5)
    
    output = {
        'query': query,
        'results': []
    }
    
    if not results:
        return output
    
    # 读取指定数量的网页全文
    for i, result in enumerate(results[:read_count], 1):
        print(f"\n[{i}/{read_count}] 读取全文...")
        url = result.get('href', '')
        
        if url.startswith('http'):
            content = read_webpage(url)
            result['content'] = content
        else:
            result['content'] = None
            
        output['results'].append(result)
    
    return output

# ================= 测试入口 =================
if __name__ == "__main__":
    # 测试搜索
    query = "quantitative finance Python libraries"
    data = search_and_read(query, read_count=2)
    
    # 输出 JSON
    print("\n" + "=" * 60)
    print("【完整结果】")
    print("=" * 60)
    
    for i, r in enumerate(data['results'], 1):
        print(f"\n{i}. {r.get('title', '无标题')}")
        print(f"   {r.get('href', '无链接')}")
        if r.get('content'):
            print(f"   内容长度：{len(r['content'])} 字符")
            print(f"   预览：{r['content'][:200]}...")
