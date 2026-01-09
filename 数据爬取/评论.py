import json
import csv

# 请将下面的file_path替换为您的实际文件路径
file_path = r"c:\Users\lenovo\xwechat_files\wxid_9u08d1b751bd22_7f96\msg\file\2025-11\stardew_reviews(1).json"
output_csv = "stardew_reviews.csv"

try:
    # 读取JSON文件
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 根据您提供的片段，假设数据结构可能是包含多个评论的列表
    # 或者可能需要调整下面的代码以匹配实际的数据结构
    reviews = []
    if isinstance(data, list):
        # 如果数据是评论列表
        for item in data:
            if 'review' in item:
                reviews.append(item['review'])
    elif isinstance(data, dict):
        # 如果数据是单个评论对象
        if 'review' in data:
            reviews.append(data['review'])
        # 或者检查是否有评论列表字段
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if 'review' in item:
                        reviews.append(item['review'])
    
    # 写入CSV文件
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 写入标题行
        writer.writerow(['评论ID', '评论内容'])
        # 写入评论数据
        for i, review in enumerate(reviews, 1):
            writer.writerow([i, review])
    
    print(f"成功提取了 {len(reviews)} 条评论并保存到 {output_csv} 文件中")
    
except Exception as e:
    print(f"处理文件时出错: {str(e)}")
    print("请确保文件路径正确，并且您有权限访问该文件")
