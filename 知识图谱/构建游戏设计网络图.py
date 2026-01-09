# 构建游戏设计网络图.py
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import glob
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

# 1. 找到最新的导出文件
export_dir = r"C:\Users\34167\exports"

# 查找最新的节点文件
node_files = glob.glob(os.path.join(export_dir, "stardew_valley_graph_*_nodes.csv"))
if not node_files:
    print(f"错误：在 {export_dir} 目录中找不到节点CSV文件")
    exit(1)

# 获取最新的文件
latest_node_file = sorted(node_files)[-1]
latest_relation_file = latest_node_file.replace("_nodes.csv", "_relations.csv")

print(f"使用节点文件: {latest_node_file}")
print(f"使用关系文件: {latest_relation_file}")

# 2. 读取数据
try:
    nodes_df = pd.read_csv(latest_node_file)
    relations_df = pd.read_csv(latest_relation_file)
    print(f"成功读取: {len(nodes_df)} 个节点, {len(relations_df)} 个关系")
except FileNotFoundError as e:
    print(f"读取文件失败: {e}")
    exit(1)

# 3. 构建网络图
G = nx.Graph()

# 添加节点
for _, row in nodes_df.iterrows():
    G.add_node(row.get('id', row.get('name')), 
               name=row.get('name', ''),
               type=row.get('type', 'Unknown'))

# 添加边
for _, row in relations_df.iterrows():
    G.add_edge(row['source'], row['target'], 
               relation=row.get('relation', 'Unknown'))

print(f"网络构建完成: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")

# 4. 导出函数定义
def export_static_visualization(G, filename):
    """导出静态网络图"""
    plt.figure(figsize=(20, 15))
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # 绘制网络
    nx.draw(G, pos, with_labels=True, node_size=200, 
            font_size=6, alpha=0.8, edge_color='gray')
    
    plt.title("星露谷物语知识图谱网络", size=16)
    plt.axis('off')
    plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"静态网络图已导出: {filename}.png")

def export_interactive_visualization(G, filename):
    """导出交互式HTML网络图"""
    try:
        import plotly.graph_objects as go
        
        # 如果节点太多，可以采样显示
        if G.number_of_nodes() > 500:
            print("节点过多，将采样显示前200个节点")
            nodes = list(G.nodes())[:200]
            H = G.subgraph(nodes)
        else:
            H = G
        
        pos = nx.spring_layout(H, k=1, iterations=50)
        
        # 准备边数据
        edge_x, edge_y = [], []
        for edge in H.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # 准备节点数据
        node_x, node_y, node_text = [], [], []
        for node in H.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_info = H.nodes[node]
            node_text.append(f"名称: {node_info.get('name', node)}<br>类型: {node_info.get('type', 'Unknown')}")
        
        # 创建图形
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                              line=dict(width=0.5, color='#888'),
                              hoverinfo='none', mode='lines')
        
        node_trace = go.Scatter(x=node_x, y=node_y,
                              mode='markers',
                              hoverinfo='text',
                              text=node_text,
                              marker=dict(size=10, line=dict(width=2)))
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(title='星露谷物语知识图谱',
                                      showlegend=False,
                                      hovermode='closest',
                                      margin=dict(b=20,l=5,r=5,t=40)))
        
        fig.write_html(f"{filename}.html")
        print(f"交互式网络图已导出: {filename}.html")
        
    except ImportError:
        print("警告: plotly 未安装，跳过交互式可视化")
        print("安装命令: pip install plotly")
    except Exception as e:
        print(f"交互式可视化导出失败: {e}")

def export_network_data(G, base_name):
    """导出网络数据文件"""
    try:
        # GEXF格式 (Gephi可读)
        nx.write_gexf(G, f"{base_name}.gexf")
        
        # GraphML格式
        nx.write_graphml(G, f"{base_name}.graphml")
        
        # 边列表
        nx.write_edgelist(G, f"{base_name}.edgelist")
        
        print(f"网络数据已导出: {base_name}.gexf, {base_name}.graphml, {base_name}.edgelist")
    except Exception as e:
        print(f"网络数据导出失败: {e}")

def export_analysis_report(G, filename):
    """导出网络分析报告"""
    try:
        report = {
            "network_statistics": {
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "density": nx.density(G),
                "is_connected": nx.is_connected(G.to_undirected()),
                "average_degree": sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
            }
        }
        
        with open(f"{filename}.json", "w", encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"分析报告已导出: {filename}.json")
    except Exception as e:
        print(f"分析报告导出失败: {e}")

def export_network_visualizations(G, base_name="stardew_valley"):
    """导出网络图的多种可视化格式"""
    print(f"\n开始导出网络可视化文件...")
    
    # 1. 静态图片导出
    export_static_visualization(G, f"{base_name}_network")
    
    # 2. 交互式HTML导出
    export_interactive_visualization(G, f"{base_name}_interactive")
    
    # 3. 数据格式导出
    export_network_data(G, base_name)
    
    # 4. 分析报告导出
    export_analysis_report(G, f"{base_name}_analysis")
    
    print(f"所有导出完成！")

# 5. 调用导出函数
if __name__ == "__main__":
    # 从文件名提取时间戳
    import re
    match = re.search(r'stardew_valley_graph_(\d+_\d+)', latest_node_file)
    if match:
        timestamp = match.group(1)
        base_name = f"stardew_valley_graph_{timestamp}"
    else:
        base_name = "stardew_valley_graph"
    
    # 执行所有导出
    export_network_visualizations(G, base_name)