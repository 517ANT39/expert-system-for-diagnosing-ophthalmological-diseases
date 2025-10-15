import json
import os
from typing import Dict, List, Optional, Any

class DecisionTreeService:
    def __init__(self, knowledge_base_path: str = None):
        self.knowledge_base_path = knowledge_base_path or os.environ.get(
            'KNOWLEDGE_BASE_PATH', 
            '/app/knowledge_base/decision_graph.json'
        )
        self.decision_graph = self._load_decision_graph()
    
    def _load_decision_graph(self) -> Dict:
        """Загрузка базы знаний из JSON файла"""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Файл базы знаний не найден: {self.knowledge_base_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"Ошибка парсинга JSON: {e}")
    
    def find_node_by_id(self, node_id: str, nodes: List[Dict]) -> Optional[Dict]:
        """
        Рекурсивная функция поиска узла по ID
        """
        for node in nodes:
            if node.get('id') == node_id:
                return node
            
            # Рекурсивный поиск в детях
            children = node.get('children', [])
            if children:
                found = self.find_node_by_id(node_id, children)
                if found:
                    return found
        
        return None
    
    def traverse_decision_tree(self, 
                             current_node_id: str, 
                             user_answers: Dict[str, bool],
                             path: List[Dict] = None) -> Dict[str, Any]:
        """
        Рекурсивный обход графа принятия решений на основе ответов пользователя
        
        Args:
            current_node_id: ID текущего узла
            user_answers: словарь с ответами пользователя {question_id: answer}
            path: пройденный путь для отладки
        
        Returns:
            Dict с результатом диагностики
        """
        if path is None:
            path = []
        
        current_node = self.find_node_by_id(current_node_id, self.decision_graph.get('nodes', []))
        
        if not current_node:
            return {
                'status': 'error',
                'message': f'Узел с ID {current_node_id} не найден',
                'path': path
            }
        
        # Добавляем текущий узел в путь
        path.append({
            'node_id': current_node_id,
            'question': current_node.get('question'),
            'type': current_node.get('type')
        })
        
        # Если это конечный узел (диагноз)
        if current_node.get('type') == 'diagnosis':
            return {
                'status': 'diagnosis_found',
                'diagnosis': current_node.get('diagnosis'),
                'treatment': current_node.get('treatment'),
                'confidence': current_node.get('confidence', 1.0),
                'path': path,
                'node_id': current_node_id
            }
        
        # Если это вопрос
        elif current_node.get('type') == 'question':
            question_id = current_node.get('id')
            user_answer = user_answers.get(question_id)
            
            if user_answer is None:
                return {
                    'status': 'question',
                    'question_id': question_id,
                    'question': current_node.get('question'),
                    'options': current_node.get('options', ['Да', 'Нет']),
                    'path': path,
                    'node_id': current_node_id
                }
            
            # Определяем следующий узел на основе ответа
            next_node_id = None
            children = current_node.get('children', [])
            
            for child in children:
                condition = child.get('condition')
                if condition == 'yes' and user_answer is True:
                    next_node_id = child.get('node_id')
                    break
                elif condition == 'no' and user_answer is False:
                    next_node_id = child.get('node_id')
                    break
            
            if next_node_id:
                return self.traverse_decision_tree(next_node_id, user_answers, path)
            else:
                return {
                    'status': 'no_path',
                    'message': 'Не найден путь для данного ответа',
                    'path': path,
                    'node_id': current_node_id
                }
        
        else:
            return {
                'status': 'error',
                'message': f'Неизвестный тип узла: {current_node.get("type")}',
                'path': path,
                'node_id': current_node_id
            }
    
    def start_diagnosis(self, initial_symptoms: Dict[str, bool] = None) -> Dict[str, Any]:
        """
        Начало диагностики с корневого узла
        
        Args:
            initial_symptoms: начальные симптомы {symptom_id: presence}
        
        Returns:
            Результат диагностики или следующий вопрос
        """
        root_node_id = self.decision_graph.get('root_node_id')
        if not root_node_id:
            # Ищем первый узел, если root_node_id не указан
            root_node_id = self.decision_graph.get('nodes', [])[0].get('id') if self.decision_graph.get('nodes') else None
        
        if not root_node_id:
            return {
                'status': 'error',
                'message': 'Корневой узел не найден в базе знаний'
            }
        
        return self.traverse_decision_tree(root_node_id, initial_symptoms or {})
    
    def get_all_symptoms(self) -> List[Dict]:
        """
        Получить все симптомы из базы знаний
        """
        symptoms = []
        
        def extract_symptoms(nodes):
            for node in nodes:
                if node.get('type') == 'question':
                    symptoms.append({
                        'id': node.get('id'),
                        'question': node.get('question'),
                        'description': node.get('description', ''),
                        'category': node.get('category', 'general')
                    })
                
                # Рекурсивно обходим детей
                children = node.get('children', [])
                if children:
                    extract_symptoms(children)
        
        extract_symptoms(self.decision_graph.get('nodes', []))
        return symptoms