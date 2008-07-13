class Settings(object):
  APP_NAME = 'pyib' # App name, as displayed in the app engine panel
  
  ROOT_DIR = '/home/.cassandra/tj9991/img.n7c.org/'
  HOME_URL = 'http://n7c.org/'
  BOARDS_URL = 'http://img.n7c.org/'
  CGI_URL = 'http://cgi.n7c.org/' # Path to folder containing the script
  
  BANNER_URL = 'http://n7c.org/banners/banner.php'
  BANNER_WIDTH = 300
  BANNER_HEIGHT = 100

  DATABASE_HOST = 'localhost'
  DATABASE_USERNAME = ''
  DATABASE_PASSWORD = ''
  DATABASE_DB = ''

  MAX_THREADS = 100
  THREADS_SHOWN_ON_FRONT_PAGE = 10
  REPLIES_SHOWN_ON_FRONT_PAGE = 5
  SECONDS_BETWEEN_NEW_THREADS = 30
  SECONDS_BETWEEN_REPLIES = 10

  MAX_IMAGE_SIZE_BYTES = 1048576
  MAX_IMAGE_SIZE_DISPLAY = '1 MB'
  MAX_DIMENSION_FOR_OP_IMAGE = 200
  MAX_DIMENSION_FOR_REPLY_IMAGE = 125
  MAX_DIMENSION_FOR_IMAGE_CATALOG = 50

  ANONYMOUS = '' # Name to display when no name is entered in the name field.  Set to an empty string to completely remove names from post display
  POST_TRIPCODE_CHARACTER = '!'
  FORCED_ANONYMOUS = True # If set, all posts will be flagged as anonymous, and will not display a name or tripcode
  DISABLE_SUBJECT = True # If set, users will not be allowed to enter subjects for their posts

  # Non-editable configuration (beginning with an underscore) follows
  _ADMINISTRATOR_VIEW = False # When the script sets this to True, special administrator commands will be visible, and pages will not be retrieved from/stored in the cache
  _BOARD = False
  _UNIQUE_USER_POSTS = 0
