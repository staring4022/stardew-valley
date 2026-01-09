# 图2_度分布与核心节点.py
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def create_degree_analysis():
    """创建度分布和核心节点分析"""
    G = nx.read_gexf("stardew_valley_network_typed.gexf")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # 左侧：度分布直方图
    degrees = [d for _, d in G.degree()]
    n, bins, patches = ax1.hist(degrees, bins=20, color='#4ECDC4', 
                               alpha=0.8, edgecolor='black', linewidth=1.2)
    avg_degree = np.mean(degrees)
    ax1.axvline(avg_degree, color='red', linestyle='--', linewidth=3,
               label=f'平均连接数: {avg_degree:.1f}')
    ax1.set_xlabel('连接数', fontsize=14)
    ax1.set_ylabel('节点数量', fontsize=14)
    ax1.set_title('度分布直方图', fontsize=16, pad=15)
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(labelsize=12)
    
    # 添加统计注释
    stats_text = f"""度分布统计:
总节点数: {len(degrees)}
平均连接数: {avg_degree:.2f}
最大连接数: {max(degrees)}
最小连接数: {min(degrees)}
连接数>5的节点: {sum(1 for d in degrees if d > 5)}个"""
    
    ax1.text(0.98, 0.95, stats_text, transform=ax1.transAxes,
            fontsize=11, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 右侧：核心节点排名
    degree_centrality = nx.degree_centrality(G)
    top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
    
    node_names = []
    centrality_scores = []
    for node_id, score in top_nodes:
        name = G.nodes[node_id].get('name', str(node_id))
        node_type = G.nodes[node_id].get('type', 'Unknown')
        # 格式化显示
        display_name = f"{name[:15]}\n({node_type})" if len(name) > 15 else f"{name}\n({node_type})"
        node_names.append(display_name)
        centrality_scores.append(score)
    
    y_pos = np.arange(len(node_names))
    bars = ax2.barh(y_pos, centrality_scores, color='#FF6B6B', alpha=0.8, height=0.7)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(node_names, fontsize=12)
    ax2.set_xlabel('度中心性', fontsize=14)
    ax2.set_title('核心节点排名 (前10)', fontsize=16, pad=15)
    ax2.invert_yaxis()
    ax2.tick_params(labelsize=12)
    ax2.grid(True, alpha=0.3, axis='x')
    
    # 在条形上添加数值
    for i, (bar, score) in enumerate(zip(bars, centrality_scores)):
        width = bar.get_width()
        ax2.text(width + 0.001, bar.get_y() + bar.get_height()/2,
                f'{score:.3f}', ha='left', va='center', fontsize=11,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.suptitle('图2: 网络连接分析与核心节点', fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('图2_度分布与核心节点.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 图2已保存: 图2_度分布与核心节点.png")

create_degree_analysis()
