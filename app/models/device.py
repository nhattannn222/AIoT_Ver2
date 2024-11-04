import bcrypt
from ..db import db  # Import db from db.py

class Device(db.Model):
    __tablename__ = 'device'
    __table_args__ = {'schema': 'chct'}
    deviceName = db.Column(db.String(100), primary_key=True)
    userName = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Store as VARCHAR(255)

    def to_dict(self, access_token=None):
        data = {
            'deviceName': self.deviceName,
            'userName': self.userName
        }
        if access_token:
            data['access_token'] = access_token
        return data

    def set_password(self, plain_password):
        # Hash the password and store it as a string
        hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
        self.password = hashed.decode('utf-8')  # Store as a string in the database

    def check_password(self, plain_password):
        # Convert the stored password back to bytes for comparison
        try:
            stored_hashed_password = self.password.encode('utf-8')  # Convert to bytes
            # Verify the password
            return bcrypt.checkpw(plain_password.encode('utf-8'), stored_hashed_password)
        except ValueError as e:
            # Log or print the error for debugging
            print(f"Error checking password: {e}")
            return False
