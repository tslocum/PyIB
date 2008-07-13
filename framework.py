import cgi
import datetime
import time

def timestamp(t=None):
  """
  Create MySQL-safe timestamp from the datetime t if provided, otherwise create
  the timestamp from datetime.now()
  """
  if not t:
    t = datetime.datetime.now()
  return int(time.mktime(t.timetuple()))

def get_post_form(environ):
  """
  Process input sent to WSGI through a POST method and output it in an easy to
  retrieve format: dictionary of dictionaries in the format of {key: value}
  """
  wsgi_input = environ['wsgi.input']
  post_form = environ.get('wsgi.post_form')
  if (post_form is not None
    and post_form[0] is wsgi_input):
    return post_form[2]
  # This must be done to avoid a bug in cgi.FieldStorage
  environ.setdefault('QUERY_STRING', '')
  fs = cgi.FieldStorage(fp=wsgi_input,
                        environ=environ,
                        keep_blank_values=1)
  new_input = InputProcessed()
  post_form = (new_input, wsgi_input, fs)
  environ['wsgi.post_form'] = post_form
  environ['wsgi.input'] = new_input
  
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
