from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import bcrypt
import re

# Импортируем модели
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from models.database_models import Doctor

class AuthService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def register_doctor(self, doctor_data: dict):
        # Валидация обязательных полей
        required_fields = ['last_name', 'first_name', 'email', 'password']
        for field in required_fields:
            if not doctor_data.get(field):
                raise ValueError(f"Поле {field} обязательно для заполнения")
        
        # Проверка email
        if not self._is_valid_email(doctor_data['email']):
            raise ValueError("Некорректный формат email")
        
        # Проверка пароля
        if len(doctor_data['password']) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        
        # Хешируем пароль
        hashed_password = bcrypt.hashpw(
            doctor_data['password'].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        try:
            doctor = Doctor(
                last_name=doctor_data['last_name'],
                first_name=doctor_data['first_name'],
                middle_name=doctor_data.get('middle_name'),
                email=doctor_data['email'],
                phone=doctor_data.get('phone'),
                password=hashed_password
            )
            
            self.db_session.add(doctor)
            self.db_session.commit()
            self.db_session.refresh(doctor)
            return doctor
            
        except IntegrityError:
            self.db_session.rollback()
            raise ValueError("Пользователь с таким email уже существует")
        except Exception as e:
            self.db_session.rollback()
            raise e

    def login_doctor(self, email: str, password: str):
        if not email or not password:
            raise ValueError("Email и пароль обязательны для заполнения")
        
        doctor = self.db_session.query(Doctor).filter(
            Doctor.email == email
        ).first()
        
        if not doctor:
            raise ValueError("Пользователь с таким email не найден")
        
        if not bcrypt.checkpw(
            password.encode('utf-8'),
            doctor.password.encode('utf-8')
        ):
            raise ValueError("Неверный пароль")
        
        return doctor

    def get_doctor_profile(self, doctor_id: int):
        return self.db_session.query(Doctor).filter(
            Doctor.id == doctor_id
        ).first()

    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None