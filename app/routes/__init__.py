from flask import Blueprint

# Khởi tạo các blueprint
device_bp = Blueprint('device', __name__)
user_bp = Blueprint('user', __name__)

# Nhập các route từ các tệp tương ứng
from .device_routes import *
from .userInfo_routes import *
