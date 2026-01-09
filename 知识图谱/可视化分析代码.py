# 在可视化分析代码.py开头添加
GEXF_FILE = r"C:\Users\34167\exports\stardew_valley_network_complete.gexf"
# 游戏设计结构可视化分析.py
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import community as community_louvain
from collections import Counter
import os

class GameDesignVisualizer:
    """游戏设计结构可视化分析器"""
    
    def __init__(self, gexf_file="stardew_valley_network_complete.gexf"):
        self.gexf_file = gexf_file
        self.G = None
        self.analysis_results = {}
        
    def load_network(self):
        """加载网络数据"""
        try:
            self.G = nx.read_gexf(self.gexf_file)
            print(f"✓ 成功加载网络: {self.G.number_of_nodes()}节点, {self.G.number_of_edges()}边")
            return True
        except Exception as e:
            print(f"加载网络失败: {e}")
            return False
    
    def analyze_network(self):
        """执行网络分析"""
        if self.G is None:
            return False
            
        # 基础统计
        self.analysis_results['basic_stats'] = {
            'node_count': self.G.number_of_nodes(),
            'edge_count': self.G.number_of_edges(),
            'density': nx.density(self.G),
            'is_connected': nx.is_connected(self.G)
        }
        
        # 中心性分析
        self.analysis_results['degree_centrality'] = nx.degree_centrality(self.G)
        self.analysis_results['betweenness'] = nx.betweenness_centrality(self.G)
        self.analysis_results['closeness'] = nx.closeness_centrality(self.G)
        
        # 社区检测
        G_undirected = self.G.to_undirected()
        partition = community_louvain.best_partition(G_undirected)
        self.analysis_results['communities'] = partition
        self.analysis_results['modularity'] = community_louvain.modularity(partition, G_undirected)
        
        # 节点类型分析
        node_types = [self.G.nodes[node].get('type', 'Unknown') for node in self.G.nodes()]
        self.analysis_results['type_distribution'] = Counter(node_types)
        
        return True
    
    def create_interactive_dashboard(self):
        """创建交互式仪表板"""
        if not self.analysis_results:
            return
        
        # 创建子图布局
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('网络拓扑图', '节点类型分布', '中心性分布', '社区结构'),
            specs=[[{"type": "scatter"}, {"type": "pie"}],
                   [{"type": "histogram"}, {"type": "scatter"}]]
        )
        
        # 1. 网络拓扑图
        self._add_network_plot(fig, row=1, col=1)
        
        # 2. 节点类型分布
        self._add_type_pie_chart(fig, row=1, col=2)
        
        # 3. 中心性分布
        self._add_centrality_histogram(fig, row=2, col=1)
        
        # 4. 社区结构
        self._add_community_plot(fig, row=2, col=2)
        
        fig.update_layout(
            title_text="星露谷物语知识图谱设计分析仪表板",
            height=800,
            showlegend=False
        )
        
        # 保存交互式HTML
        fig.write_html("game_design_dashboard.html")
        print("✓ 交互式仪表板已保存: game_design_dashboard.html")
        
    def _add_network_plot(self, fig, row, col):
        """添加网络拓扑图"""
        # 使用力导向布局
        pos = nx.spring_layout(self.G, k=1, iterations=50)
        
        # 准备节点数据
        node_x, node_y, node_text, node_colors = [], [], [], []
        color_map = {
            'NPC': '#FF6B6B', 'Quest': '#4ECDC4', 
            'Item': '#FFD166', 'Location': '#A5ABB6', 'Unknown': '#95A5A6'
        }
        
        for node in self.G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            node_data = self.G.nodes[node]
            name = node_data.get('name', str(node))
            node_type = node_data.get('type', 'Unknown')
            degree = self.G.degree(node)
            
            node_text.append(f"{name}<br>类型: {node_type}<br>连接数: {degree}")
            node_colors.append(color_map.get(node_type, '#95A5A6'))
        
        # 添加节点轨迹
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            marker=dict(size=10, color=node_colors, line=dict(width=2)),
            text=node_text,
            hoverinfo='text',
            name='节点'
        ), row=row, col=col)
        
        # 添加边
        edge_x, edge_y = [], []
        for edge in self.G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            showlegend=False
        ), row=row, col=col)
    
    def _add_type_pie_chart(self, fig, row, col):
        """添加节点类型饼图"""
        type_dist = self.analysis_results['type_distribution']
        labels = list(type_dist.keys())
        values = list(type_dist.values())
        
        colors = ['#FF6B6B', '#4ECDC4', '#FFD166', '#A5ABB6', '#95A5A6']
        
        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hoverinfo='label+percent+value',
            textinfo='percent+label'
        ), row=row, col=col)
    
    def _add_centrality_histogram(self, fig, row, col):
        """添加中心性分布直方图"""
        degree_centrality = list(self.analysis_results['degree_centrality'].values())
        
        fig.add_trace(go.Histogram(
            x=degree_centrality,
            nbinsx=20,
            marker_color='#4ECDC4',
            opacity=0.7,
            name='度中心性'
        ), row=row, col=col)
        
        fig.update_xaxes(title_text="度中心性", row=row, col=col)
        fig.update_yaxes(title_text="节点数量", row=row, col=col)
    
    def _add_community_plot(self, fig, row, col):
        """添加社区结构图"""
        communities = self.analysis_results['communities']
        community_sizes = Counter(communities.values())
        
        fig.add_trace(go.Bar(
            x=list(community_sizes.keys()),
            y=list(community_sizes.values()),
            marker_color='#FF6B6B',
            name='社区规模'
        ), row=row, col=col)
        
        fig.update_xaxes(title_text="社区ID", row=row, col=col)
        fig.update_yaxes(title_text="节点数量", row=row, col=col)
    
    def create_static_report(self):
        """生成静态分析报告"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('星露谷物语知识图谱设计分析报告', fontsize=16, fontweight='bold')
        
        # 1. 网络拓扑图
        self._plot_network_topology(axes[0, 0])
        
        # 2. 节点类型分布
        self._plot_type_distribution(axes[0, 1])
        
        # 3. 度分布
        self._plot_degree_distribution(axes[0, 2])
        
        # 4. 中心性分析
        self._plot_centrality_analysis(axes[1, 0])
        
        # 5. 社区结构
        self._plot_community_structure(axes[1, 1])
        
        # 6. 设计建议
        self._plot_design_recommendations(axes[1, 2])
        
        plt.tight_layout()
        plt.savefig('game_design_analysis_report.png', dpi=300, bbox_inches='tight')
        plt.show()
        print("✓ 静态分析报告已保存: game_design_analysis_report.png")
    
    def _plot_network_topology(self, ax):
        """绘制网络拓扑图"""
        pos = nx.spring_layout(self.G, k=1, iterations=50)
        
        # 按类型着色
        node_colors = []
        color_map = {
            'NPC': '#FF6B6B', 'Quest': '#4ECDC4', 
            'Item': '#FFD166', 'Location': '#A5ABB6', 'Unknown': '#95A5A6'
        }
        
        for node in self.G.nodes():
            node_type = self.G.nodes[node].get('type', 'Unknown')
            node_colors.append(color_map.get(node_type, '#95A5A6'))
        
        nx.draw(self.G, pos, ax=ax, node_color=node_colors, 
                node_size=50, edge_color='gray', alpha=0.7, 
                with_labels=False, linewidths=0.5)
        
        ax.set_title(f'网络拓扑图\n{self.G.number_of_nodes()}节点, {self.G.number_of_edges()}边')
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [Patch(color=color, label=label) 
                          for label, color in color_map.items()]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    def _plot_type_distribution(self, ax):
        """绘制节点类型分布"""
        type_dist = self.analysis_results['type_distribution']
        labels = list(type_dist.keys())
        sizes = list(type_dist.values())
        colors = ['#FF6B6B', '#4ECDC4', '#FFD166', '#A5ABB6', '#95A5A6']
        
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('节点类型分布')
        ax.axis('equal')
    
    def _plot_degree_distribution(self, ax):
        """绘制度分布"""
        degrees = [d for n, d in self.G.degree()]
        ax.hist(degrees, bins=20, alpha=0.7, color='#4ECDC4', edgecolor='black')
        ax.set_xlabel('连接数')
        ax.set_ylabel('节点数量')
        ax.set_title('度分布直方图')
        ax.grid(True, alpha=0.3)
        
        # 添加统计信息
        avg_degree = np.mean(degrees)
        ax.axvline(avg_degree, color='red', linestyle='--', label=f'平均: {avg_degree:.2f}')
        ax.legend()
    
    def _plot_centrality_analysis(self, ax):
        """绘制中心性分析"""
        top_nodes = sorted(self.analysis_results['degree_centrality'].items(), 
                          key=lambda x: x[1], reverse=True)[:10]
        
        names = []
        scores = []
        for node_id, score in top_nodes:
            name = self.G.nodes[node_id].get('name', str(node_id))
            names.append(name[:20] + '...' if len(name) > 20 else name)
            scores.append(score)
        
        y_pos = np.arange(len(names))
        ax.barh(y_pos, scores, color='#FF6B6B', alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.set_xlabel('度中心性')
        ax.set_title('核心节点排名')
        ax.invert_yaxis()
    
    def _plot_community_structure(self, ax):
        """绘制社区结构"""
        communities = self.analysis_results['communities']
        community_sizes = Counter(communities.values())
        
        communities_sorted = sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)[:10]
        comm_ids = [f'社区 {i}' for i, _ in communities_sorted]
        sizes = [size for _, size in communities_sorted]
        
        ax.bar(comm_ids, sizes, color='#FFD166', alpha=0.7)
        ax.set_xlabel('社区')
        ax.set_ylabel('节点数量')
        ax.set_title(f'社区结构 (模块度: {self.analysis_results["modularity"]:.3f})')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _plot_design_recommendations(self, ax):
        """绘制设计建议"""
        ax.axis('off')
        
        recommendations = self._generate_design_recommendations()
        
        text_content = "设计建议分析:\n\n"
        for i, rec in enumerate(recommendations, 1):
            text_content += f"{i}. {rec}\n"
        
        ax.text(0.1, 0.9, text_content, transform=ax.transAxes, 
                fontsize=10, verticalalignment='top', linespacing=1.5)
        ax.set_title('游戏设计建议', fontweight='bold')
    
    def _generate_design_recommendations(self):
        """生成设计建议"""
        recommendations = []
        
        stats = self.analysis_results['basic_stats']
        type_dist = self.analysis_results['type_distribution']
        modularity = self.analysis_results['modularity']
        
        # 网络复杂度分析
        density = stats['density']
        if density < 0.01:
            recommendations.append("网络密度较低，可增加任务关联性")
        elif density > 0.1:
            recommendations.append("网络密度较高，可简化部分连接")
        else:
            recommendations.append("网络密度适中，结构良好")
        
        # 类型平衡分析
        main_types = {k: v for k, v in type_dist.items() if v > 5}
        if len(main_types) >= 3:
            recommendations.append("游戏元素类型分布均衡")
        else:
            recommendations.append("建议增加更多游戏元素类型")
        
        # 模块化分析
        if modularity > 0.5:
            recommendations.append("模块化程度高，游戏结构清晰")
        elif modularity > 0.3:
            recommendations.append("模块化程度适中")
        else:
            recommendations.append("模块化程度较低，可优化功能分区")
        
        # 连接性建议
        avg_degree = sum(dict(self.G.degree()).values()) / stats['node_count']
        if 3 <= avg_degree <= 5:
            recommendations.append("平均连接数理想，游戏节奏良好")
        elif avg_degree < 3:
            recommendations.append("连接较少，可增加互动元素")
        else:
            recommendations.append("连接较多，可简化复杂度")
        
        return recommendations
    
    def generate_text_report(self):
        """生成文本分析报告"""
        report = []
        
        stats = self.analysis_results['basic_stats']
        type_dist = self.analysis_results['type_distribution']
        modularity = self.analysis_results['modularity']
        
        report.append("="*60)
        report.append("星露谷物语知识图谱设计分析报告")
        report.append("="*60)
        report.append(f"网络规模: {stats['node_count']} 节点, {stats['edge_count']} 边")
        report.append(f"网络密度: {stats['density']:.4f}")
        report.append(f"模块化程度: {modularity:.3f}")
        report.append(f"连通性: {'是' if stats['is_connected'] else '否'}")
        
        report.append("\n节点类型分布:")
        for type_name, count in type_dist.most_common():
            report.append(f"  {type_name}: {count} 节点")
        
        # 核心节点分析
        top_nodes = sorted(self.analysis_results['degree_centrality'].items(), 
                          key=lambda x: x[1], reverse=True)[:5]
        report.append("\n核心游戏机制 (按中心性排名):")
        for i, (node_id, centrality) in enumerate(top_nodes, 1):
            name = self.G.nodes[node_id].get('name', str(node_id))
            node_type = self.G.nodes[node_id].get('type', 'Unknown')
            report.append(f"  {i}. {name} ({node_type}): {centrality:.4f}")
        
        # 设计建议
        recommendations = self._generate_design_recommendations()
        report.append("\n设计建议:")
        for i, rec in enumerate(recommendations, 1):
            report.append(f"  {i}. {rec}")
        
        report.append("="*60)
        
        # 保存报告
        with open('game_design_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print("✓ 文本分析报告已保存: game_design_analysis_report.txt")
        print('\n'.join(report))
    
    def run_complete_analysis(self):
        """运行完整分析"""
        print("开始游戏设计结构可视化分析...")
        
        if not self.load_network():
            return False
        
        if not self.analyze_network():
            return False
        
        # 生成所有可视化
        self.create_interactive_dashboard()
        self.create_static_report()
        self.generate_text_report()
        
        print("分析完成！")
        return True


def main():
    """主函数"""
    # 查找可用的GEXF文件
    possible_files = [
        "stardew_valley_network_complete.gexf",
        "stardew_valley_network_optimized.gexf", 
        "stardew_valley_network_colored.gexf",
        "stardew_valley_network.gexf"
    ]
    
    for file in possible_files:
        if os.path.exists(file):
            print(f"使用网络文件: {file}")
            visualizer = GameDesignVisualizer(file)
            visualizer.run_complete_analysis()
            break
    else:
        print("错误：找不到任何GEXF网络文件")
        print("请先运行网络构建脚本生成GEXF文件")


if __name__ == "__main__":
    main()
