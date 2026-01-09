# 创建交互式可视化.py
import plotly.graph_objects as go
import networkx as nx
import pandas as pd

# 读取GEXF文件
G = nx.read_gexf("stardew_valley_network_complete.gexf")

print(f"网络图: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")

# 创建交互式可视化
def create_interactive_network(G, output_file="stardew_valley_interactive.html"):
    # 使用力导向布局
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # 准备边数据
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # 准备节点数据
    node_x, node_y, node_text, node_colors, node_sizes = [], [], [], [], []
    color_map = {
        'NPC': '#FF6B6B',      # 红色
        'Quest': '#4ECDC4',    # 青色  
        'Item': '#FFD166',     # 黄色
        'Location': '#A5ABB6'  # 灰色
    }
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # 节点信息
        node_data = G.nodes[node]
        node_name = node_data.get('name', str(node))
        node_type = node_data.get('type', 'Unknown')
        degree = G.degree(node)
        
        node_text.append(f"<b>{node_name}</b><br>类型: {node_type}<br>连接数: {degree}")
        node_colors.append(color_map.get(node_type, '#CCCCCC'))
        node_sizes.append(max(10, min(30, degree * 2)))  # 根据连接数调整大小
    
    # 创建边轨迹
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # 创建节点轨迹
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            color=node_colors,
            size=node_sizes,
            line=dict(width=2, color='darkgray')
        )
    )
    
    # 创建图形
    fig = go.Figure(data=[edge_trace, node_trace],
                   layout=go.Layout(
                       title='<b>星露谷物语知识图谱</b>',
                       titlefont_size=16,
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=20,l=5,r=5,t=40),
                       annotations=[dict(
                           text="节点颜色: 红色=NPC, 青色=任务, 黄色=物品, 灰色=其他",
                           showarrow=False,
                           xref="paper", yref="paper",
                           x=0.005, y=-0.002
                       )],
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                   ))
    
    # 保存为HTML文件
    fig.write_html(output_file)
    print(f"交互式可视化已保存: {output_file}")
    return output_file

# 生成交互式可视化
create_interactive_network(G)
