from flask import Blueprint, jsonify, request
from app.models.device import Device
from app.db import db  # Nhập đối tượng db để lưu dữ liệu
import bcrypt
import requests  # Import thư viện requests để gửi yêu cầu HTTP
from ..models.userInfo import UserInfo  # Điều chỉnh import theo cấu trúc của bạn
from flask import Blueprint, jsonify, request
import joblib
import numpy as np
import pandas as pd
import os
from collections import defaultdict
from datetime import datetime,timedelta

device_bp = Blueprint('device', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
svm_model_path = os.path.join(current_dir, 'model_ai/svm_model.pkl')
preprocessor_path = os.path.join(current_dir, 'model_ai/preprocessor.pkl')
label_encoder_path = os.path.join(current_dir, 'model_ai/label_encoder.pkl')

svm_model = joblib.load(svm_model_path)
preprocessor = joblib.load(preprocessor_path)
label_encoder = joblib.load(label_encoder_path)

EIToken = ""
username = ""
password = ""
API_LOGIN_URL = "https://portal-datahub-24vn-ews.education.wise-paas.com/api/v1/Auth"

def checkToken():
    global EIToken  # Sử dụng biến toàn cục EIToken
    headerscheckToken = {
            'Authorization': f'Bearer {EIToken}',  # Replace YOUR_ACCESS_TOKEN with your actual token
            'Content-Type': 'application/json'
        }

    checktoken = requests.get("https://portal-datahub-24vn-ews.education.wise-paas.com/api/v1/Nodes/list?orgName=CHCT",headers=headerscheckToken)
    if(checktoken.status_code == 200):
        return 
    else: 
        payload = {
            'username': username,
            'password': password,
            'redirectUri': "https://portal-datahub-24vn-ews.education.wise-paas.com"
        }
        
        # Gửi yêu cầu đăng nhập
        response = requests.post(API_LOGIN_URL, data=payload)
        
        if response.status_code == 200:
            # Token sẽ được lưu trong cookie, có thể kiểm tra trong response.cookies
            EIToken = response.cookies.get("EIToken")  # Lấy token từ cookie
            print(f"Token mới: {EIToken}")
        else:
            print(f"Đăng nhập không thành công. Mã lỗi: {response.status_code}")

@device_bp.route('/<string:deviceId>', methods=['GET'])
def get_data_device(deviceId):
    try:
        checkToken()
        userInfo = UserInfo.query.filter_by(deviceName=deviceId).first()

        if not userInfo:
            return jsonify({'message': 'Can not find user with this deviceId.'}), 400
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
            {
                "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
                "deviceId": deviceId,
                "tagName": "Accelerometer",
            },
        ]

        # Send POST request to the external API
        external_api_url = "https://portal-datahub-24vn-ews.education.wise-paas.com/api/v1/RealData/raw"
        
        # Add Bearer Token to headers
        headers = {
            'Authorization': f'Bearer {EIToken}',  # Replace YOUR_ACCESS_TOKEN with your actual token
            'Content-Type': 'application/json'
        }
        
        # Use requests.post to send the request
        response = requests.post(external_api_url, json=post_data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors

        if response.status_code == 401:
            checkToken()

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
        
        age = datetime.now().year - userInfo.childBirthday.year
        gender = userInfo.gender
        height = userInfo.childHeight
        weight = userInfo.childWeight

        heart_rate = data['HeartRate']
        spo2 = data['SpO2']
        temperature = data['Temperature']
        accelerometer = data['Accelerometer']

        feature_values = pd.DataFrame([[age, gender, height, weight, heart_rate, spo2, temperature, accelerometer]], columns=['age', 'gender', 'height', 'weight', 'heart_rate', 'spo2', 'temperature', 'accelerometer'])
        feature_values_processed = preprocessor.transform(feature_values)
        prediction = svm_model.predict(feature_values_processed)
        decoded_prediction = label_encoder.inverse_transform(prediction)

        prediction_result = {
            'age': age,
            'gender': gender,
            'height': height,
            'weight': weight,
            'heart_rate': heart_rate,
            'spo2': spo2,
            'temperature': temperature,
            'accelerometer': accelerometer,
            'prediction': decoded_prediction[0]
        }
    
        file_path = 'children_health_predict.csv'
        try:
            df = pd.read_csv(file_path)
            new_df = pd.DataFrame([prediction_result])
            df = pd.concat([df, new_df], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([prediction_result])
        df.to_csv(file_path, index=False)

        data['prediction'] = prediction_result['prediction']
        data['age'] = age
        data['gender']= gender
        data['height'] = userInfo.childHeight
        data['weight'] = userInfo.childWeight

        
        return jsonify(data), 200


    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return jsonify({'error': "Đã xảy ra lỗi HTTP trong quá trình gọi API"}), 500
    except Exception as error:
        print("Lỗi trong quá trình gọi API:", error)
        return jsonify({'error': "Đã xảy ra lỗi trong quá trình gọi API"}), 500

@device_bp.route('/location/<string:deviceId>', methods=['GET'])
def get_location(deviceId):
    try:
        checkToken()
        userInfo = UserInfo.query.filter_by(deviceName=deviceId).first()

        if not userInfo:
            return jsonify({'message': 'Can not find user with this deviceId.'}), 400
        # Data to send in the POST request
        post_data = [
            {
                "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
                "deviceId": deviceId,
                "tagName": "Longitude"
            },
            {
                "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
                "deviceId": deviceId,
                "tagName": "Latitude"
            }
        ]

        # Send POST request to the external API
        external_api_url = "https://portal-datahub-24vn-ews.education.wise-paas.com/api/v1/RealData/raw"
        
        # Add Bearer Token to headers
        headers = {
            'Authorization': f'Bearer {EIToken}',  # Replace YOUR_ACCESS_TOKEN with your actual token
            'Content-Type': 'application/json'
        }
        
        # Use requests.post to send the request
        response = requests.post(external_api_url, json=post_data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors

        if response.status_code == 401:
            checkToken()

        response_data = response.json()  # Get JSON data from the response

        
        
        data = combine_health_data(response_data)
        
       
        
        return jsonify(data), 200


    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return jsonify({'error': "Đã xảy ra lỗi HTTP trong quá trình gọi API"}), 500
    except Exception as error:
        print("Lỗi trong quá trình gọi API:", error)
        return jsonify({'error': "Đã xảy ra lỗi trong quá trình gọi API"}), 500

@device_bp.route('/notify/<string:deviceId>', methods=['GET'])
def notify(deviceId):
    try:
        checkToken()
        userInfo = UserInfo.query.filter_by(deviceName=deviceId).first()

        if not userInfo:
            return jsonify({'message': 'Can not find user with this deviceId.'}), 400
        # Data to send in the POST request
        post_data = {
        "tags": [
            {
            "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
            "deviceId": deviceId,
            "tagName": "Temperature"
            },
        {
            "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
            "deviceId": deviceId,
            "tagName": "SpO2"
            },
        {
            "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
            "deviceId": deviceId,
            "tagName": "HeartRate"
            },
        {
            "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
            "deviceId": deviceId,
            "tagName": "Accelerometer"
            }
        ],
            "startTs": "2024-11-08T02:16:48.912Z",
            "endTs": "2024-11-08T02:18:48.912Z",
            # "startTs": (datetime.now() - timedelta(minutes=3)).isoformat() + "Z",
            # "endTs": datetime.now().isoformat() + "Z",
            "desc": "true",
            "count": 20
        }

        # Send POST request to the external API
        external_api_url = "https://portal-datahub-24vn-ews.education.wise-paas.com/api/v1/HistData/raw"
        
        # Add Bearer Token to headers
        headers = {
            'Authorization': f'Bearer {EIToken}',  # Replace YOUR_ACCESS_TOKEN with your actual token
            'Content-Type': 'application/json'
        }
        
        # Use requests.post to send the request
        response = requests.post(external_api_url, json=post_data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors

        if response.status_code == 401:
            checkToken()

        response_data = response.json()  # Get JSON data from the response

        data = merge_data(response_data)

        age = datetime.now().year - userInfo.childBirthday.year
        gender = userInfo.gender
        height = userInfo.childHeight
        weight = userInfo.childWeight
        data_for_model = []

        # Duyệt qua từng record trong danh sách dữ liệu
        for record in data:
            # Lấy các thuộc tính cần thiết từ từng bản ghi
            heart_rate = record.get("HeartRate")
            spo2 = record.get("SpO2")
            temperature = record.get("Temperature")
            accelerometer = record.get("Accelerometer")
            ts = record.get("ts")  # Lấy giá trị thời gian (timestamp) từ bản ghi

            # Ghi lại vào mảng
            data_for_model.append({
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
                "heart_rate": heart_rate,
                "spo2": spo2,
                "temperature": temperature,
                "accelerometer": accelerometer,
                "ts": ts  # Thêm thời gian vào mảng dữ liệu
            })

        # Mảng chứa kết quả dự đoán
        prediction_results = []

        # Đường dẫn file CSV để lưu kết quả
        file_path = 'children_health_predict.csv'

        # Duyệt qua từng bản ghi trong data_for_model
        for record in data_for_model:
            # Lấy các giá trị từ bản ghi
            age = record['age']
            gender = record['gender']
            height = record['height']
            weight = record['weight']
            heart_rate = record['heart_rate']
            spo2 = record['spo2']
            temperature = record['temperature']
            accelerometer = record['accelerometer']
            ts = record['ts']  # Lấy thời gian (timestamp) từ record

            # Chuyển dữ liệu vào DataFrame
            feature_values = pd.DataFrame(
                [[age, gender, height, weight, heart_rate, spo2, temperature, accelerometer]], 
                columns=['age', 'gender', 'height', 'weight', 'heart_rate', 'spo2', 'temperature', 'accelerometer']
            )

            # Xử lý dữ liệu trước khi đưa vào mô hình
            feature_values_processed = preprocessor.transform(feature_values)

            # Dự đoán kết quả với mô hình SVM
            prediction = svm_model.predict(feature_values_processed)
            decoded_prediction = label_encoder.inverse_transform(prediction)

            # Tạo kết quả dự đoán cho bản ghi hiện tại
            prediction_result = {
                'age': age,
                'gender': gender,
                'height': height,
                'weight': weight,
                'heart_rate': heart_rate,
                'spo2': spo2,
                'temperature': temperature,
                'accelerometer': accelerometer,
                'prediction': decoded_prediction[0],
                'ts': ts  # Lưu lại thời gian (timestamp) trong kết quả dự đoán
            }

            # Thêm kết quả vào mảng
            prediction_results.append(prediction_result)

        # Ghi kết quả vào file CSV
        try:
            # Đọc file CSV hiện có nếu tồn tại
            df = pd.read_csv(file_path)
            new_df = pd.DataFrame(prediction_results)
            df = pd.concat([df, new_df], ignore_index=True)
        except FileNotFoundError:
            # Tạo file CSV mới nếu chưa tồn tại
            df = pd.DataFrame(prediction_results)

        notification_results = []
        for index, result in enumerate(prediction_results):
            notification = {}
            ts = result['ts']  # Lấy thời gian từ kết quả dự đoán

            # Convert ts to datetime and add 8 hours
            ts_datetime = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")  # Use ISO 8601 format
            adjusted_ts = ts_datetime + timedelta(hours=8)
            adjusted_ts_str = adjusted_ts.strftime("%Y-%m-%d %H:%M:%S")  # Format as needed

            if result['prediction'] == 'danger':
                notification = {
                    'id': str(index + 1),
                    'type': 'Nguy hiểm',
                    'message': 'Bé có trạng thái nguy hiểm vì nhiệt độ cao hoặc dấu hiệu nhịp tim bất thường',
                    'time': adjusted_ts_str,  # Use adjusted timestamp
                    'color': 'red',
                    'read': False
                }
            elif result['prediction'] == 'warning':
                notification = {
                    'id': str(index + 1),
                    'type': 'Cảnh báo',
                    'message': 'Vị trí của bé đã thay đổi hoặc nhịp tim có dấu hiệu không ổn định',
                    'time': adjusted_ts_str,  # Use adjusted timestamp
                    'color': 'yellow',
                    'read': False
                }
            else:
                notification = {
                    'id': str(index + 1),
                    'type': 'Bình thường',
                    'message': 'Trạng thái của bé đang bình thường',
                    'time': adjusted_ts_str,  # Use adjusted timestamp
                    'color': 'green',
                    'read': False
                }
            
            notification_results.append(notification)
        # Trả về thông tin thông báo
        return jsonify(notification_results), 200

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return jsonify({'error': "Đã xảy ra lỗi HTTP trong quá trình gọi API"}), 500
    except Exception as error:
        print("Lỗi trong quá trình gọi API:", error)
        return jsonify({'error': "Đã xảy ra lỗi trong quá trình gọi API"}), 500

@device_bp.route('/chart/<string:deviceId>', methods=['GET'])
def chart(deviceId):
    try:
        checkToken()
        userInfo = UserInfo.query.filter_by(deviceName=deviceId).first()

        if not userInfo:
            return jsonify({'message': 'Can not find user with this deviceId.'}), 400
        # Data to send in the POST request
        post_data = {
        "tags": [
            {
            "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
            "deviceId": deviceId,
            "tagName": "Temperature"
            },
        {
            "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
            "deviceId": deviceId,
            "tagName": "SpO2"
            },
        {
            "nodeId": "8bab95f7-be6d-46c1-b55b-cfbe9e089c6a",
            "deviceId": deviceId,
            "tagName": "HeartRate"
            }
        ],
            "startTs": "2024-11-08T02:16:48.912Z",
            "endTs": "2024-11-08T02:18:48.912Z",
            # "startTs": (datetime.now() - timedelta(minutes=3)).isoformat() + "Z",
            # "endTs": datetime.now().isoformat() + "Z",
            "desc": "true",
            "count": 20
        }

        # Send POST request to the external API
        external_api_url = "https://portal-datahub-24vn-ews.education.wise-paas.com/api/v1/HistData/raw"
        
        # Add Bearer Token to headers
        headers = {
            'Authorization': f'Bearer {EIToken}',  # Replace YOUR_ACCESS_TOKEN with your actual token
            'Content-Type': 'application/json'
        }
        
        # Use requests.post to send the request
        response = requests.post(external_api_url, json=post_data, headers=headers)
        response.raise_for_status()  # Check for HTTP errors

        if response.status_code == 401:
            checkToken()

        response_data = response.json()  # Get JSON data from the response

        data = merge_data(response_data)
        

        
        return jsonify(data), 200

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return jsonify({'error': "Đã xảy ra lỗi HTTP trong quá trình gọi API"}), 500
    except Exception as error:
        print("Lỗi trong quá trình gọi API:", error)
        return jsonify({'error': "Đã xảy ra lỗi trong quá trình gọi API"}), 500


def merge_data(data):
    # Sử dụng defaultdict để lưu trữ giá trị theo timestamp
    merged_data = defaultdict(dict)
    
    # Duyệt qua từng đối tượng trong danh sách
    for item in data:
        tag_name = item['tagName']
        
        # Duyệt qua từng giá trị trong 'values'
        for value in item['values']:
            ts = value['ts']
            
            merged_data[ts][tag_name] = value['value']
    
    # Chuyển defaultdict sang danh sách kết quả
    result = []
    for ts, values in merged_data.items():
        merged_record = {'ts': ts}
        merged_record.update(values)
        result.append(merged_record)
    
    # Sắp xếp kết quả theo timestamp (giảm dần)
    result.sort(key=lambda x: x['ts'], reverse=True)
    
    return result

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

