import os

class Config():
    FLASK_APP=os.environ.get('FLASK_APP')
    DEBUG=os.environ.get('FLASK_ENV') == 'development'
    SECRET_KEY=os.environ.get('SECRET_KEY')