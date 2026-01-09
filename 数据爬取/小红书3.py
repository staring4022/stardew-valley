import urllib.request
import urllib.parse
import json
import time
import random
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XiaohongshuScraper:
    def __init__(self):
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.xiaohongshu.com/',
        }
    
    def make_request(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return response.read().decode('utf-8')
                else:
                    logger.error(f"请求失败，状态码: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return None
    
    def search_posts(self, keyword, page_size=5, max_pages=1):
        all_posts = []
        encoded_keyword = urllib.parse.quote(keyword)
        
        for page in range(max_pages):
            try:
                search_url = f"https://www.xiaohongshu.com/api/sns/web/v1/search/notes?keyword={encoded_keyword}&page={page+1}&page_size={page_size}"
                response_text = self.make_request(search_url)
                
                if response_text:
                    data = json.loads(response_text)
                    if data.get('data') and data['data'].get('notes'):
                        notes = data['data']['notes']
                        all_posts.extend(notes)
                        logger.info(f"获取到 {len(notes)} 个帖子")
                        time.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.error(f"搜索失败: {e}")
        
        return all_posts
    
    def get_post_detail(self, note_id):
        try:
            detail_url = f"https://www.xiaohongshu.com/api/sns/web/v1/feed/detail?note_id={note_id}"
            response_text = self.make_request(detail_url)
            
            if response_text:
                return json.loads(response_text).get('data')
        except Exception as e:
            logger.error(f"获取详情失败: {e}")
        finally:
            time.sleep(random.uniform(1, 3))
    
    def remove_html_tags(self, text):
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

def main():
    scraper = XiaohongshuScraper()
    keyword = "星露谷物语"
    logger.info(f"搜索关键词: {keyword}")
    
    # 只搜索一页，避免被反爬
    posts = scraper.search_posts(keyword, page_size=3, max_pages=1)
    
    if not posts:
        logger.warning("未找到相关帖子")
        return
    
    # 处理找到的帖子
    for i, post in enumerate(posts):
        note_id = post.get('note_id')
        if not note_id:
            continue
            
        logger.info(f"处理帖子 {i+1}/{len(posts)}")
        detail = scraper.get_post_detail(note_id)
        
        if detail and detail.get('note'):
            note = detail['note']
            content = scraper.remove_html_tags(note.get('desc', ''))
            
            # 保存到文本文件
            with open(f"stardew_valley_post_{i+1}.txt", "w", encoding="utf-8") as f:
                f.write(f"标题: {note.get('title', '无标题')}\n")
                f.write(f"作者: {detail.get('user', {}).get('nickname', '未知')}\n")
                f.write(f"点赞数: {note.get('likes', 0)}\n")
                f.write(f"收藏数: {note.get('collections', 0)}\n")
                f.write(f"评论数: {note.get('comments_count', 0)}\n")
                f.write("\n内容:\n")
                f.write(content)
                
            logger.info(f"帖子内容已保存到 stardew_valley_post_{i+1}.txt")

if __name__ == "__main__":
    main()
