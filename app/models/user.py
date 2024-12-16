from flask_login import UserMixin
from .database import Database

class User(UserMixin):
    def __init__(self, id='admin'):
        self.id = id
        
    def get_id(self):
        return self.id 