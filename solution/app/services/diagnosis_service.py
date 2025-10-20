import json
import os
from typing import Dict, List, Optional

class DiagnosisService:
    def __init__(self):
        self.knowledge_graph = self._load_knowledge_graph()
        print(f"🧠 DIAGNOSIS SERVICE INITIALIZED!")
        print(f"🧠 Knowledge graph loaded: {bool(self.knowledge_graph)}")
        if self.knowledge_graph:
            print(f"🧠 Root question: {self.knowledge_graph.get('text', 'UNKNOWN')}")
    
    def _load_knowledge_graph(self) -> Dict:
        """Загрузка графа знаний из data.json"""
        try:
            # Основной путь в Docker - правильная структура
            data_path = '/app/solution/statistics/data.json'
            
            if os.path.exists(data_path):
                print(f"✅ Loading from: {data_path}")
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ SUCCESS: Loaded knowledge graph with root: {data.get('text', 'UNKNOWN')}")
                    return data
            
            print(f"❌ File not found: {data_path}")
            
            # Альтернативные пути для отладки
            alternative_paths = [
                '/app/statistics/data.json',
                './solution/statistics/data.json',
                '../solution/statistics/data.json',
                'solution/statistics/data.json'
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    print(f"✅ Loading from alternative: {alt_path}")
                    with open(alt_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            print("❌ data.json not found anywhere, using fallback")
            return self._get_fallback_graph()
            
        except Exception as e:
            print(f"❌ ERROR loading knowledge graph: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_graph()
    
    def _get_fallback_graph(self):
        """Резервное дерево вопросов"""
        return {
            "text": "Нарушены ли зрительные функции?",
            "yes": {
                "text": "Есть ли перикорнеальная или смешанная инъекция?",
                "yes": {"text": "Ирит", "yes": None, "no": None},
                "no": {"text": "Ксерофтальмия", "yes": None, "no": None}
            },
            "no": {
                "text": "Есть ли конъюнктивальная инъекция?",
                "yes": {"text": "Бактериальный конъюнктивит", "yes": None, "no": None},
                "no": {"text": "Эндокринная офтальмопатия", "yes": None, "no": None}
            }
        }
    
    def get_initial_question(self) -> Optional[Dict]:
        """Получение начального вопроса"""
        if not self.knowledge_graph:
            return None
        
        question = {
            'text': self.knowledge_graph.get('text', 'Начало диагностики'),
            'is_final': False,
            'has_yes': 'yes' in self.knowledge_graph and self.knowledge_graph['yes'] is not None,
            'has_no': 'no' in self.knowledge_graph and self.knowledge_graph['no'] is not None
        }
        
        print(f"🧠 get_initial_question: {question}")
        return question
    
    def get_next_question(self, current_path: List[str], answer: str) -> Optional[Dict]:
        """Получение следующего вопроса"""
        print(f"\n🧠 GET_NEXT_QUESTION: path={current_path}, answer='{answer}'")
        
        if answer not in ['yes', 'no']:
            print(f"❌ Invalid answer: {answer}")
            return None
        
        # Начинаем с корня
        current_node = self.knowledge_graph
        print(f"🧠 Starting from root: {current_node.get('text', 'UNKNOWN')}")
        
        # Проходим по текущему пути
        for i, step in enumerate(current_path):
            print(f"🧠 Step {i}: '{step}' -> {current_node.get(step, {}).get('text', 'NOT FOUND')}")
            if step in current_node:
                current_node = current_node[step]
            else:
                print(f"❌ Path step not found: {step}")
                return None
        
        print(f"🧠 Current node before answer: {current_node.get('text', 'UNKNOWN')}")
        
        # Переходим по ответу
        if answer in current_node and current_node[answer] is not None:
            next_node = current_node[answer]
            new_path = current_path + [answer]
            
            is_final = next_node.get('yes') is None and next_node.get('no') is None
            
            result = {
                'text': next_node.get('text', 'Следующий вопрос'),
                'is_final': is_final,
                'has_yes': 'yes' in next_node and next_node['yes'] is not None,
                'has_no': 'no' in next_node and next_node['no'] is not None,
                'path': new_path
            }
            
            print(f"✅ NEXT QUESTION FOUND: '{result['text']}'")
            print(f"✅ New path: {new_path}")
            print(f"✅ Is final: {is_final}")
            
            return result
        
        print(f"❌ No '{answer}' path available from current node")
        return None
    
    def get_question_by_path(self, path: List[str]) -> Optional[Dict]:
        """Получение вопроса по пути"""
        print(f"🧠 get_question_by_path: path={path}")
        
        if not self.knowledge_graph:
            print("❌ Knowledge graph not loaded!")
            return None
            
        current_node = self.knowledge_graph
        
        for i, step in enumerate(path):
            print(f"🧠 Path step {i}: '{step}'")
            if step in current_node and current_node[step] is not None:
                current_node = current_node[step]
                print(f"🧠 Moved to: {current_node.get('text', 'UNKNOWN')}")
            else:
                print(f"❌ Path step not found: {step} in {list(current_node.keys())}")
                return None
        
        is_final = current_node.get('yes') is None and current_node.get('no') is None
        
        question = {
            'text': current_node.get('text', 'Вопрос'),
            'is_final': is_final,
            'has_yes': 'yes' in current_node and current_node['yes'] is not None,
            'has_no': 'no' in current_node and current_node['no'] is not None
        }
        
        print(f"🧠 Question at path {path}: {question}")
        return question
    
    def get_diagnosis(self, path: List[str]) -> Optional[str]:
        """Получение диагноза по пути"""
        current_node = self.knowledge_graph
        
        for step in path:
            if step in current_node:
                current_node = current_node[step]
            else:
                return None
        
        return current_node.get('text')