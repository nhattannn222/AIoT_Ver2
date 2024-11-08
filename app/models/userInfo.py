from ..db import db  # Import db from db.py

class UserInfo(db.Model):
    __tablename__ = 'userinfo'
    __table_args__ = {'schema': 'chct'}

    # Define primary key as a composite key
    deviceName = db.Column(db.String(100), db.ForeignKey('chct.device.deviceName'), primary_key=True)
    parentName = db.Column(db.String(100), nullable=False)
    childName = db.Column(db.String(100), nullable=True)
    phoneNumber = db.Column(db.String(20), nullable=False, primary_key=True)  # Ensure this is unique if required
    email = db.Column(db.String(100), nullable=True)
    childWeight = db.Column(db.Float, nullable=True)
    childHeight = db.Column(db.Float, nullable=True)
    childBirthday = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)

    # Define a relationship with the Device model
    device = db.relationship('Device', backref='user_info', lazy=True)

    def to_dict(self):
        return {
            'deviceName': self.deviceName,
            'parentName': self.parentName,
            'childName': self.childName,
            'phoneNumber': self.phoneNumber,
            'email': self.email,
            'childWeight': self.childWeight,
            'childHeight': self.childHeight,
            'childBirthday': self.childBirthday,
            'gender': self.gender
        }
