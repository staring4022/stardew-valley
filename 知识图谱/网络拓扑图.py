# 图1_网络拓扑图.py
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter

def create_network_topology():
    """创建清晰的大尺寸网络拓扑图"""
    G = nx.read_gexf("stardew_valley_network_typed.gexf")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # 左侧：网络拓扑图
    color_map = {'NPC':'#FF6B6B', 'Quest':'#4ECDC4', 'Item':'#FFD166', 
                'Location':'#A5ABB6', 'Unknown':'#95A5A6'}
    pos = nx.spring_layout(G, k=1, iterations=50, seed=42)
    node_colors = [color_map.get(G.nodes[n].get('type','Unknown'), '#95A5A6') for n in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, ax=ax1, node_color=node_colors, 
                          node_size=80, alpha=0.8)
    nx.draw_networkx_edges(G, pos, ax=ax1, edge_color='gray', 
                          alpha=0.3, width=0.8)
    ax1.set_title(f'星露谷物语知识图谱网络拓扑\n{G.number_of_nodes()}节点, {G.number_of_edges()}边', 
                 fontsize=16, pad=15)
    ax1.axis('off')
    
    # 右侧：类型分布饼图
    type_counts = Counter([G.nodes[n].get('type','Unknown') for n in G.nodes()])
    labels = list(type_counts.keys())
    sizes = list(type_counts.values())
    colors = [color_map.get(label, '#95A5A6') for label in labels]
    
    wedges, texts, autotexts = ax2.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                      colors=colors, startangle=90, 
                                      textprops={'fontsize': 12})
    ax2.set_title('节点类型分布', fontsize=16, pad=15)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    plt.suptitle('图1: 网络结构与类型分布', fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('图1_网络拓扑与类型分布.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 图1已保存: 图1_网络拓扑与类型分布.png")

create_network_topology()
