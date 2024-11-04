from flask import request, jsonify
from . import user_bp
from ..models.userInfo import UserInfo
from app import db  # Nhập db nếu cần thiết

@user_bp.route('/', methods=['GET'])
def get_users():
    users = UserInfo.query.all()
    return jsonify([{'deviceName': u.deviceName, 'parentName': u.parentName} for u in users])

