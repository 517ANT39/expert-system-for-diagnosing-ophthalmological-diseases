from sqlalchemy.orm import Session, joinedload
from ..models.database_models import Consultation, Patient, Doctor

class ConsultationRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_consultation(self, consultation_data: dict):
        """Создание новой консультации"""
        try:
            consultation = Consultation(**consultation_data)
            self.db_session.add(consultation)
            self.db_session.commit()
            self.db_session.refresh(consultation)
            return consultation
        except Exception as e:
            self.db_session.rollback()
            raise e

    def get_consultation_by_id(self, consultation_id: int):
        """Получение консультации по ID"""
        return self.db_session.query(Consultation)\
            .options(
                joinedload(Consultation.patient),
                joinedload(Consultation.doctor)
            )\
            .filter(Consultation.id == consultation_id)\
            .first()

    def get_patient_consultations(self, patient_id: int):
        """Получение всех консультаций пациента"""
        return self.db_session.query(Consultation)\
            .options(joinedload(Consultation.doctor))\
            .filter(Consultation.patient_id == patient_id)\
            .order_by(Consultation.consultation_date.desc())\
            .all()

    def get_doctor_consultations(self, doctor_id: int):
        """Получение всех консультаций врача"""
        return self.db_session.query(Consultation)\
            .options(joinedload(Consultation.patient))\
            .filter(Consultation.doctor_id == doctor_id)\
            .order_by(Consultation.consultation_date.desc())\
            .all()

    def update_consultation(self, consultation_id: int, consultation_data: dict):
        """Обновление данных консультации"""
        try:
            consultation = self.get_consultation_by_id(consultation_id)
            if not consultation:
                return None
            
            for key, value in consultation_data.items():
                if hasattr(consultation, key):
                    setattr(consultation, key, value)
            
            self.db_session.commit()
            self.db_session.refresh(consultation)
            return consultation
            
        except Exception as e:
            self.db_session.rollback()
            raise e

    def update_consultation_status(self, consultation_id: int, status: str):
        """Обновление статуса консультации"""
        try:
            consultation = self.get_consultation_by_id(consultation_id)
            if consultation:
                consultation.status = status
                self.db_session.commit()
                return consultation
            return None
        except Exception as e:
            self.db_session.rollback()
            raise e

    def get_active_consultation(self, patient_id: int, doctor_id: int):
        """Получение активной консультации для пациента и врача"""
        return self.db_session.query(Consultation)\
            .filter(
                Consultation.patient_id == patient_id,
                Consultation.doctor_id == doctor_id,
                Consultation.status.in_(['draft', 'active'])
            )\
            .order_by(Consultation.consultation_date.desc())\
            .first()