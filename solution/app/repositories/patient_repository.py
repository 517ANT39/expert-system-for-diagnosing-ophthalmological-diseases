from sqlalchemy.orm import Session
from datetime import datetime

# Относительные импорты внутри пакета app
from ..models.database_models import Patient, Consultation, Doctor

class PatientRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_patient(self, patient_data: dict):
        """Создание нового пациента"""
        try:
            # Преобразуем строку даты в объект datetime
            if 'birthday' in patient_data and isinstance(patient_data['birthday'], str):
                patient_data['birthday'] = datetime.strptime(patient_data['birthday'], '%Y-%m-%d').date()
            
            # Создаем объект пациента
            patient = Patient(**patient_data)
            
            self.db_session.add(patient)
            self.db_session.commit()
            self.db_session.refresh(patient)
            
            return patient
            
        except Exception as e:
            self.db_session.rollback()
            raise e

    def get_patient_by_id(self, patient_id: int):
        """Получение пациента по ID"""
        return self.db_session.query(Patient).filter(Patient.id == patient_id).first()
    
    def get_all_patients(self):
        """Получение всех пациентов из базы данных"""
        return self.db_session.query(Patient).all()
    
    def search_patients(self, search_term: str = None):
        """Поиск пациентов по ФИО"""
        query = self.db_session.query(Patient)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (Patient.last_name.ilike(search_pattern)) |
                (Patient.first_name.ilike(search_pattern)) |
                (Patient.middle_name.ilike(search_pattern)) |
                (Patient.phone.ilike(search_pattern)) |
                (Patient.email.ilike(search_pattern))
            )
        
        return query.all()

    def get_patients_by_doctor(self, doctor_id: int):
        """Получение всех пациентов врача (через консультации)"""
        return self.db_session.query(Patient).distinct().\
            join(Patient.consultations).\
            filter(Consultation.doctor_id == doctor_id).\
            all()

    def update_patient(self, patient_id: int, patient_data: dict):
        """Обновление данных пациента"""
        try:
            patient = self.get_patient_by_id(patient_id)
            if not patient:
                return None
            
            # Преобразуем дату рождения если нужно
            if 'birthday' in patient_data and isinstance(patient_data['birthday'], str):
                patient_data['birthday'] = datetime.strptime(patient_data['birthday'], '%Y-%m-%d').date()
            
            # Обновляем поля
            for key, value in patient_data.items():
                if hasattr(patient, key):
                    setattr(patient, key, value)
            
            self.db_session.commit()
            self.db_session.refresh(patient)
            
            return patient
            
        except Exception as e:
            self.db_session.rollback()
            raise e

    def delete_patient(self, patient_id: int) -> bool:
        """Удаление пациента"""
        try:
            patient = self.get_patient_by_id(patient_id)
            if patient:
                self.db_session.delete(patient)
                self.db_session.commit()
                return True
            return False
            
        except Exception as e:
            self.db_session.rollback()
            raise e

    def search_patients(self, search_term: str, doctor_id: int = None):
        """Поиск пациентов по ФИО"""
        query = self.db_session.query(Patient)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                (Patient.last_name.ilike(search_pattern)) |
                (Patient.first_name.ilike(search_pattern)) |
                (Patient.middle_name.ilike(search_pattern))
            )
        
        if doctor_id:
            query = query.join(Patient.consultations).filter(Consultation.doctor_id == doctor_id)
        
        return query.all()