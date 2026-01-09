import requests
import json
import time
import random
from typing import Dict, List, Optional

class XiaohongshuCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.xiaohongshu.com/',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.session = requests.Session()
        self.base_url = "https://www.xiaohongshu.com/"
        
    def search_posts(self, keyword: str, max_pages: int = 5) -> List[Dict]:
        """
        搜索相关帖子
        """
        posts = []
        for page in range(1, max_pages + 1):
            try:
                # 注意：小红书搜索接口需要登录且有加密参数
                params = {
                    'keyword': keyword,
                    'page': page,
                    'page_size': 20,
                    'sort': 'general',  # 综合排序
                    'note_type': 0  # 0表示全部
                }
                
                # 实际请求需要处理加密参数和cookies
                # 这里只是示例，实际需要逆向分析接口
                url = "https://www.xiaohongshu.com/fe_api/burdiness/weixin/v2/search/notes"
                
                response = self.session.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('success'):
                    for item in data.get('data', {}).get('notes', []):
                        post = {
                            'note_id': item.get('id'),
                            'title': item.get('title'),
                            'desc': item.get('desc'),
                            'likes': item.get('likes', 0),
                            'collects': item.get('collects', 0),
                            'comments': item.get('comments', 0),
                            'user_name': item.get('user', {}).get('nickname'),
                            'publish_time': item.get('time'),
                            'url': f"https://www.xiaohongshu.com/explore/{item.get('id')}"
                        }
                        posts.append(post)
                
                print(f"第{page}页爬取完成，获取到{len(posts)}条数据")
                time.sleep(random.uniform(2, 4))  # 避免请求过快
                
            except Exception as e:
                print(f"搜索第{page}页时出错: {e}")
                break
        
        return posts
    
    def get_comments(self, note_id: str, max_comments: int = 100) -> List[Dict]:
        """
        获取帖子评论
        """
        comments = []
        cursor = ""
        
        try:
            while len(comments) < max_comments:
                params = {
                    'note_id': note_id,
                    'cursor': cursor,
                    'top_comment_id': '',
                    'image_formats': 'jpg,webp',
                    'num': 10  # 每次请求数量
                }
                
                url = "https://www.xiaohongshu.com/fe_api/burdiness/weixin/v2/note/comments"
                response = self.session.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('success'):
                    for comment in data.get('data', {}).get('comments', []):
                        comment_data = {
                            'comment_id': comment.get('id'),
                            'content': comment.get('content'),
                            'likes': comment.get('like_count', 0),
                            'user_name': comment.get('user_info', {}).get('nickname'),
                            'create_time': comment.get('create_time'),
                            'reply_count': comment.get('sub_comment_count', 0)
                        }
                        comments.append(comment_data)
                    
                    # 检查是否有更多评论
                    has_more = data.get('data', {}).get('has_more', False)
                    cursor = data.get('data', {}).get('cursor', '')
                    
                    if not has_more or not cursor:
                        break
                
                time.sleep(random.uniform(1, 2))
                
        except Exception as e:
            print(f"获取评论时出错: {e}")
        
        return comments[:max_comments]
    
    def save_to_file(self, data: List[Dict], filename: str):
        """保存数据到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")

def main():
    # 初始化爬虫
    crawler = XiaohongshuCrawler()
    
    # 搜索关键词
    keyword = "星露谷物语"
    
    print(f"开始搜索关键词: {keyword}")
    
    # 搜索帖子
    posts = crawler.search_posts(keyword, max_pages=3)
    
    if posts:
        print(f"共找到 {len(posts)} 条相关帖子")
        
        # 保存帖子信息
        crawler.save_to_file(posts, f"xiaohongshu_{keyword}_posts.json")
        
        # 获取每个帖子的评论（示例：只获取前5个帖子的评论）
        all_comments = []
        for i, post in enumerate(posts[:5]):
            print(f"正在获取帖子 '{post.get('title', '无标题')}' 的评论...")
            comments = crawler.get_comments(post['note_id'], max_comments=50)
            all_comments.extend(comments)
            print(f"  获取到 {len(comments)} 条评论")
        
        # 保存评论信息
        crawler.save_to_file(all_comments, f"xiaohongshu_{keyword}_comments.json")
    else:
        print("未找到相关帖子")

if __name__ == "__main__":
    main()
