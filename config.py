
class Config(object):
    TEMPLATES_AUTO_RELOAD = True
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"
    SQLALCHEMY_DATABASE_URI = "sqlite:///base.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ECHO = True
    FLASK_ADMIN_SWATCH = 'cerulean'
    UPLOAD_FOLDER = 'static'
    MAX_CONTENT_PATH = 16*1000*1000
    THUMBNAIL_SIZE = 256, 256
    QUOTE_SAMPLE_LENGHT = 10
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    LEFT_CURRENT = 2
    RIGHT_CURRENT = 3
    ITEMS_PER_PAGE = 12
