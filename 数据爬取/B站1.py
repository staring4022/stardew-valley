import urllib.request
import urllib.parse
import json
import csv
import time
import ssl
from urllib.error import HTTPError, URLError

# 忽略SSL证书验证（用于解决某些HTTPS连接问题）
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

def get_bilibili_comments(bvid, output_file):
    """
    爬取B站视频的全部评论并保存为CSV文件
    """
    base_url = "https://api.bilibili.com/x/v2/reply"
    page_size = 20  # 每页评论数
    all_comments = []
    cursor = 0  # 分页游标
    max_retries = 3  # 最大重试次数
    
    print(f"开始爬取视频BV号: {bvid} 的评论...")
    
    while True:
        # 构建请求参数
        params = {
            'type': 1,  # 视频类型
            'oid': get_aid_from_bvid(bvid),  # 需要将BV号转换为aid
            'pn': (cursor // page_size) + 1,  # 页码
            'ps': page_size,  # 每页数量
            'sort': 2  # 按热度排序，0按时间排序
        }
        
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        
        # 添加请求头以模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': f'https://www.bilibili.com/video/{bvid}',
        }
        
        req = urllib.request.Request(url, headers=headers)
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                # 发送请求
                with urllib.request.urlopen(req, context=context) as response:
                    data = response.read().decode('utf-8')
                    result = json.loads(data)
                    
                    if result['code'] != 0:
                        print(f"API返回错误: {result['message']}")
                        break
                    
                    # 提取评论
                    replies = result.get('data', {}).get('replies', [])
                    if not replies:
                        print("没有更多评论了")
                        success = True
                        break
                    
                    # 处理每条评论
                    for reply in replies:
                        comment = {
                            '评论者': reply.get('member', {}).get('uname', '未知用户'),
                            '评论内容': reply.get('content', {}).get('message', '').replace('\n', ' '),
                            '评论时间': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reply.get('ctime', 0))),
                            '点赞数': reply.get('like', 0)
                        }
                        all_comments.append(comment)
                    
                    print(f"已爬取 {len(all_comments)} 条评论")
                    success = True
                    
                    # 检查是否还有下一页
                    if len(replies) < page_size:
                        print("已获取全部评论")
                        return all_comments, output_file
                    
                    # 增加游标
                    cursor += page_size
                    
                    # 添加延迟避免触发反爬
                    time.sleep(2)
                    
            except HTTPError as e:
                print(f"HTTP错误: {e.code}, 重试中... ({retry_count + 1}/{max_retries})")
                retry_count += 1
                time.sleep(5)
            except URLError as e:
                print(f"URL错误: {e.reason}, 重试中... ({retry_count + 1}/{max_retries})")
                retry_count += 1
                time.sleep(5)
            except Exception as e:
                print(f"未知错误: {str(e)}, 重试中... ({retry_count + 1}/{max_retries})")
                retry_count += 1
                time.sleep(5)
        
        # 如果重试次数用完，仍然失败，则终止
        if not success:
            print(f"达到最大重试次数，终止爬取")
            break
    
    # 保存到CSV文件
    if all_comments:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['评论者', '评论内容', '评论时间', '点赞数']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_comments)
        print(f"评论已保存到 {output_file}，共 {len(all_comments)} 条")
    else:
        print("未获取到任何评论")
    
    return all_comments, output_file

def get_aid_from_bvid(bvid):
    """
    将BV号转换为aid
    """
    # 简单实现，实际中可能需要从API获取
    # 这里使用一个备用方法，直接通过视频页面解析
    try:
        video_url = f"https://www.bilibili.com/video/{bvid}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(video_url, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            data = response.read().decode('utf-8')
            # 尝试从页面中提取aid
            import re
            aid_match = re.search(r'aid=(\d+)', data)
            if aid_match:
                return aid_match.group(1)
    except Exception as e:
        print(f"获取aid失败: {str(e)}")
    
    # 如果获取失败，返回一个默认值（可能需要手动设置）
    print("警告：无法自动获取aid，请手动设置")
    # 注意：这里可能需要根据实际情况修改为正确的aid
    return input("请输入视频的aid: ")

if __name__ == "__main__":
    # 请修改为你要爬取的视频BV号
    bvid = "BV1hkhizEETM"  # 替换为你的BV号
    output_file = "bilibili_comments.csv"
    
    comments, file = get_bilibili_comments(bvid, output_file)
    print(f"爬取完成！共获取 {len(comments)} 条评论")
