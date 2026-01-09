import json
import os
import glob
import csv
from collections import defaultdict
import re

class StardewValleyKnowledgeGraph:
    def __init__(self, content_path):
        """
        初始化星露谷物语知识图谱提取器
        
        Args:
            content_path: C:\Program Files (x86)\Steam\steamapps\common\Stardew Valley\Content (unpacked)
        """
        self.content_path = content_path
        self.triplets = []  # 存储(主语, 关系, 宾语)三元组
        self.entity_cache = {}  # 实体缓存，避免重复解析
        self.data = {}  # 存储加载的游戏数据
        
    def load_game_data(self):
        """
        加载游戏的核心数据文件
        基于星露谷物语实际的数据文件结构[1,2](@ref)
        """
        print("开始加载游戏数据文件...")
        
        # 定义关键数据文件路径
        data_files = {
            'quests': 'Data/Quests.json',
            'objects': 'Data/ObjectInformation.json',  # 物品信息
            'npcs': 'Data/NPCDispositions.json',      # NPC信息
            'locations': 'Data/Locations.json',        # 地点信息
            'monsters': 'Data/Monsters.json',          # 怪物信息（如果存在）
            'crafting': 'Data/CraftingRecipes.json',   # 合成配方
        }
        
        for data_type, file_path in data_files.items():
            full_path = os.path.join(self.content_path, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        self.data[data_type] = json.load(f)
                    print(f"✓ 已加载: {file_path}")
                except Exception as e:
                    print(f"✗ 加载失败 {file_path}: {str(e)}")
                    self.data[data_type] = {}
            else:
                print(f"⚠ 文件不存在: {file_path}")
                self.data[data_type] = {}
    
    def parse_quest_data(self):
        """
        解析任务数据，提取核心关系
        基于星露谷物语任务数据的实际格式[2](@ref)
        """
        if 'quests' not in self.data:
            return
            
        print("开始解析任务数据...")
        
        for quest_id, quest_str in self.data['quests'].items():
            try:
                # 解析任务字符串格式: "类型/名称/描述/目标/地点/..."
                parts = quest_str.split('/')
                if len(parts) < 5:
                    continue
                    
                quest_type, quest_name, description, objective = parts[0:4]
                location = parts[4] if len(parts) > 4 else "未知"
                
                # 缓存任务信息
                self.entity_cache[f"quest_{quest_id}"] = quest_name
                
                # 提取任务发布者关系 (NPC -> 任务)
                self._extract_quest_giver(quest_id, quest_name, quest_str)
                
                # 提取任务目标关系 (任务 -> 物品/怪物)
                self._extract_quest_objectives(quest_id, quest_name, objective, quest_str)
                
                # 提取任务奖励关系 (任务 -> 物品)
                self._extract_quest_rewards(quest_id, quest_name, quest_str)
                
                # 提取任务地点关系 (任务 -> 地点)
                if location and location != 'null' and location != '-1':
                    self.triplets.append((quest_name, "发生于", location))
                    
            except Exception as e:
                print(f"解析任务 {quest_id} 时出错: {str(e)}")
    
    def _extract_quest_giver(self, quest_id, quest_name, quest_str):
        """
        提取任务发布者关系
        基于任务数据中的发布者信息[2](@ref)
        """
        # 从任务描述或结构中推断发布者
        # 实际游戏中，发布者信息可能在其他关联数据中
        common_givers = {
            '1': '法师', '2': '齐先生', '6': '镇长刘易斯', '7': '罗宾',
            '21': '玛妮', '22': '乔迪', '100': '罗宾', '101': '乔迪'
        }
        
        if quest_id in common_givers:
            giver = common_givers[quest_id]
            self.triplets.append((giver, "发布", quest_name))
            self.entity_cache[f"npc_{quest_id}"] = giver
    
    def _extract_quest_objectives(self, quest_id, quest_name, objective, quest_str):
        """
        提取任务目标要求的关系
        """
        objective_lower = objective.lower()
        
        # 检测收集类任务
        collect_patterns = [
            (r'带(?:来|给).*?(\d+).*?(个)?(.*?)[。，]', '需要收集'),
            (r'收集.*?(\d+).*?(个)?(.*?)[。，]', '需要收集'),
            (r'带给.*?(一株|一个|一瓶)(.*?)[。，]', '需要交付'),
        ]
        
        for pattern, relation in collect_patterns:
            matches = re.finditer(pattern, objective)
            for match in matches:
                item_name = match.group(3) if len(match.groups()) >= 3 else match.group(2)
                if item_name and len(item_name) < 50:  # 避免过长的错误匹配
                    self.triplets.append((quest_name, relation, item_name.strip()))
        
        # 检测击杀类任务
        kill_patterns = [
            (r'击杀.*?(\d+).*?(只|个)(.*?)[。，]', '要求击杀'),
            (r'杀死.*?(\d+).*?(只|个)(.*?)[。，]', '要求击杀'),
            (r'讨伐.*?(\d+).*?(只|个)(.*?)[。，]', '要求击杀'),
        ]
        
        for pattern, relation in kill_patterns:
            matches = re.finditer(pattern, objective)
            for match in matches:
                monster_name = match.group(3)
                if monster_name and len(monster_name) < 50:
                    self.triplets.append((quest_name, relation, monster_name.strip()))
        
        # 检测到达地点类任务
        location_patterns = [
            (r'进入(.*?)[。，]', '要求到达'),
            (r'抵达(.*?)[。，]', '要求到达'),
            (r'到达(.*?)[。，]', '要求到达'),
            (r'前往(.*?)[。，]', '要求到达'),
        ]
        
        for pattern, relation in location_patterns:
            matches = re.finditer(pattern, objective)
            for match in matches:
                location_name = match.group(1)
                if location_name and len(location_name) < 100:
                    self.triplets.append((quest_name, relation, location_name.strip()))
    
    def _extract_quest_rewards(self, quest_id, quest_name, quest_str):
        """
        提取任务奖励关系
        基于任务数据中的奖励信息[2](@ref)
        """
        # 从任务字符串中解析奖励信息
        parts = quest_str.split('/')
        if len(parts) > 7:
            try:
                # 假设奖励金钱在特定位置
                money_reward = parts[7] if len(parts) > 7 else None
                if money_reward and money_reward != '-1' and money_reward.isdigit():
                    reward_amount = int(money_reward)
                    if reward_amount > 0:
                        self.triplets.append((quest_name, "奖励金币", f"{reward_amount}金"))
            except:
                pass
        
        # 常见任务奖励映射
        reward_mapping = {
            '6': '100金', '7': '100金', '8': '100金', '24': '250金',
            '100': '250金', '101': '350金', '102': '750金'
        }
        
        if quest_id in reward_mapping:
            self.triplets.append((quest_name, "奖励", reward_mapping[quest_id]))
    
    def parse_item_relationships(self):
        """
        解析物品之间的关系（合成、掉落等）
        """
        if 'crafting' not in self.data:
            return
            
        print("解析合成关系...")
        
        # 解析合成配方
        for recipe_id, recipe_str in self.data['crafting'].items():
            try:
                # 配方格式: "结果物品ID 数量/材料1ID 数量 材料2ID 数量/..."
                parts = recipe_str.split('/')
                if len(parts) >= 2:
                    result_part = parts[0].split()
                    materials_part = parts[1].split()
                    
                    if len(result_part) >= 2:
                        result_id, result_count = result_part[0], result_part[1]
                        result_name = self._get_item_name(result_id)
                        
                        # 解析材料
                        for i in range(0, len(materials_part), 2):
                            if i + 1 < len(materials_part):
                                material_id, material_count = materials_part[i], materials_part[i+1]
                                material_name = self._get_item_name(material_id)
                                
                                if result_name and material_name:
                                    self.triplets.append((result_name, "合成需要", f"{material_name}×{material_count}"))
                                    
            except Exception as e:
                print(f"解析配方 {recipe_id} 时出错: {str(e)}")
    
    def _get_item_name(self, item_id):
        """
        根据物品ID获取物品名称
        """
        if 'objects' in self.data and item_id in self.data['objects']:
            item_str = self.data['objects'][item_id]
            # 物品格式: "名称/价格/...""[2](@ref)
            parts = item_str.split('/')
            return parts[0] if parts else f"物品_{item_id}"
        return f"物品_{item_id}"
    
    def parse_npc_relationships(self):
        """
        解析NPC相关关系（喜好、日程等）
        """
        if 'npcs' not in self.data:
            return
            
        print("解析NPC关系...")
        
        for npc_id, npc_str in self.data['npcs'].items():
            try:
                # NPC数据格式较为复杂，包含多种信息
                parts = npc_str.split('/')
                if len(parts) > 0:
                    npc_name = parts[0]
                    self.entity_cache[f"npc_{npc_id}"] = npc_name
                    
                    # 这里可以扩展解析NPC的喜好、厌恶等关系
                    # 例如：解析礼物偏好数据
                    
            except Exception as e:
                print(f"解析NPC {npc_id} 时出错: {str(e)}")
    
    def extract_from_dialogue_files(self):
        """
        从对话文件中提取额外关系
        """
        print("扫描对话文件...")
        
        # 扫描Characters目录下的对话文件
        dialogue_path = os.path.join(self.content_path, 'Characters', 'Dialogue')
        if os.path.exists(dialogue_path):
            for file in os.listdir(dialogue_path):
                if file.endswith('.json'):
                    npc_name = os.path.splitext(file)[0]
                    file_path = os.path.join(dialogue_path, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            dialogue_data = json.load(f)
                            self._parse_dialogue_for_relationships(npc_name, dialogue_data)
                    except:
                        pass  # 忽略无法解析的文件
    
    def _parse_dialogue_for_relationships(self, npc_name, dialogue_data):
        """
        从对话数据中解析关系
        """
        if isinstance(dialogue_data, dict):
            for key, dialogue_text in dialogue_data.items():
                if isinstance(dialogue_text, str):
                    text_lower = dialogue_text.lower()
                    
                    # 检测提到任务
                    if '任务' in text_lower or 'quest' in text_lower:
                        # 这里可以添加更复杂的自然语言处理来提取具体关系
                        pass
                    
                    # 检测提到物品
                    common_items = ['剑', '斧', '镐', '鱼竿', '种子', '作物']
                    for item in common_items:
                        if item in text_lower:
                            self.triplets.append((npc_name, "提到", item))
    
    def enhance_with_hardcoded_knowledge(self):
        """
        基于游戏常识添加硬编码的关系
        这些是基于游戏机制的常见关系[1,2](@ref)
        """
        print("添加游戏常识关系...")
        
        # 商店相关的购买关系
        shop_relationships = [
            ('皮埃尔', '出售', '种子'),
            ('皮埃尔', '出售', '肥料'),
            ('克林特', '出售', '矿石'),
            ('克林特', '打造', '工具'),
            ('罗宾', '出售', '建材'),
            ('威利', '出售', '鱼竿'),
            ('玛妮', '出售', '动物'),
        ]
        
        for subj, rel, obj in shop_relationships:
            self.triplets.append((subj, rel, obj))
        
        # 地点相关的包含关系
        location_contains = [
            ('矿洞', '包含', '矿石'),
            ('矿洞', '包含', '怪物'),
            ('森林', '包含', ' forageables'),
            ('河流', '包含', '鱼类'),
            ('海洋', '包含', '鱼类'),
        ]
        
        for subj, rel, obj in location_contains:
            self.triplets.append((subj, rel, obj))
        
        # 季节与作物的关系
        season_crops = [
            ('春季', '适合种植', '防风草'),
            ('春季', '适合种植', '花椰菜'),
            ('夏季', '适合种植', '蓝莓'),
            ('夏季', '适合种植', '辣椒'),
            ('秋季', '适合种植', '蔓越莓'),
            ('秋季', '适合种植', '南瓜'),
        ]
        
        for subj, rel, obj in season_crops:
            self.triplets.append((subj, rel, obj))
    
    def remove_duplicates(self):
        """
        去除重复的三元组
        """
        print("去除重复关系...")
        unique_triplets = []
        seen = set()
        
        for triplet in self.triplets:
            triplet_str = f"{triplet[0]}|{triplet[1]}|{triplet[2]}"
            if triplet_str not in seen:
                seen.add(triplet_str)
                unique_triplets.append(triplet)
        
        self.triplets = unique_triplets
        print(f"去重后剩余 {len(self.triplets)} 个三元组")
    
    def export_triplets(self, output_file="stardew_knowledge_graph.csv"):
        """
        导出三元组到CSV文件
        """
        if not self.triplets:
            print("没有可导出的三元组数据")
            return
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['subject', 'relation', 'object'])
            
            for triplet in self.triplets:
                writer.writerow(triplet)
        
        print(f"三元组已导出到: {output_file}")
        
        # 同时导出实体映射
        entity_file = "stardew_entities.csv"
        with open(entity_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['entity_id', 'entity_name'])
            for entity_id, entity_name in self.entity_cache.items():
                writer.writerow([entity_id, entity_name])
        
        print(f"实体映射已导出到: {entity_file}")
    
    def print_statistics(self):
        """
        打印提取统计信息
        """
        if not self.triplets:
            print("没有可统计的三元组数据")
            return
        
        relation_stats = defaultdict(int)
        for triplet in self.triplets:
            relation_stats[triplet[1]] += 1
        
        print("\n" + "="*50)
        print("知识图谱提取统计")
        print("="*50)
        print(f"总三元组数量: {len(self.triplets)}")
        print(f"唯一实体数量: {len(self.entity_cache)}")
        print("\n关系类型统计:")
        for relation, count in sorted(relation_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {relation}: {count}个")
        
        print("\n样例三元组:")
        for i, triplet in enumerate(self.triplets[:10]):
            print(f"  {i+1}. ({triplet[0]}) -[{triplet[1]}]-> ({triplet[2]})")
    
    def run_extraction(self):
        """
        运行完整的提取流程
        """
        print("开始提取星露谷物语知识图谱...")
        print("="*60)
        
        # 1. 加载游戏数据
        self.load_game_data()
        
        # 2. 解析各种关系
        self.parse_quest_data()
        self.parse_item_relationships()
        self.parse_npc_relationships()
        
        # 3. 从对话文件补充关系
        self.extract_from_dialogue_files()
        
        # 4. 添加游戏常识
        self.enhance_with_hardcoded_knowledge()
        
        # 5. 清理数据
        self.remove_duplicates()
        
        # 6. 输出结果
        self.print_statistics()
        self.export_triplets()
        
        print("\n提取完成！")
        return self.triplets

# 使用示例
if __name__ == "__main__":
    # 替换为您的实际游戏数据路径
    CONTENT_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Stardew Valley\Content (unpacked)"
    
    # 创建提取器实例
    extractor = StardewValleyKnowledgeGraph(CONTENT_PATH)
    
    # 运行提取流程
    knowledge_triplets = extractor.run_extraction()
    
    # 保存详细日志
    with open('extraction_log.txt', 'w', encoding='utf-8') as f:
        f.write("星露谷物语知识图谱提取日志\n")
        f.write("="*50 + "\n")
        f.write(f"数据路径: {CONTENT_PATH}\n")
        f.write(f"提取时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总三元组数: {len(knowledge_triplets)}\n\n")
        
        f.write("前50个三元组:\n")
        for i, triplet in enumerate(knowledge_triplets[:50]):
            f.write(f"{i+1:3d}. ({triplet[0]}) -[{triplet[1]}]-> ({triplet[2]})\n")
    import os
    print("当前工作目录是:", os.getcwd())
