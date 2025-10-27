import os
from datetime import timedelta

class ProxmoxConfig:
    NODE_NAME = os.getenv('PROXMOX_NODE_NAME', "pve-proxmox")
    HOST = os.getenv('PROXMOX_HOST', '192.168.1.138')
    PORT = os.getenv('PROXMOX_PORT', 8006)
    ROOT_USER = os.getenv('PROXMOX_ROOT_USER','root@pam')
    PASSWORD = os.getenv('PROXMOX_ROOT_PASSWORD', 'password')

class GuacamoleConfig:
    BASE_URL = os.getenv('GUACAMOLE_HOST', "http://192.168.1.140:8080/guacamole")
    USER = os.getenv('GUACAMOLE_USER', "guacadmin")
    PASSWORD = os.getenv('GUACAMOLE_PASSWORD', "guacadmin")
    PORT = 3306 # Default port for MySQL
    DATABASE_TYPE = "mysql"
    DATABASE_NAME = os.getenv('GUACAMOLE_DATABASE', "guacamole-db")

class FlaskAppConfig:
    # TODO: Change this to a more secure way of creating the secret key
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', os.urandom(32))

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './tmp/uploads')

    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = '/tmp/flask_session' # TODO: Cambiarlo a un ruta más segura / dentro del contenedor
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_USE_SIGNER = True

class Config:
    FLASK = FlaskAppConfig
    PROXMOX = ProxmoxConfig
    GUACAMOLE = GuacamoleConfig
