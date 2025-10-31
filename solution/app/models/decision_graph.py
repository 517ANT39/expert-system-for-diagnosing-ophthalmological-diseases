import json
import os
from typing import Dict, Any, Optional

class DecisionGraph:
    def __init__(self, data_file: str = None):
        self.graph = {}
        if data_file:
            self.load_from_file(data_file)
    
    def load_from_file(self, file_path: str):
        """Загрузка графа решений из JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.graph = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки графа решений: {e}")
            self.graph = {}
    
    def get_question(self, path: list = None) -> Optional[Dict[str, Any]]:
        """Получение текущего вопроса по пути"""
        if path is None:
            path = []
        
        current = self.graph
        for step in path:
            if step in current and current[step] is not None:
                current = current[step]
            else:
                return None
        
        if current and 'text' in current:
            return {
                'text': current['text'],
                'is_final': current.get('yes') is None and current.get('no') is None,
                'has_yes': current.get('yes') is not None,
                'has_no': current.get('no') is not None
            }
        return None
    
    def get_next_question(self, path: list, answer: str) -> list:
        """Получение следующего пути на основе ответа"""
        if answer not in ['yes', 'no']:
            return path
        
        new_path = path.copy()
        new_path.append(answer)
        
        # Проверяем, существует ли следующий вопрос
        next_question = self.get_question(new_path)
        if next_question:
            return new_path
        return path
    
    def get_diagnosis(self, path: list) -> Optional[str]:
        """Получение диагноза по пути ответов"""
        current = self.graph
        for step in path:
            if step in current:
                current = current[step]
            else:
                return None
        
        if current and 'text' in current:
            return current['text']
        return None
    
    def get_all_possible_diagnoses(self) -> list:
        """Получение всех возможных диагнозов из графа"""
        diagnoses = []
        
        def traverse(node, path):
            if node is None:
                return
            
            if 'text' in node:
                # Если это конечный узел (нет yes/no ответов)
                if node.get('yes') is None and node.get('no') is None:
                    diagnoses.append({
                        'diagnosis': node['text'],
                        'path': path.copy()
                    })
            
            if 'yes' in node and node['yes'] is not None:
                traverse(node['yes'], path + ['yes'])
            
            if 'no' in node and node['no'] is not None:
                traverse(node['no'], path + ['no'])
        
        traverse(self.graph, [])
        return diagnoses

# Глобальный экземпляр графа решений
knowledge_graph = DecisionGraph()