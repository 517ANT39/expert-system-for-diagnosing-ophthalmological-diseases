from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.database_models import Doctor
import bcrypt

class UserRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_doctor(self, doctor_data: dict) -> Doctor:
        try:
            # Хешируем пароль
            hashed_password = bcrypt.hashpw(
                doctor_data['password'].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
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

    def get_doctor_by_email(self, email: str) -> Doctor:
        return self.db_session.query(Doctor).filter(
            Doctor.email == email, 
            Doctor.is_active == True
        ).first()

    def get_doctor_by_id(self, doctor_id: int) -> Doctor:
        return self.db_session.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.is_active == True
        ).first()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )