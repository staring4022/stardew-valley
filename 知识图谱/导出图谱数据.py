#!/usr/bin/env python3
"""
星露谷物语知识图谱数据导出脚本
"""

import pandas as pd
import json
import argparse
from neo4j import GraphDatabase
from datetime import datetime
import os

class StardewValleyExporter:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.export_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def export_complete_dataset(self, output_dir="."):
        """导出完整数据集"""
        print("开始导出星露谷物语知识图谱数据...")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 基础数据导出
        nodes_df, relations_df = self.export_basic_data()
        
        # 高级分析数据导出
        advanced_data = self.export_advanced_data()
        
        # 生成文件名
        base_name = f"{output_dir}/stardew_valley_graph_{self.export_time}"
        
        # 导出各种格式
        self.export_formats(nodes_df, relations_df, base_name)
        self.export_advanced_formats(advanced_data, base_name)
        
        # 生成报告
        report = self.generate_report(nodes_df, relations_df, advanced_data)
        
        print(f"导出完成！文件保存在: {base_name}_*")
        return report
    
    def export_basic_data(self):
        """导出基础节点和关系数据"""
        with self.driver.session() as session:
            # 节点数据 - 修正后的查询（移除Cypher语句中的Python注释）
            nodes_result = session.run("""
                MATCH (n:Entity)
                RETURN n.id as id, n.name as name, n.type as type,
                       COUNT{ (n)--() } as degree,
                       properties(n) as attributes
            """)
            nodes_data = [dict(record) for record in nodes_result]
            nodes_df = pd.DataFrame(nodes_data)
            
            # 关系数据
            relations_result = session.run("""
                MATCH (a:Entity)-[r:REL]->(b:Entity)
                RETURN a.id as source, b.id as target, r.type as relation,
                       properties(r) as rel_attributes
            """)
            relations_data = [dict(record) for record in relations_result]
            relations_df = pd.DataFrame(relations_data)
            
        return nodes_df, relations_df
    
    def export_advanced_data(self):
        """导出高级分析数据"""
        queries = {
            'centrality': """
                MATCH (n:Entity)
                WITH n, COUNT{ (n)--() } as degree
                RETURN n.id as node_id, n.name as node_name, degree
                ORDER BY degree DESC
            """,
            'triangles': """
                MATCH (a:Entity)-[:REL]->(b:Entity)-[:REL]->(c:Entity)-[:REL]->(a:Entity)
                WHERE a <> b AND b <> c AND a <> c
                RETURN a.name as a, b.name as b, c.name as c
                LIMIT 500
            """,
            'long_chains': """
                MATCH path = (start:Entity)-[:REL*3..5]->(end:Entity)
                WHERE start.type = 'NPC' AND end.type = 'Item'
                RETURN [n in nodes(path) | n.name] as chain,
                       length(path) as chain_length
                ORDER BY chain_length DESC
                LIMIT 200
            """,
            'community_detection': """
                MATCH (a:Entity)-[:REL]-(b:Entity)
                WITH a, b, COUNT{ (a)-[:REL]-(b) } as weight
                RETURN a.id as source_id, a.name as source_name, 
                       b.id as target_id, b.name as target_name, weight
                LIMIT 1000
            """
        }
        
        advanced_data = {}
        with self.driver.session() as session:
            for key, query in queries.items():
                try:
                    result = session.run(query)
                    advanced_data[key] = [dict(record) for record in result]
                except Exception as e:
                    print(f"警告: 查询 {key} 执行失败: {e}")
                    advanced_data[key] = []
        
        return advanced_data
    
    def export_formats(self, nodes_df, relations_df, base_name):
        """导出为多种格式"""
        try:
            # CSV格式
            nodes_df.to_csv(f"{base_name}_nodes.csv", index=False, encoding='utf-8-sig')
            relations_df.to_csv(f"{base_name}_relations.csv", index=False, encoding='utf-8-sig')
            
            # JSON格式
            nodes_df.to_json(f"{base_name}_nodes.json", orient='records', indent=2, force_ascii=False)
            relations_df.to_json(f"{base_name}_relations.json", orient='records', indent=2, force_ascii=False)
            
            # Excel格式
            with pd.ExcelWriter(f"{base_name}_full_data.xlsx", engine='openpyxl') as writer:
                nodes_df.to_excel(writer, sheet_name='节点数据', index=False)
                relations_df.to_excel(writer, sheet_name='关系数据', index=False)
                
        except Exception as e:
            print(f"导出文件时出错: {e}")
    
    def export_advanced_formats(self, advanced_data, base_name):
        """导出高级数据格式"""
        for key, data in advanced_data.items():
            try:
                if data:  # 确保数据不为空
                    df = pd.DataFrame(data)
                    df.to_csv(f"{base_name}_{key}.csv", index=False, encoding='utf-8-sig')
                    df.to_json(f"{base_name}_{key}.json", orient='records', indent=2, force_ascii=False)
            except Exception as e:
                print(f"导出高级数据 {key} 时出错: {e}")
    
    def generate_report(self, nodes_df, relations_df, advanced_data):
        """生成导出报告"""
        try:
            # 计算基本统计
            total_nodes = len(nodes_df)
            total_relationships = len(relations_df)
            
            # 节点类型分布
            if 'type' in nodes_df.columns:
                node_types = nodes_df['type'].value_counts().to_dict()
            else:
                node_types = {"Unknown": total_nodes}
            
            # 关系类型分布
            if 'relation' in relations_df.columns:
                relationship_types = relations_df['relation'].value_counts().to_dict()
            else:
                relationship_types = {"Unknown": total_relationships}
            
            # 计算节点连接数统计
            if 'degree' in nodes_df.columns:
                avg_degree = nodes_df['degree'].mean()
                max_degree = nodes_df['degree'].max()
                min_degree = nodes_df['degree'].min()
            else:
                avg_degree = max_degree = min_degree = 0
            
            report = {
                'export_time': self.export_time,
                'summary': {
                    'total_nodes': int(total_nodes),
                    'total_relationships': int(total_relationships),
                    'node_types_distribution': node_types,
                    'relationship_types': relationship_types,
                    'degree_statistics': {
                        'average': float(avg_degree),
                        'maximum': float(max_degree),
                        'minimum': float(min_degree)
                    }
                },
                'top_connected_nodes': nodes_df.nlargest(10, 'degree')[['name', 'type', 'degree']].to_dict('records') if 'degree' in nodes_df.columns else [],
                'most_common_relationships': list(relationship_types.items())[:10]
            }
            
            # 保存报告
            report_path = f"stardew_valley_graph_{self.export_time}_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return report
            
        except Exception as e:
            print(f"生成报告时出错: {e}")
            return {"error": str(e)}
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()

def main():
    parser = argparse.ArgumentParser(description='导出星露谷物语知识图谱数据')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j连接URI')
    parser.add_argument('--username', default='neo4j', help='用户名')
    parser.add_argument('--password', required=True, help='密码')
    parser.add_argument('--output', default='./exports', help='输出目录')
    
    args = parser.parse_args()
    
    exporter = None
    try:
        # 创建导出器并执行导出
        exporter = StardewValleyExporter(args.uri, args.username, args.password)
        report = exporter.export_complete_dataset(args.output)
        
        print("\n" + "="*50)
        print("导出报告")
        print("="*50)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("="*50)
        
    except Exception as e:
        print(f"导出过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if exporter:
            exporter.close()

if __name__ == "__main__":
    main()