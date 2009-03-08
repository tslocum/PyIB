import threading

class SettingsLocal(threading.local):
  USING_SQLALCHEMY = False # If SQLAlchemy is installed, set to True to use it

  # Ignore these
  BOARD = None
  MODBROWSE = False

class Settings(object):
  NAME = "not7chan"
  DOMAIN = ".n7c.org"
  ROOT_DIR = "/home/tj9991/img.n7c.org/"
  HOME_URL = "http://n7c.org/"
  BOARDS_URL = "http://img.n7c.org/"
  CGI_URL = "http://cgi.n7c.org/" # Path to folder containing the script
  MAX_PROGRAM_THREADS = 10 # Maximum threads this Python application can start (must be 2 or greater)
                           # Setting this too high can cause the program to terminate before finishing
  
  BANNER_URL = "http://n7c.org/banners/banner.php"
  BANNER_WIDTH = 300
  BANNER_HEIGHT = 100

  DATABASE_HOST = "localhost"
  DATABASE_USERNAME = ""
  DATABASE_PASSWORD = ""
  DATABASE_DB = ""
  # The following two entries apply only if USING_SQLALCHEMY is set to True
  DATABASE_POOL_SIZE = 5 # Initial number of database connections
  DATABASE_POOL_OVERFLOW = 21 # Maximum number of database connections

  MAX_THREADS = 100
  THREADS_SHOWN_ON_FRONT_PAGE = 10
  REPLIES_SHOWN_ON_FRONT_PAGE = 5
  SECONDS_BETWEEN_NEW_THREADS = 30
  SECONDS_BETWEEN_REPLIES = 10

  SHOW_NAVBAR = False # If you set this to True, edit navbar.html
  DEFAULT_STYLE = "Futaba" # Futaba or Burichan
  
  IMAGE_SIZE_UNIT = "B" # B or KB
  MAX_IMAGE_SIZE_BYTES = 1048576
  MAX_IMAGE_SIZE_DISPLAY = "1 MB"
  MAX_DIMENSION_FOR_OP_IMAGE = 200
  MAX_DIMENSION_FOR_REPLY_IMAGE = 125

  USE_MARKDOWN = False
  
  _ = SettingsLocal() # Used when running multiple threads

