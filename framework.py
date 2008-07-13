import cgi
import datetime
import time

def timestamp(t=None):
  if not t:
    t = datetime.datetime.now()
  return int(time.mktime(t.timetuple()))

def get_post_form(environ):
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

  formdata = {}
    
  fs = dict(fs)
  for key in fs:
    formdata[key] = str(fs[key].value)
      
  return formdata

class InputProcessed(object):
  def read(self):
    raise EOFError('The wsgi.input stream has already been consumed')
  readline = readlines = __iter__ = read
