import cgi
import datetime
import time
import pickle
import _mysql
from Cookie import SimpleCookie

from settings import Settings
from database import *

def setBoard(dir):
  """
  Sets the board which the script is operating on by filling Settings._BOARD
  with the data from the db.  Once the data is set, the configuration field from
  the database is unpickled and placed in a pseudo-field called settings.
  All settings have a default value which will remain that way until the script
  changes and updates the board by calling updateBoardSettings()
  This allows new settings to be added for each board without requiring any SQL
  queries to be ran
  """
  board = FetchOne("SELECT * FROM `boards` WHERE `dir` = '" + _mysql.escape_string(dir) + "' LIMIT 1")
  
  board['settings'] = {
    'anonymous': 'Anonymous',
    'forced_anonymous': False,
    'disable_subject': False,
    'tripcode_character': '!',
  }

  if board['configuration'] != '':
    configuration = pickle.loads(board['configuration'])
    board['settings'].update(configuration)
    
  Settings._BOARD = board
  Settings._UNIQUE_USER_POSTS = 0
  
  return board
  
def updateBoardSettings():
  """
  Pickle the board's settings and store it in the configuration field
  """
  board = Settings._BOARD
  configuration = pickle.dumps(board['settings'])
  
  db.query("UPDATE `boards` SET `configuration` = '" + _mysql.escape_string(configuration) + "' WHERE `id` = " + board['id'] + " LIMIT 1")

def timestamp(t=None):
  """
  Create MySQL-safe timestamp from the datetime t if provided, otherwise create
  the timestamp from datetime.now()
  """
  if not t:
    t = datetime.datetime.now()
  return int(time.mktime(t.timetuple()))

def formatTimestamp(t):
  """
  Format a timestamp to a readable date
  """
  return datetime.datetime.fromtimestamp(int(t)).strftime("%y/%m/%d(%a)%H:%M:%S")

def timeTaken(time_start, time_finish):
  return str(round(time_finish - time_start, 2))

def getFormData(self):
  """
  Process input sent to WSGI through a POST method and output it in an easy to
  retrieve format: dictionary of dictionaries in the format of {key: value}
  """
  wsgi_input = self.environ['wsgi.input']
  post_form = self.environ.get('wsgi.post_form')
  if (post_form is not None
    and post_form[0] is wsgi_input):
    return post_form[2]
  # This must be done to avoid a bug in cgi.FieldStorage
  self.environ.setdefault('QUERY_STRING', '')
  fs = cgi.FieldStorage(fp=wsgi_input,
                        environ=self.environ,
                        keep_blank_values=1)
  new_input = InputProcessed()
  post_form = (new_input, wsgi_input, fs)
  self.environ['wsgi.post_form'] = post_form
  self.environ['wsgi.input'] = new_input
  
  """
  Pre-"list comprehension" code (benchmarked as being five times slower):
  formdata = {}
  fs = dict(fs)
  for key in fs:
    formdata[key] = str(fs[key].value)
  """
  
  formdata = dict([(key, fs[key].value) for key in dict(fs)])
  
  #import sys
  #sys.exit(repr(formdata))
  
  return formdata

class InputProcessed(object):
  def read(self):
    raise EOFError('The wsgi.input stream has already been consumed')
  readline = readlines = __iter__ = read
  
def setCookie(self, key, value='', max_age=None, expires=None, path='/', domain=None, secure=None):
  """
  Copied from Colubrid
  """
  if self._cookies is None:
    self._cookies = SimpleCookie()
  self._cookies[key] = value
  if not max_age is None:
    self._cookies[key]['max-age'] = max_age
  if not expires is None:
    if isinstance(expires, basestring):
      self._cookies[key]['expires'] = expires
      expires = None
    elif isinstance(expires, datetime):
      expires = expires.utctimetuple()
    elif not isinstance(expires, (int, long)):
      expires = datetime.datetime.gmtime(expires)
    else:
      raise ValueError('datetime or integer required')
    if not expires is None:
      now = datetime.datetime.gmtime()
      month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
               'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][now.tm_mon - 1]
      day = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
             'Friday', 'Saturday', 'Sunday'][expires.tm_wday]
      date = '%02d-%s-%s' % (
          now.tm_mday, month, str(now.tm_year)[-2:]
      )
      d = '%s, %s %02d:%02d:%02d GMT' % (day, date, now.tm_hour,
                                         now.tm_min, now.tm_sec)
      self._cookies[key]['expires'] = d
  if not path is None:
    self._cookies[key]['path'] = path
  if not domain is None:
    if domain != 'THIS':
      self._cookies[key]['domain'] = domain
  else:
    self._cookies[key]['domain'] = Settings.DOMAIN
  if not secure is None:
    self._cookies[key]['secure'] = secure

def deleteCookie(self, key):
  """
  Copied from Colubrid
  """
  if self._cookies is None:
    self._cookies = SimpleCookie()
  if not key in self._cookies:
    self._cookies[key] = ''
  self._cookies[key]['max-age'] = 0
