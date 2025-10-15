from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()

class SexEnum(enum.Enum):
    M = 'M'
    F = 'F'

class ConsultationStatusEnum(enum.Enum):
    draft = 'draft'
    active = 'active'
    completed = 'completed'
    canceled = 'canceled'

class Doctor(Base):
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    password = Column(String(255), nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    consultations = relationship("Consultation", back_populates="doctor")

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    birthday = Column(Date, nullable=False)
    sex = Column(Enum(SexEnum), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(String(500))
    allergies = Column(String(1000))
    chronic_diseases = Column(String(1000))
    current_medications = Column(String(1000))
    family_anamnes = Column(String(1000))
    notes = Column(String(2000))
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    consultations = relationship("Consultation", back_populates="patient")

class Consultation(Base):
    __tablename__ = 'consultations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    consultation_date = Column(DateTime, default=datetime.utcnow)
    sub_graph_find_diagnosis = Column(JSON)  # JSON дерево диагностики
    final_diagnosis = Column(String(500))
    status = Column(Enum(ConsultationStatusEnum), default=ConsultationStatusEnum.draft)
    notes = Column(String(2000))
    
    # Связи
    doctor = relationship("Doctor", back_populates="consultations")
    patient = relationship("Patient", back_populates="consultations")