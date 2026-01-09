# 图4_设计优化建议.py
import matplotlib.pyplot as plt
import networkx as nx
from collections import Counter

def create_design_recommendations():
    """创建设计优化建议图"""
    G = nx.read_gexf("stardew_valley_network_typed.gexf")
    type_counts = Counter([G.nodes[n].get('type','Unknown') for n in G.nodes()])
    
    fig, ax = plt.subplots(figsize=(16, 12))
    ax.axis('off')
    
    # 构建详细的设计建议
    recommendations = [
        "═" * 50,
        "💡 星露谷物语知识图谱 - 设计优化建议报告",
        "═" * 50,
        "",
        "🎯 当前状态分析:",
        f"   总游戏元素: {G.number_of_nodes()} 个",
        f"   元素间关系: {G.number_of_edges()} 条",
        "",
        "✅ 设计优势分析:",
        "   1. 网络结构清晰，复杂度适中",
        "   2. 核心任务机制明确突出", 
        "   3. 整体规模合理，不过度臃肿",
        "   4. 类型分布符合RPG游戏特征",
        "",
        "⚠️ 需改进的问题:",
    ]
    
    # 添加具体问题
    total_nodes = G.number_of_nodes()
    
    # NPC分析
    npc_count = type_counts.get('NPC', 0)
    npc_percent = (npc_count / total_nodes) * 100
    recommendations.append(f"   1. NPC角色偏少 ({npc_count}个, {npc_percent:.1f}%)")
    
    # 物品分析
    item_count = type_counts.get('Item', 0)
    item_percent = (item_count / total_nodes) * 100
    recommendations.append(f"   2. 物品系统简单 ({item_count}个, {item_percent:.1f}%)")
    
    # 地点分析
    location_count = type_counts.get('Location', 0)
    location_percent = (location_count / total_nodes) * 100
    recommendations.append(f"   3. 游戏地点有限 ({location_count}个, {location_percent:.1f}%)")
    
    # 未知节点
    unknown_count = type_counts.get('Unknown', 0)
    unknown_percent = (unknown_count / total_nodes) * 100
    recommendations.append(f"   4. 未知节点较多 ({unknown_count}个, {unknown_percent:.1f}%)")
    
    # 连接性分析
    degrees = [d for _, d in G.degree()]
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    recommendations.append(f"   5. 平均连接数偏低 ({avg_degree:.1f}/3-5理想范围)")
    
    recommendations.extend([
        "",
        "🔧 具体优化建议:",
        "",
        "📈 内容扩展建议:",
        "   1. 新增5-8个NPC角色，丰富社交系统",
        "   2. 增加10-15种新物品，扩展收集要素",
        "   3. 添加3-5个新场景，丰富游戏世界",
        "   4. 为44个未知节点完善类型标注",
        "",
        "🔄 连接优化建议:",
        "   5. 增加次要任务间的关联性",
        "   6. 优化物品获取的依赖关系", 
        "   7. 增强NPC与场景的互动连接",
        "   8. 平衡核心与边缘节点连接数",
        "",
        "🎮 玩法设计建议:",
        "   9. 利用中心节点设计主线任务",
        "   10. 基于社区结构设计支线任务链",
        "   11. 按类型分布设计难度梯度",
        "   12. 优化玩家体验路径规划",
        "",
        "📊 实施优先级:",
        "   🔴 高: 完善类型标注、增加NPC",
        "   🟡 中: 扩展物品系统、优化连接",
        "   🟢 低: 微调平衡性、界面优化",
    ])
    
    rec_text = "\n".join(recommendations)
    
    # 显示文本
    ax.text(0.05, 0.95, rec_text, fontsize=12, 
            fontfamily='DejaVu Sans Mono',
            verticalalignment='top', linespacing=1.5,
            transform=ax.transAxes)
    
    ax.set_title('图4: 设计优化与实施建议报告', fontsize=18, pad=20, loc='center')
    
    # 添加装饰性边框
    rect = plt.Rectangle((0.02, 0.02), 0.96, 0.96, 
                        linewidth=3, edgecolor='#FF6B6B', 
                        facecolor='none', alpha=0.8, linestyle='-')
    ax.add_patch(rect)
    
    plt.tight_layout()
    plt.savefig('图4_设计优化建议.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("✅ 图4已保存: 图4_设计优化建议.png")

create_design_recommendations()
