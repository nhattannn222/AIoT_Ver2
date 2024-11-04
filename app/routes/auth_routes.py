from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from app.models.device import Device
from app.db import db  # Nhập đối tượng db để lưu dữ liệu
import bcrypt
import requests  # Import thư viện requests để gửi yêu cầu HTTP
from ..models.userInfo import UserInfo  # Điều chỉnh import theo cấu trúc của bạn

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('userName')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    device = Device.query.filter_by(userName=username).first()

    if device and device.check_password(password):
        access_token = create_access_token(identity={'userName': username})
        return jsonify(device.to_dict(access_token=access_token)), 200
    else:
        return jsonify({'message': 'Invalid username or password.'}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    device_name = data.get('deviceName')
    username = data.get('userName')
    password = data.get('password')
    parent_name = data.get('parentName')
    phone_number = data.get('phoneNumber')
    child_name = data.get('childName')
    email = data.get('email')
    child_weight = data.get('childWeight')
    child_height = data.get('childHeight')
    child_birthday = data.get('childBirthday')

    if not all([device_name, username, password, parent_name, phone_number]):
        return jsonify({'message': 'Missing required fields.'}), 400

    existing_device = Device.query.filter_by(deviceName=device_name).first()
    if existing_device:
        return jsonify({'message': 'Device already exists.'}), 400

    new_device = Device(deviceName=device_name, userName=username)
    new_device.set_password(password)

    new_user_info = UserInfo(
        deviceName=device_name,
        parentName=parent_name,
        childName=child_name,
        phoneNumber=phone_number,
        email=email,
        childWeight=child_weight,
        childHeight=child_height,
        childBirthday=child_birthday
    )

    try:
        db.session.add(new_device)
        db.session.add(new_user_info)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error during registration.', 'error': str(e)}), 500

    return jsonify({'message': 'Registration successful.'}), 201

