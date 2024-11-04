from flask import Blueprint, jsonify, request
from app.models.device import Device
from app.db import db  # Nhập đối tượng db để lưu dữ liệu
import bcrypt
import requests  # Import thư viện requests để gửi yêu cầu HTTP
from ..models.userInfo import UserInfo  # Điều chỉnh import theo cấu trúc của bạn

device_bp = Blueprint('device', __name__)

@device_bp.route('/', methods=['GET'])
def get_devices():
    devices = Device.query.all()
    return jsonify([{'deviceName': d.deviceName, 'userName': d.userName} for d in devices])
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

@device_bp.route('/<string:deviceId>', methods=['GET'])
def get_data_device(deviceId):
    try:
        # Data to send in the POST request
        post_data = [
            {
                "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
                "deviceId": deviceId,
                "tagName": "Temperature",
            },
            {
                "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
                "deviceId": deviceId,
                "tagName": "SpO2",
            },
            {
                "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
                "deviceId": deviceId,
                "tagName": "HeartRate",
            },
        ]

        # Send POST request to the external API
        external_api_url = "https://portal-datahub-24vn-ews.education.wise-paas.com/api/v1/RealData/raw"
        
        # Add Bearer Token to headers
        headers = {
            'Authorization': 'Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJjb3VudHJ5IjoiIiwiY3JlYXRpb25UaW1lIjoxNzI3NzU0NjUwLCJleHAiOjE3MzA2OTgxODYsImZpcnN0TmFtZSI6IlVzZXIiLCJpYXQiOjE3MzA2OTQ1ODYsImlkIjoiNjYzOWQ5MmEtY2NkNC00ZTI2LWI1MzctNjAzMjc2Mzk3MTI3IiwiaXNzIjoid2lzZS1wYWFzIiwibGFzdE1vZGlmaWVkVGltZSI6MTcyOTA0MzE5MCwibGFzdE5hbWUiOiJBcHAiLCJyZWZyZXNoVG9rZW4iOiI2YzEwNDIyOC05YTY1LTExZWYtYTg0Mi0wYTU4MGFlOTQ3MWUiLCJzdGF0dXMiOiJBY3RpdmUiLCJ1c2VybmFtZSI6IjIwMDUwMDEzQHN0dWRlbnQuYmR1LmVkdS52biJ9.ac1-I8XrZttiwpRGr5VhYMO5iOP8S9VwKMradnDYJPSp-olwVmNqOPowuFkoNQ_6lbkvPOeEsJ9LLV6991e2iw',  # Replace YOUR_ACCESS_TOKEN with your actual token
            'Content-Type': 'application/json'
        }
        
        # Use requests.post to send the request
        response = requests.post(external_api_url, json=post_data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors

        response_data = response.json()  # Get JSON data from the response

        # Process the response data
        mapped_data = [
            {
                **item,
                **get_health_status(item)  # Add health status info
            }
            for item in response_data
        ]
        
        data = combine_health_data(mapped_data)
        
        return jsonify(data), 200

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return jsonify({'error': "Đã xảy ra lỗi HTTP trong quá trình gọi API"}), 500
    except Exception as error:
        print("Lỗi trong quá trình gọi API:", error)
        return jsonify({'error': "Đã xảy ra lỗi trong quá trình gọi API"}), 500

def get_health_status(item):
    # Return health status based on the tagName
    tag_name = item.get("tagName")
    value = item.get("value")  # Get the value from the item
    try:
        value = float(value)  # Attempt to convert to float for comparison
    except (ValueError, TypeError):  # Catch errors in conversion
        value = 0  # Default to 0 if conversion fails

    if tag_name == "Temperature":
        return {
            "ketQuaNhietDo": "Nhiệt độ " +
                ("Bình thường" if 36 <= value <= 38 else "Cảm lạnh" if value < 36 else "Sốt")
        }
    elif tag_name == "SpO2":
        return {
            "ketQuaSpO2": "Chỉ số SpO2 " +
                ("Bình thường" if 96 <= value <= 100 else "Cần theo dõi" if 90 <= value < 96 else "Nguy hiểm")
        }
    elif tag_name == "HeartRate":
        return {
            "ketQuaNhipTim": "Nhịp tim " +
                ("Bình thường" if 60 <= value <= 100 else "Không bình thường")
        }
    else:
        return {}


def combine_health_data(data):
    combined = {}
    for item in data:
        device_id = item["deviceId"]
        node_id = item["nodeId"]
        ts = item.get("ts")
        tag_name = item["tagName"]
        value = item["value"]

        # Combine data while avoiding duplicating tagName in the output
        combined.update({
            "deviceId": device_id,
            "nodeId": node_id,
            "ts": ts,
            tag_name: value,  # Use the tagName as a key for the value
            **get_health_status(item),  # Include health status
        })

    return combined