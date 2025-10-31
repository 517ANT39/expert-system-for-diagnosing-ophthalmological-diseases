from flask import jsonify
from utils.database import _calculate_age

def json_response(success, message, data=None, status_code=200):
    """Универсальный метод для JSON ответов"""
    response = {'success': success, 'message': message}
    if data:
        response.update(data)
    return jsonify(response), status_code

def prepare_patient_data(patient, for_json=True):
    """Подготовка данных пациента для JSON ответов или шаблонов"""
    base_data = {
        'id': patient.id,
        'last_name': patient.last_name,
        'first_name': patient.first_name,
        'middle_name': patient.middle_name,
        'sex': patient.sex,
        'phone': patient.phone,
        'email': patient.email,
        'address': patient.address,
        'allergies': patient.allergies,
        'chronic_diseases': patient.chronic_diseases,
        'current_medications': patient.current_medications,
        'family_anamnes': patient.family_anamnes,
        'notes': patient.notes
    }
    
    if for_json:
        # Для JSON ответов
        base_data.update({
            'birthday': patient.birthday.isoformat() if patient.birthday else None,
            'registered_at': patient.registered_at.isoformat() if patient.registered_at else None,
            'age': _calculate_age(patient.birthday) if patient.birthday else None
        })
    else:
        # Для шаблонов
        base_data.update({
            'birthday': patient.birthday,
            'registered_at': patient.registered_at,
            'age': _calculate_age(patient.birthday) if patient.birthday else None
        })
    
    return base_data

def prepare_consultation_patient_data(patient):
    """Подготовка данных пациента для шаблонов консультации"""
    return {
        'id': patient.id,
        'last_name': patient.last_name,
        'first_name': patient.first_name,
        'middle_name': patient.middle_name,
        'birthday': patient.birthday,
        'age': _calculate_age(patient.birthday) if patient.birthday else None
    }

def prepare_consultation_result_data(consultation_data, diagnosis_result):
    """Подготовка данных для страницы результатов консультации"""
    patient = consultation_data.patient
    doctor = consultation_data.doctor
    
    from datetime import datetime
    return {
        'patient': {
            'name': f"{patient.last_name} {patient.first_name} {patient.middle_name or ''}".strip(),
            'birth_date': patient.birthday.strftime('%d.%m.%Y') if patient.birthday else 'Не указана',
            'sex': patient.sex,
            'age': _calculate_age(patient.birthday) if patient.birthday else None
        },
        'doctor': {
            'name': f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}".strip(),
            'qualification': "Врач-офтальмолог"
        },
        'consultation_info': {
            'date': consultation_data.consultation_date.strftime('%d.%m.%Y %H:%M') if consultation_data.consultation_date else datetime.now().strftime('%d.%m.%Y %H:%M'),
            'final_diagnosis': consultation_data.final_diagnosis or diagnosis_result['primary_diagnosis'],
            'notes': consultation_data.notes or ''
        },
        'diagnosis_result': diagnosis_result
    }