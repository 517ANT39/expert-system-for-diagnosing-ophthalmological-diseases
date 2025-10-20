import os
import json
from datetime import datetime
from ..repositories.consultation_repository import ConsultationRepository
from ..models.database_models import ConsultationStatusEnum

class ConsultationService:
    def __init__(self, db_session):
        self.consultation_repository = ConsultationRepository(db_session)
        self.knowledge_graph = self._load_knowledge_graph()

    def _load_knowledge_graph(self):
        """Загрузка графа знаний из data.json"""
        try:
            # Путь к data.json относительно корня проекта
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_file = os.path.join(base_dir, 'statistics', 'data.json')
            
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки базы знаний: {e}")
            return {}

    def _get_question(self, path=None):
        """Получение текущего вопроса по пути"""
        if path is None:
            path = []
        
        current = self.knowledge_graph
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

    def _get_next_question(self, path, answer):
        """Получение следующего пути на основе ответа"""
        if answer not in ['yes', 'no']:
            return path
        
        new_path = path.copy()
        new_path.append(answer)
        
        # Проверяем, существует ли следующий вопрос
        next_question = self._get_question(new_path)
        if next_question:
            return new_path
        return path

    def _get_diagnosis(self, path):
        """Получение диагноза по пути ответов"""
        current = self.knowledge_graph
        for step in path:
            if step in current:
                current = current[step]
            else:
                return None
        
        if current and 'text' in current:
            return current['text']
        return None

    def start_consultation(self, patient_id: int, doctor_id: int):
        """Начало новой консультации"""
        # Проверяем, есть ли активная консультация
        active_consultation = self.consultation_repository.get_active_consultation(patient_id, doctor_id)
        
        if active_consultation:
            return active_consultation
        
        # Получаем первый вопрос из графа решений
        first_question = self._get_question()
        
        # Создаем новую консультацию
        consultation_data = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'status': 'active',
            'sub_graph_find_diagnosis': {
                'current_path': [],  # Путь ответов в графе
                'current_question': first_question['text'] if first_question else "Начало консультации",
                'answers': {},
                'symptoms': [],
                'started_at': datetime.utcnow().isoformat()
            }
        }
        
        return self.consultation_repository.create_consultation(consultation_data)

    def save_consultation_answer(self, consultation_id: int, answer: str):
        """Сохранение ответа на вопрос и переход к следующему"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        # Получаем текущий вопрос
        current_question = self._get_question(current_path)
        if not current_question:
            raise ValueError("Текущий вопрос не найден")
        
        # Сохраняем ответ
        if 'answers' not in diagnosis_data:
            diagnosis_data['answers'] = {}
        
        question_key = f"q{len(current_path) + 1}"
        diagnosis_data['answers'][question_key] = {
            'question': current_question['text'],
            'answer': answer,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Получаем следующий путь
        next_path = self._get_next_question(current_path, answer)
        
        # Проверяем, достигли ли мы диагноза
        next_question = self._get_question(next_path)
        
        if next_question and not next_question['is_final']:
            # Есть следующий вопрос
            diagnosis_data['current_path'] = next_path
            diagnosis_data['current_question'] = next_question['text']
        else:
            # Достигли конечного диагноза
            diagnosis = self._get_diagnosis(next_path)
            diagnosis_data['current_path'] = next_path
            diagnosis_data['current_question'] = diagnosis or "Диагноз не определен"
            diagnosis_data['final_diagnosis_candidate'] = diagnosis
            diagnosis_data['completed_at'] = datetime.utcnow().isoformat()
        
        consultation_data = {
            'sub_graph_find_diagnosis': diagnosis_data
        }
        
        return self.consultation_repository.update_consultation(consultation_id, consultation_data)

    def get_current_question(self, consultation_id: int):
        """Получение текущего вопроса консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            return None
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        return self._get_question(current_path)

    def complete_consultation(self, consultation_id: int, final_diagnosis: str = None, notes: str = None):
        """Завершение консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        
        # Если диагноз не указан явно, используем кандидата из графа
        if not final_diagnosis and 'final_diagnosis_candidate' in diagnosis_data:
            final_diagnosis = diagnosis_data['final_diagnosis_candidate']
        
        consultation_data = {
            'status': 'completed',
            'final_diagnosis': final_diagnosis,
            'notes': notes
        }
        
        if 'completed_at' not in diagnosis_data:
            diagnosis_data['completed_at'] = datetime.utcnow().isoformat()
        
        consultation_data['sub_graph_find_diagnosis'] = diagnosis_data
        
        return self.consultation_repository.update_consultation(consultation_id, consultation_data)

    def get_consultation_result(self, consultation_id: int):
        """Получение результатов консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            return None
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        # Получаем диагноз из графа
        graph_diagnosis = self._get_diagnosis(current_path)
        final_diagnosis = consultation.final_diagnosis or graph_diagnosis
        
        # Формируем историю вопросов-ответов
        qa_history = []
        answers = diagnosis_data.get('answers', {})
        for key, qa in sorted(answers.items()):
            qa_history.append({
                'question': qa['question'],
                'answer': qa['answer'],
                'timestamp': qa.get('timestamp')
            })
        
        # Генерируем рекомендации на основе диагноза
        recommendations = self._generate_recommendations(final_diagnosis)
        
        return {
            'consultation': consultation,
            'diagnosis_result': {
                'primary_diagnosis': final_diagnosis,
                'confidence': self._calculate_confidence(qa_history),
                'explanation': self._generate_explanation(qa_history, final_diagnosis),
                'qa_history': qa_history,
                'recommendations': recommendations
            }
        }

    def _calculate_confidence(self, qa_history: list) -> int:
        """Расчет уверенности в диагнозе на основе количества ответов"""
        if not qa_history:
            return 0
        
        total_questions = len(qa_history)
        confidence = min(80 + (total_questions * 2), 95)
        return confidence

    def _generate_explanation(self, qa_history: list, diagnosis: str) -> str:
        """Генерация объяснения диагноза"""
        if not qa_history:
            return "Диагноз основан на базовых симптомах."
        
        positive_answers = [qa for qa in qa_history if qa['answer'] == 'yes']
        
        if positive_answers:
            symptoms = [qa['question'] for qa in positive_answers[:3]]
            symptoms_text = ", ".join(symptoms)
            return f"Диагноз '{diagnosis}' основан на наличии следующих симптомов: {symptoms_text}."
        else:
            return f"Диагноз '{diagnosis}' основан на отсутствии характерных симптомов других заболеваний."

    def _generate_recommendations(self, diagnosis: str) -> dict:
        """Генерация рекомендаций по диагнозу"""
        # База рекомендаций для различных диагнозов
        recommendations_db = {
            "Ирит": {
                'medication': [
                    "Циклоплегические средства: Атропин 1% - по 1 капле 2-3 раза в день",
                    "Противовоспалительные: Дексаметазон 0.1% - по 1 капле 4-6 раз в день"
                ],
                'general': [
                    "Постельный режим",
                    "Защита глаза от света",
                    "Немедленное обращение при ухудшении"
                ],
                'follow_up': [
                    "Контрольный осмотр через 2-3 дня",
                    "Консультация ревматолога при рецидивирующем течении"
                ]
            },
            "Бактериальный конъюнктивит": {
                'medication': [
                    "Антибактериальные капли: Ципрофлоксацин 0.3% - по 1-2 капли 4-6 раз в день",
                    "Антибактериальная мазь на ночь: Тетрациклин 1%"
                ],
                'general': [
                    "Частое мытье рук",
                    "Использование отдельного полотенца",
                    "Исключение контактных линз на период лечения"
                ],
                'follow_up': [
                    "Повторный осмотр через 3-5 дней",
                    "Обратиться при отсутствии улучшения через 48 часов"
                ]
            },
            "Катаракта": {
                'medication': [
                    "Витаминные капли: Тауфон 4% - по 1-2 капли 2-3 раза в день",
                    "При прогрессировании - хирургическое лечение"
                ],
                'general': [
                    "Защита от ультрафиолета (солнцезащитные очки)",
                    "Контроль сопутствующих заболеваний (диабет, гипертония)"
                ],
                'follow_up': [
                    "Наблюдение у офтальмолога каждые 6-12 месяцев",
                    "Консультация хирурга при значительном снижении зрения"
                ]
            }
        }
        
        # Поиск рекомендаций по ключевым словам
        for key, value in recommendations_db.items():
            if key.lower() in diagnosis.lower():
                return value
        
        # Рекомендации по умолчанию
        return {
            'medication': [
                "Симптоматическое лечение по показаниям",
                "Увлажняющие капли при необходимости"
            ],
            'general': [
                "Наблюдение за динамикой симптомов",
                "Обратиться к офтальмологу для уточнения диагноза"
            ],
            'follow_up': [
                "Повторная консультация при сохранении симптомов",
                "Немедленно обратиться при ухудшении состояния"
            ]
        }

    def get_consultation_progress(self, consultation_id: int):
        """Получение прогресса консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            return None
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        answers = diagnosis_data.get('answers', {})
        
        # Оценка прогресса на основе количества ответов
        total_questions = len(answers)
        progress = min((total_questions / 15) * 100, 100)  # Максимум 15 вопросов
        
        return {
            'current_question': diagnosis_data.get('current_question', ''),
            'progress_percent': progress,
            'questions_answered': total_questions,
            'is_completed': consultation.status == 'completed'
        }