import urllib.request
import json
import time
import csv
import ssl

# 忽略SSL证书验证（避免部分环境下的证书问题）
ssl._create_default_https_context = ssl._create_unverified_context

# 视频的BV号或AV号
video_id = "BV1hkhizEETM"  # 请替换为您想要爬取的视频BV号

# 输出文件
output_csv = "bilibili_comments.csv"

def get_comments(video_id):
    # B站API的基本URL
    url = f"https://api.bilibili.com/x/v2/reply?type=1&oid={video_id}&pn={{}}&ps=20&sort=2"
    
    comments = []
    page = 1
    
    print(f"开始爬取视频 {video_id} 的评论...")
    
    while True:
        try:
            # 发送请求（使用标准库urllib.request）
            req = urllib.request.Request(url.format(page), headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8')
                data = json.loads(data)
            
            # 检查请求是否成功
            if data.get('code') != 0:
                print(f"请求出错: {data.get('message')}")
                break
            
            # 获取评论数据
            replies = data.get('data', {}).get('replies', [])
            
            # 如果没有更多评论，结束循环
            if not replies:
                break
            
            # 提取评论内容
            for reply in replies:
                comment = {
                    'user_name': reply.get('member', {}).get('uname', ''),
                    'comment_text': reply.get('content', {}).get('message', ''),
                    'like_count': reply.get('like', 0),
                    'publish_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reply.get('ctime', 0)))
                }
                comments.append(comment)
                
                # 检查是否有回复
                if reply.get('replies'):
                    for sub_reply in reply.get('replies'):
                        sub_comment = {
                            'user_name': sub_reply.get('member', {}).get('uname', ''),
                            'comment_text': sub_reply.get('content', {}).get('message', ''),
                            'like_count': sub_reply.get('like', 0),
                            'publish_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sub_reply.get('ctime', 0)))
                        }
                        comments.append(sub_comment)
            
            print(f"已爬取第 {page} 页，共 {len(comments)} 条评论")
            page += 1
            
            # 添加延时，避免被反爬
            time.sleep(2)
            
        except Exception as e:
            print(f"爬取第 {page} 页时出错: {str(e)}")
            # 出错时重试
            time.sleep(5)
    
    return comments

def save_to_csv(comments, output_file):
    if not comments:
        print("没有评论数据可以保存")
        return
    
    # 获取字段名
    fieldnames = comments[0].keys()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comments)
    
    print(f"成功保存 {len(comments)} 条评论到 {output_file}")

if __name__ == "__main__":
    # 直接运行，不需要安装任何依赖
    comments = get_comments(video_id)
    
    # 保存到CSV
    if comments:
        save_to_csv(comments, output_csv)
        print("评论爬取完成！")
