def extract_symptoms_for_html(diagnosis_data):
    """Извлекает симптомы для HTML шаблона"""
    if not diagnosis_data:
        return []
    
    symptoms = []
    
    # Формат 1: symptoms_evidence как список словарей
    if 'symptoms_evidence' in diagnosis_data and isinstance(diagnosis_data['symptoms_evidence'], list):
        for symptom in diagnosis_data['symptoms_evidence']:
            if isinstance(symptom, dict):
                symptoms.append({
                    'name': symptom.get('name', symptom.get('symptom', 'Неизвестный симптом')),
                    'present': symptom.get('present', symptom.get('confirmed', True))
                })
    
    # Формат 2: answers как словарь вопросов-ответов (основной формат)
    elif 'answers' in diagnosis_data and isinstance(diagnosis_data['answers'], dict):
        for question, answer_data in diagnosis_data['answers'].items():
            if isinstance(answer_data, dict):
                symptoms.append({
                    'name': answer_data.get('question', question),
                    'present': answer_data.get('answer') == 'yes'
                })
    
    # Формат 3: прямой список симптомов
    elif 'symptoms' in diagnosis_data and isinstance(diagnosis_data['symptoms'], list):
        for symptom in diagnosis_data['symptoms']:
            if isinstance(symptom, str):
                symptoms.append({
                    'name': symptom,
                    'present': True
                })
            elif isinstance(symptom, dict):
                symptoms.append({
                    'name': symptom.get('name', 'Неизвестный симптом'),
                    'present': symptom.get('present', True)
                })
    
    return symptoms

def prepare_consultation_data(consultation):
    """Подготавливает данные консультации для отображения"""
    diagnosis_data = consultation.sub_graph_find_diagnosis or {}
    
    # Единая логика извлечения симптомов
    symptoms_evidence = extract_symptoms_for_html(diagnosis_data)
    
    return {
        'primary_diagnosis': consultation.final_diagnosis or diagnosis_data.get('primary_diagnosis', 'Диагноз не указан'),
        'symptoms_evidence': symptoms_evidence,
        'recommendations': diagnosis_data.get('recommendations', {})
    }