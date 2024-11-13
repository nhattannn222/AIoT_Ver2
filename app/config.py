import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://b1d72ac3-a069-4182-825b-809fe72df8c9:JSi3MYRL2gkAt8yYuoUoh9Ssu@52.163.226.41:5432/e4f1625f-498b-457f-8718-8d8f03cc9ce0'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHCT'
    JWT_SECRET_KEY = 'CHCT'  # Khóa bí mật JWT