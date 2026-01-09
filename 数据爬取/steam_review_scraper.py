import requests
import pandas as pd
import time
import random
import json


def get_stardew_valley_reviews(max_reviews=500):
    """
    爬取《星露谷物语》的Steam评论
    """
    # 星露谷物语的Steam App ID
    appid = 413150

    # API地址
    url = f"https://store.steampowered.com/appreviews/{appid}"

    # 请求参数
    params = {
        'json': 1,
        'filter': 'all',  # 所有评论
        'language': 'all',  # 所有语言
        'day_range': 9223372036854775807,  # 所有时间
        'review_type': 'all',  # 推荐和不推荐都包括
        'purchase_type': 'all',  # 所有购买类型
        'num_per_page': 100  # 每页100条
    }

    reviews = []  # 存储所有评论
    cursor = '*'  # 分页游标，初始为*

    print("🚀 开始爬取《星露谷物语》Steam评论...")
    print("⏳ 请耐心等待，这可能需要几分钟...")

    page = 1
    while len(reviews) < max_reviews:
        print(f"📄 正在获取第 {page} 页数据...")

        # 设置当前页的游标
        params['cursor'] = cursor

        try:
            # 发送HTTP请求
            response = requests.get(url, params=params)

            # 检查请求是否成功
            if response.status_code != 200:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                break

            # 解析JSON数据
            data = response.json()

            # 检查API返回是否成功
            if data.get('success', 0) != 1:
                print("❌ API返回失败")
                break

            # 获取当前页的评论
            page_reviews = data.get('reviews', [])

            if not page_reviews:
                print("✅ 所有评论已获取完毕")
                break

            # 处理每条评论
            for review in page_reviews:
                review_data = {
                    'review_id': review.get('recommendationid', ''),
                    'steam_id': review.get('author', {}).get('steamid', ''),
                    'language': review.get('language', ''),
                    'review_content': review.get('review', ''),
                    'timestamp_created': review.get('timestamp_created', 0),
                    'timestamp_updated': review.get('timestamp_updated', 0),
                    'is_recommended': review.get('voted_up', False),
                    'helpful_count': review.get('votes_up', 0),
                    'funny_count': review.get('votes_funny', 0),
                    'weighted_score': review.get('weighted_vote_score', 0),
                    'comment_count': review.get('comment_count', 0),
                    'steam_purchase': review.get('steam_purchase', False),
                    'received_for_free': review.get('received_for_free', False),
                    'early_access_review': review.get('written_during_early_access', False),
                    'total_playtime': review.get('author', {}).get('playtime_forever', 0),
                    'playtime_last_two_weeks': review.get('author', {}).get('playtime_last_two_weeks', 0),
                    'playtime_at_review': review.get('author', {}).get('playtime_at_review', 0),
                    'last_played': review.get('author', {}).get('last_played', 0)
                }
                reviews.append(review_data)

            # 获取下一页的游标
            cursor = data.get('cursor', '')

            # 如果没有更多数据，退出循环
            if not cursor:
                print("✅ 已到达最后一页")
                break

            # 显示进度
            print(f"✅ 第 {page} 页完成，已获取 {len(reviews)} 条评论")

            # 随机延时，避免请求过快
            delay = random.uniform(2, 5)
            print(f"⏸️  等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)

            page += 1

        except Exception as e:
            print(f"❌ 发生错误: {e}")
            break

    print(f"🎉 爬取完成！共获取 {len(reviews)} 条评论")
    return reviews


def save_to_csv(reviews, filename='stardew_valley_reviews.csv'):
    """
    将评论数据保存为CSV文件
    """
    # 转换为DataFrame
    df = pd.DataFrame(reviews)

    # 转换时间戳为可读格式
    if 'timestamp_created' in df.columns:
        df['review_date'] = pd.to_datetime(df['timestamp_created'], unit='s')
    if 'last_played' in df.columns:
        df['last_played_date'] = pd.to_datetime(df['last_played'], unit='s')

    # 转换游戏时长为小时
    if 'total_playtime' in df.columns:
        df['total_playtime_hours'] = df['total_playtime'] / 60

    # 保存为CSV
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"💾 数据已保存到: {filename}")

    return df


def analyze_data(df):
    """
    简单分析数据
    """
    print("\n" + "=" * 50)
    print("📊 数据简要分析")
    print("=" * 50)

    print(f"总评论数: {len(df)}")
    print(f"推荐比例: {df['is_recommended'].mean():.2%}")
    print(f"平均游戏时长: {df['total_playtime_hours'].mean():.1f} 小时")
    print(f"免费获取比例: {df['received_for_free'].mean():.2%}")

    # 语言分布
    print(f"\n🌐 评论语言分布:")
    lang_counts = df['language'].value_counts().head(5)
    for lang, count in lang_counts.items():
        print(f"  {lang}: {count} 条 ({count / len(df):.1%})")

    # 游戏时长分布
    print(f"\n⏱️  游戏时长分布:")
    playtime_stats = df['total_playtime_hours'].describe()
    print(f"  最长: {playtime_stats['max']:.1f} 小时")
    print(f"  最短: {playtime_stats['min']:.1f} 小时")
    print(f"  中位数: {playtime_stats['50%']:.1f} 小时")


def preview_reviews(df, num=3):
    """
    预览几条评论内容
    """
    print(f"\n📝 前{num}条评论预览:")
    print("-" * 50)

    for i in range(min(num, len(df))):
        review = df.iloc[i]
        content_preview = review['review_content'][:100] + "..." if len(review['review_content']) > 100 else review[
            'review_content']

        print(f"\n评论 {i + 1}:")
        print(f"  推荐: {'✅' if review['is_recommended'] else '❌'}")
        print(f"  游戏时长: {review['total_playtime_hours']:.1f} 小时")
        print(f"  语言: {review['language']}")
        print(f"  内容: {content_preview}")


# 主程序
if __name__ == "__main__":
    print("=" * 60)
    print("🌟 《星露谷物语》Steam评论爬虫")
    print("=" * 60)

    # 获取评论数据
    reviews_data = get_stardew_valley_reviews(max_reviews=500)

    if reviews_data:
        # 保存数据
        df = save_to_csv(reviews_data)

        # 数据分析
        analyze_data(df)

        # 预览评论
        preview_reviews(df)

        print(f"\n🎯 数据已准备就绪，可用于后续的情感分析！")
    else:
        print("❌ 未能获取到数据，请检查网络连接或重试")