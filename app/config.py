import os

class Config:
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHCT'
    JWT_SECRET_KEY = 'CHCT'  # Khóa bí mật JWT