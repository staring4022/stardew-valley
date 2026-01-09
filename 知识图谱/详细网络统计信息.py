# 图3_网络统计信息.py
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from collections import Counter

def create_network_statistics():
    """创建详细的网络统计信息图"""
    G = nx.read_gexf("stardew_valley_network_typed.gexf")
    
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.axis('off')
    
    # 计算所有统计数据
    degrees = [d for _, d in G.degree()]
    type_counts = Counter([G.nodes[n].get('type','Unknown') for n in G.nodes()])
    
    # 构建详细的统计信息
    stats_lines = [
        "═" * 50,
        "📊 星露谷物语知识图谱 - 详细网络统计信息",
        "═" * 50,
        "",
        "📈 网络基本统计:",
        f"   总节点数: {G.number_of_nodes():>5} 个",
        f"   总边数:   {G.number_of_edges():>5} 条", 
        f"   网络密度:  {nx.density(G):.6f}",
        f"   平均连接数: {np.mean(degrees):.2f}",
        f"   最大连接数: {max(degrees):>5}",
        f"   最小连接数: {min(degrees):>5}",
        f"   网络直径:  {nx.diameter(G) if nx.is_connected(G) else '不连通':>5}",
        f"   连通性:    {'✅ 是' if nx.is_connected(G) else '❌ 否'}",
        "",
        "🎯 中心性分析统计:",
    ]
    
    # 中心性分析
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    
    stats_lines.append(f"   平均度中心性:   {np.mean(list(degree_centrality.values())):.4f}")
    stats_lines.append(f"   平均介数中心性: {np.mean(list(betweenness.values())):.4f}")
    
    stats_lines.extend([
        "",
        "🔢 节点类型详细统计:",
        "   ┌──────────────┬──────────┬──────────┐",
        "   │    类型      │  数量    │  占比    │",
        "   ├──────────────┼──────────┼──────────┤",
    ])
    
    total_nodes = G.number_of_nodes()
    for node_type, count in type_counts.most_common():
        percentage = (count / total_nodes) * 100
        stats_lines.append(f"   │ {node_type:12} │ {count:8} │ {percentage:7.1f}% │")
    
    stats_lines.append("   └──────────────┴──────────┴──────────┘")
    
    stats_lines.extend([
        "",
        "🔗 连接性分析:",
    ])
    
    # 连接性统计
    degree_dist = Counter(degrees)
    for degree, count in sorted(degree_dist.items())[:5]:
        stats_lines.append(f"   连接数为 {degree} 的节点: {count:4} 个")
    
    stats_lines.extend([
        "",
        "⚡ 网络拓扑特征:",
        f"   聚类系数: {nx.average_clustering(G):.4f}",
        f"   平均路径长度: {nx.average_shortest_path_length(G) if nx.is_connected(G) else 'N/A':.2f}",
    ])
    
    stats_text = "\n".join(stats_lines)
    
    # 显示文本
    ax.text(0.05, 0.95, stats_text, fontsize=12, 
            fontfamily='DejaVu Sans Mono',  # 等宽字体
            verticalalignment='top', linespacing=1.5,
            transform=ax.transAxes)
    
    ax.set_title('图3: 详细网络统计信息报告', fontsize=18, pad=20, loc='center')
    
    # 添加装饰性边框
    rect = plt.Rectangle((0.02, 0.02), 0.96, 0.96, 
                        linewidth=3, edgecolor='#4ECDC4', 
                        facecolor='none', alpha=0.8, linestyle='-')
    ax.add_patch(rect)
    
    plt.tight_layout()
    plt.savefig('图3_详细网络统计信息.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 图3已保存: 图3_详细网络统计信息.png")

create_network_statistics()
