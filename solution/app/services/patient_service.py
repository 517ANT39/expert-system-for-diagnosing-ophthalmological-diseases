# Относительные импорты внутри пакета app
from ..repositories.patient_repository import PatientRepository
from ..models.database_models import SexEnum
from datetime import datetime
import re

class PatientService:
    def __init__(self, db_session):
        self.patient_repository = PatientRepository(db_session)

    def create_patient(self, patient_data: dict):
        """Создание нового пациента с валидацией"""
        # Валидация обязательных полей
        required_fields = ['last_name', 'first_name', 'birthday', 'sex']
        for field in required_fields:
            if not patient_data.get(field):
                raise ValueError(f"Поле '{field}' обязательно для заполнения")

        # Валидация ФИО
        if not self._validate_name(patient_data['last_name']):
            raise ValueError("Фамилия должна содержать только буквы")
        
        if not self._validate_name(patient_data['first_name']):
            raise ValueError("Имя должно содержать только буквы")
        
        if patient_data.get('middle_name') and not self._validate_name(patient_data['middle_name']):
            raise ValueError("Отчество должно содержать только буквы")

        # Валидация даты рождения
        if not self._validate_birthdate(patient_data['birthday']):
            raise ValueError("Некорректная дата рождения")

        # Валидация пола
        if patient_data['sex'] not in ['M', 'F', 'male', 'female']:
            raise ValueError("Некорректное значение пола")
        
        # Приводим пол к формату Enum
        if patient_data['sex'] in ['male', 'M']:
            patient_data['sex'] = SexEnum.M
        else:
            patient_data['sex'] = SexEnum.F

        # Валидация email если указан
        if patient_data.get('email') and not self._validate_email(patient_data['email']):
            raise ValueError("Некорректный формат email")

        # Валидация телефона если указан
        if patient_data.get('phone') and not self._validate_phone(patient_data['phone']):
            raise ValueError("Некорректный формат телефона")

        # Создаем пациента
        return self.patient_repository.create_patient(patient_data)

    def get_patient(self, patient_id: int):
        """Получение пациента по ID"""
        return self.patient_repository.get_patient_by_id(patient_id)

    def get_doctor_patients(self, doctor_id: int):
        """Получение пациентов врача"""
        return self.patient_repository.get_patients_by_doctor(doctor_id)
    
    def get_all_patients(self):
        """Получение всех пациентов"""
        return self.patient_repository.get_all_patients()

    def search_patients(self, search_term: str = None):
        """Поиск пациентов"""
        return self.patient_repository.search_patients(search_term)

    def update_patient(self, patient_id: int, patient_data: dict):
        """Обновление данных пациента"""
        # Валидация полей если они присутствуют в обновлении
        if 'last_name' in patient_data and not self._validate_name(patient_data['last_name']):
            raise ValueError("Фамилия должна содержать только буквы")
        
        if 'first_name' in patient_data and not self._validate_name(patient_data['first_name']):
            raise ValueError("Имя должно содержать только буквы")
        
        if 'middle_name' in patient_data and patient_data['middle_name'] and not self._validate_name(patient_data['middle_name']):
            raise ValueError("Отчество должно содержать только буквы")

        if 'birthday' in patient_data and not self._validate_birthdate(patient_data['birthday']):
            raise ValueError("Некорректная дата рождения")

        if 'email' in patient_data and patient_data['email'] and not self._validate_email(patient_data['email']):
            raise ValueError("Некорректный формат email")

        if 'phone' in patient_data and patient_data['phone'] and not self._validate_phone(patient_data['phone']):
            raise ValueError("Некорректный формат телефона")

        return self.patient_repository.update_patient(patient_id, patient_data)

    def search_patients(self, search_term: str, doctor_id: int = None):
        """Поиск пациентов"""
        return self.patient_repository.search_patients(search_term, doctor_id)

    def _validate_name(self, name: str) -> bool:
        """Валидация имени (только буквы, дефисы, пробелы)"""
        if not name or not isinstance(name, str):
            return False
        return bool(re.match(r'^[a-zA-Zа-яА-ЯёЁ\s\-]+$', name.strip()))

    def _validate_birthdate(self, birthdate) -> bool:
        """Валидация даты рождения"""
        try:
            if isinstance(birthdate, str):
                birth_date = datetime.strptime(birthdate, '%Y-%m-%d').date()
            else:
                birth_date = birthdate
            
            # Проверяем что дата не в будущем
            if birth_date > datetime.now().date():
                return False
            
            # Проверяем разумный возраст (до 150 лет)
            age = datetime.now().year - birth_date.year
            if age > 150:
                return False
                
            return True
        except (ValueError, TypeError):
            return False

    def _validate_email(self, email: str) -> bool:
        """Валидация email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        """Валидация телефона (российский формат)"""
        # Упрощенная валидация для российских номеров
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        return len(cleaned_phone) >= 10 and cleaned_phone.startswith(('7', '8', '+7'))