import tenjin
from tenjin.helpers import * # Used when templating

from settings import Settings
from database import *

def renderTemplate(template, template_values={}):
  """
  Run Tenjin on the supplied template name, with the extra values
  template_values (if supplied)
  """
  global db
  
  board = Settings._BOARD
  if Settings._UNIQUE_USER_POSTS == 0:
    unique_user_posts = FetchOne('SELECT COUNT(DISTINCT(`ip`)) FROM `posts` WHERE `boardid` = ' + board['id'], 0)
    Settings._UNIQUE_USER_POSTS = unique_user_posts[0]
  engine = tenjin.Engine()

  values = {
    'title': 'n7c',
    'board': board['dir'],
    'board_name': board['name'],
    'is_page': 'false',
    'replythread': 0,
    'home_url': Settings.HOME_URL,
    'boards_url': Settings.BOARDS_URL,
    'cgi_url': Settings.CGI_URL,
    'banner_url': Settings.BANNER_URL,
    'banner_width': Settings.BANNER_WIDTH,
    'banner_height': Settings.BANNER_HEIGHT,
    'anonymous': Settings.ANONYMOUS,
    'forced_anonymous': Settings.FORCED_ANONYMOUS,
    'disable_subject': Settings.DISABLE_SUBJECT,
    'tripcode_character': Settings.POST_TRIPCODE_CHARACTER,
    'disable_subject': Settings.DISABLE_SUBJECT,
    'MAX_FILE_SIZE': Settings.MAX_IMAGE_SIZE_BYTES,
    'maxsize_display': Settings.MAX_IMAGE_SIZE_DISPLAY,
    'maxdimensions': Settings.MAX_DIMENSION_FOR_OP_IMAGE,
    'unique_user_posts': Settings._UNIQUE_USER_POSTS,
    'page_navigator': '',
  }
  values.update(template_values)
  
  return engine.render('templates/' + template, values)
