# 星露谷物语知识图谱分析_颜色修复版.py
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import glob
import json
import ast
from neo4j import GraphDatabase
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET


class StardewValleyAnalyzer:
    """星露谷物语知识图谱分析器"""
    
    # 颜色配置常量 - 使用更鲜明的颜色
    COLOR_SCHEME = {
        'NPC': {'color': '#FF6B6B', 'size': 25},      # 红色 - NPC角色
        'Quest': {'color': '#4ECDC4', 'size': 20},    # 青色 - 任务
        'Item': {'color': '#FFD166', 'size': 15},     # 黄色 - 物品
        'Location': {'color': '#A5ABB6', 'size': 18}, # 灰色 - 地点
        'Unknown': {'color': '#95A5A6', 'size': 12}   # 浅灰 - 未知类型
    }
    
    # 节点ID字段优先级
    ID_COLUMNS = ['id', 'entity_id', 'ID', 'Id']
    NAME_COLUMNS = ['name', 'entity_name', 'Name', 'label']
    TYPE_COLUMNS = ['type', 'Type', 'category', 'label']
    
    def __init__(self, export_dir: str = r"C:\Users\34167\exports"):
        self.export_dir = export_dir
        self.G = nx.Graph()
        self.name_to_id: Dict[str, str] = {}
        
    @staticmethod
    def parse_attribute_string(attr_str: str) -> Dict[str, Any]:
        """解析属性字符串为字典"""
        if pd.isna(attr_str) or not isinstance(attr_str, str):
            return {}
        
        try:
            # 尝试JSON解析
            try:
                cleaned = attr_str.replace("'", '"').replace("nan", "null")
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # 尝试Python字典解析
                try:
                    return ast.literal_eval(attr_str)
                except:
                    # 手动解析
                    result = {}
                    content = attr_str.strip('{}')
                    pairs = [pair.strip() for pair in content.split(',') if pair.strip()]
                    
                    for pair in pairs:
                        if ':' in pair:
                            key, val = pair.split(':', 1)
                            key = key.strip().strip('"').strip("'")
                            val = val.strip().strip('"').strip("'")
                            if val.lower() != 'nan' and val != '':
                                result[key] = val
                    return result
        except Exception as e:
            print(f"属性解析警告: {e}")
            return {}
    
    def query_neo4j_relationships(self) -> List[Dict[str, Any]]:
        """直接从Neo4j数据库查询关系数据"""
        print("=== 直接从Neo4j查询关系数据 ===")
        
        try:
            driver = GraphDatabase.driver(
                "bolt://localhost:7687", 
                auth=("neo4j", "606588ZXzx@")
            )
            
            query = """
            MATCH (a:Entity)-[r:REL]->(b:Entity)
            RETURN 
                a.id as source_id,
                a.name as source_name, 
                a.type as source_type,
                r.type as relation,
                b.id as target_id,
                b.name as target_name,
                b.type as target_type
            ORDER BY a.name, r.type
            """
            
            with driver.session() as session:
                result = session.run(query)
                relationships = []
                
                print("Neo4j中的实际关系:")
                print("-" * 80)
                
                for i, record in enumerate(result):
                    rel_data = {
                        'source_id': record['source_id'],
                        'source_name': record['source_name'],
                        'source_type': record['source_type'],
                        'relation': record['relation'],
                        'target_id': record['target_id'],
                        'target_name': record['target_name'],
                        'target_type': record['target_type']
                    }
                    relationships.append(rel_data)
                    
                    if i < 5:  # 只显示前5个关系
                        print(f"{i+1:2d}. {record['source_name']} ({record['source_type']})")
                        print(f"     --[{record['relation']}]--> {record['target_name']} ({record['target_type']})")
                
                print(f"总共找到 {len(relationships)} 个关系")
                return relationships
                
        except Exception as e:
            print(f"查询Neo4j失败: {e}")
            return []
    
    def export_corrected_relationships(self, relationships: List[Dict], output_file: str) -> pd.DataFrame:
        """导出修正后的关系CSV文件"""
        if not relationships:
            print("警告：没有关系数据可导出")
            return pd.DataFrame()
        
        df_data = []
        for rel in relationships:
            df_data.append({
                'source': rel['source_id'],
                'source_name': rel['source_name'],
                'source_type': rel['source_type'],
                'relation': rel['relation'],
                'target': rel['target_id'],
                'target_name': rel['target_name'],
                'target_type': rel['target_type']
            })
        
        df = pd.DataFrame(df_data)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"修正后的关系文件已保存: {output_file}")
        return df
    
    def find_latest_files(self) -> tuple[str, str]:
        """查找最新的数据文件"""
        node_files = glob.glob(os.path.join(self.export_dir, "stardew_valley_graph_*_nodes.csv"))
        
        if not node_files:
            raise FileNotFoundError(f"在 {self.export_dir} 目录中找不到节点CSV文件")
        
        latest_node_file = sorted(node_files)[-1]
        latest_relation_file = latest_node_file.replace("_nodes.csv", "_relations.csv")
        
        return latest_node_file, latest_relation_file
    
    def build_network(self) -> bool:
        """构建网络图"""
        try:
            # 查找文件
            node_file, relation_file = self.find_latest_files()
            print(f"使用节点文件: {node_file}")
            print(f"使用关系文件: {relation_file}")
            
            # 读取数据
            nodes_df = pd.read_csv(node_file)
            relations_df = pd.read_csv(relation_file)
            print(f"成功读取: {len(nodes_df)} 个节点, {len(relations_df)} 个关系")
            
            # 检查关系文件
            if not self._check_relations_valid(relations_df):
                print("关系文件无效，从Neo4j重新查询...")
                relationships = self.query_neo4j_relationships()
                if relationships:
                    corrected_file = relation_file.replace(".csv", "_corrected.csv")
                    relations_df = self.export_corrected_relationships(relationships, corrected_file)
                    relation_file = corrected_file
                else:
                    print("错误：无法获取有效的关系数据")
                    return False
            
            # 添加节点
            self._add_nodes(nodes_df)
            
            # 添加边
            self._add_edges(relations_df)
            
            return True
            
        except Exception as e:
            print(f"构建网络失败: {e}")
            return False
    
    def _check_relations_valid(self, relations_df: pd.DataFrame) -> bool:
        """检查关系文件是否有效"""
        if len(relations_df) == 0:
            return False
        
        # 检查是否有有效的source和target列
        has_valid_columns = any(col in relations_df.columns for col in ['source', 'target', 'source_id', 'target_id'])
        if not has_valid_columns:
            return False
        
        # 检查前几行数据
        sample_size = min(3, len(relations_df))
        for i in range(sample_size):
            row = relations_df.iloc[i]
            has_data = False
            for col in ['source', 'target', 'source_id', 'target_id']:
                if col in relations_df.columns and pd.notna(row[col]):
                    has_data = True
                    break
            if not has_data:
                return False
        
        return True
    
    def _add_nodes(self, nodes_df: pd.DataFrame) -> None:
        """添加节点到网络"""
        print("\n=== 添加节点 ===")
        
        for index, row in nodes_df.iterrows():
            attrs = self.parse_attribute_string(row.get('attributes', ''))
            
            # 确定节点ID
            node_id = self._extract_value(row, attrs, self.ID_COLUMNS, f"node_{index}")
            
            # 获取节点信息
            node_name = self._extract_value(row, attrs, self.NAME_COLUMNS, "")
            node_type = self._extract_value(row, attrs, self.TYPE_COLUMNS, "Unknown")
            
            # 添加节点
            self.G.add_node(node_id, name=node_name, type=node_type, attributes=attrs)
            if node_name:
                self.name_to_id[node_name] = node_id
            
            if index < 3:  # 显示前3个节点
                print(f"  添加节点: ID={node_id}, 名称={node_name}, 类型={node_type}")
        
        print(f"成功添加 {self.G.number_of_nodes()} 个节点")
    
    def _extract_value(self, row: pd.Series, attrs: Dict, columns: List[str], default: Any) -> Any:
        """从行数据或属性中提取值"""
        for col in columns:
            if col in row and pd.notna(row[col]):
                return str(row[col])
            elif col in attrs and attrs[col]:
                return str(attrs[col])
        return default
    
    def _add_edges(self, relations_df: pd.DataFrame) -> None:
        """添加边到网络"""
        print("\n=== 添加边关系 ===")
        edges_added = 0
        
        for index, row in relations_df.iterrows():
            source_id = self._find_node_id(row, 'source')
            target_id = self._find_node_id(row, 'target')
            
            if source_id and target_id and source_id in self.G and target_id in self.G:
                relation_type = self._extract_relation_type(row)
                
                if not self.G.has_edge(source_id, target_id):
                    self.G.add_edge(source_id, target_id, relation=relation_type)
                    edges_added += 1
                    
                    if edges_added <= 3:  # 显示前3条边
                        src_name = self.G.nodes[source_id].get('name', source_id)
                        tgt_name = self.G.nodes[target_id].get('name', target_id)
                        print(f"  添加边: {src_name} --[{relation_type}]--> {tgt_name}")
        
        print(f"成功添加 {edges_added} 条边")
        print(f"最终网络: {self.G.number_of_nodes()} 节点, {self.G.number_of_edges()} 边")
    
    def _find_node_id(self, row: pd.Series, prefix: str) -> Optional[str]:
        """查找节点ID"""
        # 尝试多种列名组合
        for col_suffix in ['', '_id', '_name']:
            col_name = f"{prefix}{col_suffix}"
            if col_name in row and pd.notna(row[col_name]):
                value = str(row[col_name])
                
                # 直接匹配节点ID
                if value in self.G:
                    return value
                
                # 通过名称映射
                if value in self.name_to_id:
                    return self.name_to_id[value]
        
        return None
    
    def _extract_relation_type(self, row: pd.Series) -> str:
        """提取关系类型"""
        for col in ['relation', 'relation_type', 'type']:
            if col in row and pd.notna(row[col]):
                return str(row[col])
        return "Unknown"
    
    def _add_color_attributes(self) -> None:
        """为节点添加Gephi兼容的颜色属性 - 修复版"""
        print("\n=== 添加颜色属性 ===")
        
        for node_id in self.G.nodes():
            node_type = self.G.nodes[node_id].get('type', 'Unknown')
            scheme = self.COLOR_SCHEME.get(node_type, self.COLOR_SCHEME['Unknown'])
            
            # 获取颜色值
            color_hex = scheme['color']
            
            # 转换为RGB整数
            r = int(color_hex[1:3], 16)  # 红色分量
            g = int(color_hex[3:5], 16)  # 绿色分量
            b = int(color_hex[5:7], 16)  # 蓝色分量
            
            # 方法1: 添加GEXF标准viz属性（Gephi首选）
            self.G.nodes[node_id]['viz'] = {
                'color': {
                    'r': r,
                    'g': g, 
                    'b': b,
                    'a': 1.0  # 透明度
                },
                'size': scheme['size']
            }
            
            # 方法2: 添加单独的颜色属性（兼容性）
            self.G.nodes[node_id]['color'] = color_hex
            self.G.nodes[node_id]['r'] = r
            self.G.nodes[node_id]['g'] = g
            self.G.nodes[node_id]['b'] = b
            self.G.nodes[node_id]['size'] = scheme['size']
            self.G.nodes[node_id]['node_type'] = node_type  # 添加明确的类型属性
            
        print(f"已为 {self.G.number_of_nodes()} 个节点添加颜色属性")
        
        # 显示颜色映射
        print("\n颜色映射:")
        for node_type, scheme in self.COLOR_SCHEME.items():
            print(f"  {node_type}: {scheme['color']} (大小: {scheme['size']})")
    
    def verify_color_attributes(self, output_file: str) -> None:
        """验证颜色属性是否正确设置"""
        print(f"\n=== 验证GEXF颜色属性 ===")
        print(f"检查文件: {output_file}")
        
        try:
            # 读取GEXF文件检查属性
            tree = ET.parse(output_file)
            root = tree.getroot()
            
            # 检查是否有viz属性
            namespaces = {'viz': 'http://www.gexf.net/1.2draft/viz'}
            nodes_with_color = 0
            nodes_without_color = 0
            
            print("检查前5个节点的颜色属性:")
            print("-" * 60)
            
            for i, node in enumerate(root.findall('.//node')):
                if i >= 5:  # 只检查前5个
                    break
                    
                node_id = node.get('id')
                viz_color = node.find('viz:color', namespaces)
                
                if viz_color is not None:
                    r = viz_color.get('r')
                    g = viz_color.get('g')
                    b = viz_color.get('b')
                    print(f"节点 {node_id}: 颜色 (r={r}, g={g}, b={b})")
                    nodes_with_color += 1
                else:
                    print(f"节点 {node_id}: 无viz颜色属性")
                    nodes_without_color += 1
            
            print(f"\n统计: {nodes_with_color} 个节点有颜色, {nodes_without_color} 个节点无颜色")
            
            # 检查属性
            print("\n检查节点属性:")
            for i, node in enumerate(root.findall('.//node')):
                if i >= 3:
                    break
                node_id = node.get('id')
                attrs = node.find('attvalues')
                if attrs is not None:
                    for attr in attrs.findall('attvalue'):
                        print(f"  属性: {attr.get('for')} = {attr.get('value')}")
            
        except Exception as e:
            print(f"验证颜色属性失败: {e}")
    
    def analyze_centrality(self) -> None:
        """进行中心性分析"""
        if self.G.number_of_edges() == 0:
            print("警告：网络中没有边，无法进行中心性分析！")
            self._show_node_info()
            return
        
        print("\n=== 中心性分析 ===")
        
        try:
            # 计算中心性指标
            degree_centrality = nx.degree_centrality(self.G)
            betweenness = nx.betweenness_centrality(self.G)
            print("中心性计算完成")
            
            # 获取重要节点排名
            top_nodes = sorted(degree_centrality.items(), 
                             key=lambda x: x[1], reverse=True)[:20]
            
            self._print_ranking(top_nodes, betweenness)
            self._print_statistics()
            self._save_network()
            
        except Exception as e:
            print(f"中心性分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _print_ranking(self, top_nodes: List[tuple], betweenness: Dict) -> None:
        """打印节点排名"""
        print("\n" + "="*80)
        print("核心游戏元素排名 (按度中心性):")
        print("="*80)
        
        for i, (node_id, centrality) in enumerate(top_nodes, 1):
            node_data = self.G.nodes[node_id]
            name = node_data.get('name', '未知名称')
            node_type = node_data.get('type', 'Unknown')
            degree = self.G.degree(node_id)
            betweenness_score = betweenness[node_id]
            
            print(f"{i:2d}. {name:<30} ({node_type:<10})")
            print(f"    度中心性: {centrality:.4f} | 连接数: {degree} | 介数中心性: {betweenness_score:.4f}")
            print(f"    节点ID: {node_id}")
            print()
        
        print("="*80)
    
    def _print_statistics(self) -> None:
        """打印统计信息"""
        print("\n=== 网络统计 ===")
        type_stats = {}
        
        for node_id in self.G.nodes():
            node_type = self.G.nodes[node_id].get('type', 'Unknown')
            if node_type not in type_stats:
                type_stats[node_type] = {'count': 0, 'total_degree': 0}
            type_stats[node_type]['count'] += 1
            type_stats[node_type]['total_degree'] += self.G.degree(node_id)
        
        print("按类型统计:")
        for node_type, stats in sorted(type_stats.items(), 
                                     key=lambda x: x[1]['count'], reverse=True):
            avg_degree = (stats['total_degree'] / stats['count'] 
                         if stats['count'] > 0 else 0)
            print(f"  {node_type:<15}: {stats['count']:3d} 节点, "
                  f"平均连接数: {avg_degree:.2f}")
    
    def _show_node_info(self) -> None:
        """显示节点信息"""
        print("\n节点信息 (前10个):")
        for i, node_id in enumerate(list(self.G.nodes())[:10]):
            node_data = self.G.nodes[node_id]
            name = node_data.get('name', '未知')
            node_type = node_data.get('type', 'Unknown')
            print(f"  {i+1}. {name} ({node_type}) - ID: {node_id}")
    
    def _save_network(self) -> None:
        """保存网络图"""
        try:
            # 添加颜色属性
            self._add_color_attributes()
            
            # 保存GEXF文件
            output_file = "stardew_valley_network_colored.gexf"
            nx.write_gexf(self.G, output_file)
            print(f"\n网络图已保存为: {output_file}")
            
            # 验证颜色属性
            self.verify_color_attributes(output_file)
            
            # 生成Gephi使用说明
            self._generate_gephi_instructions(output_file)
            
        except Exception as e:
            print(f"保存网络图失败: {e}")
    
    def _generate_gephi_instructions(self, gexf_file: str) -> None:
        """生成Gephi使用说明"""
        print("\n" + "="*80)
        print("Gephi 使用说明")
        print("="*80)
        print("""
1. 打开Gephi
2. 文件 → 打开 → 选择: {}
3. 在左侧面板选择"外观"选项卡
4. 点击"节点"子选项卡（圆形图标）
5. 选择"Partition"（分区）模式
6. 在下拉菜单中选择"type"属性
7. 点击"刷新"按钮查看类型列表
8. 为每种类型分配颜色：
   - NPC: 红色 (#FF6B6B)
   - Quest: 青色 (#4ECDC4) 
   - Item: 黄色 (#FFD166)
   - Location: 灰色 (#A5ABB6)
   - Unknown: 浅灰 (#95A5A6)
9. 点击"应用"按钮
10. 在"布局"面板选择"Force Atlas 2"
11. 点击"运行"进行布局
12. 在"预览"设置中调整外观
13. 导出高质量图片
        """.format(gexf_file))
        print("="*80)


def test_color_attributes():
    """测试颜色属性是否设置正确"""
    print("=== 测试颜色属性 ===")
    
    # 创建测试网络
    G = nx.Graph()
    
    # 添加测试节点
    test_nodes = [
        ('npc_1', {'name': '法师', 'type': 'NPC'}),
        ('quest_1', {'name': 'Meet The Wizard', 'type': 'Quest'}),
        ('item_1', {'name': '铁矿石', 'type': 'Item'}),
        ('loc_1', {'name': '矿洞', 'type': 'Location'}),
        ('unknown_1', {'name': '未知节点', 'type': 'Unknown'})
    ]
    
    for node_id, attrs in test_nodes:
        G.add_node(node_id, **attrs)
    
    # 添加颜色属性
    analyzer = StardewValleyAnalyzer()
    analyzer.G = G
    analyzer._add_color_attributes()
    
    # 检查属性
    for node_id in G.nodes():
        print(f"\n节点 {node_id}:")
        print(f"  名称: {G.nodes[node_id].get('name')}")
        print(f"  类型: {G.nodes[node_id].get('type')}")
        print(f"  颜色: {G.nodes[node_id].get('color')}")
        print(f"  viz属性: {G.nodes[node_id].get('viz', '无')}")
    
    # 保存测试文件
    test_file = "test_colored_network.gexf"
    nx.write_gexf(G, test_file)
    print(f"\n测试文件已保存: {test_file}")


def main():
    """主函数"""
    print("星露谷物语知识图谱分析 - 颜色修复版")
    print("="*50)
    
    # 先运行颜色测试
    test_color_attributes()
    
    print("\n" + "="*50)
    print("开始正式分析...")
    print("="*50)
    
    analyzer = StardewValleyAnalyzer()
    
    try:
        # 构建网络
        if analyzer.build_network():
            # 进行分析
            analyzer.analyze_centrality()
        else:
            print("网络构建失败，分析终止")
            
    except Exception as e:
        print(f"程序执行错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n分析完成！")


if __name__ == "__main__":
    main()