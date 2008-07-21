#!/usr/bin/python2.4
#!/usr/bin/env python

import time
import datetime
import cgi
import _mysql
from Cookie import SimpleCookie

import tenjin
import manage
from database import *
from settings import Settings
from framework import *
from formatting import *
from post import *
from img import *

class pyib(object):
  def __init__(self, environ, start_response):
    global db
    self.environ = environ
    self.start = start_response
    self.formdata = getFormData(self)
    self.output = ''
    self.handleRequest()

    try:
      self.run()
    except Exception, message:
      self.output += renderTemplate('error.html', {'error': message, 'navbar': False})
  
  def __iter__(self):
    self.handleResponse()
    self.start('200 OK', self.headers)
    yield self.output
  
  def run(self):
    if self.environ['PATH_INFO'] == '/post':
      try:
        if self.formdata['board']:
          board = FetchOne("SELECT * FROM `boards` WHERE `dir` = '" + _mysql.escape_string(self.formdata['board']) + "' LIMIT 1")
          if not board:
            raise Exception
          board = setBoard(self.formdata['board'])
        else:
          raise Exception
      except:
        raise Exception, 'Invalid board supplied'
  
      post = {
        'name': '',
        'tripcode': '',
        'email': '',
        'subject': '',
        'message': '',
        'password': '',
        'parent': 0,
        'file': '',
        'file_hex': '',
        'file_mime': '',
        'file_original': '',
        'file_size': 0,
        'file_size_formatted': '',
        'thumb': '',
        'image_width': 0,
        'image_height': 0,
        'thumb_width': 0,
        'thumb_height': 0,
        'thumb_catalog_width': 0,
        'thumb_catalog_height': 0,
        'ip': self.environ['REMOTE_ADDR'],
      }
      
      try:
        parent = cgi.escape(self.formdata['parent']).strip()
        try:
          parent_post = FetchOne('SELECT COUNT(*) FROM `posts` WHERE `id` = ' + parent + ' AND `parentid` = 0 AND `boardid` = ' + board['id'] + ' LIMIT 1', 0)
          if int(parent_post[0]) > 0:
            post['parent'] = parent
          else:
            raise Exception
        except:
          raise Exception, 'That parent post ID is invalid.'
      except:
        pass

      if not checkNotFlooding(post):
        raise Exception, 'Flood detected.  Please try again'
        
      try:
        if not board['settings']['forced_anonymous']:
          post['name'] = cgi.escape(self.formdata['name']).strip()
          setCookie(self, 'pyib_name', self.formdata['name'])
      except:
        pass
      
      if post['name'] != '':
        name_match = re.compile(r'(.*)#(.*)').match(post['name'])
        if name_match:
          if name_match.group(2):
            post['name'] = name_match.group(1)
            post['tripcode'] = tripcode(name_match.group(2))
  
      try:
        post['email'] = cgi.escape(self.formdata['email']).strip()
      except:
        pass
      
      try:
        if not board['settings']['disable_subject'] and not post['parent']:
          post['subject'] = cgi.escape(self.formdata['subject']).strip()
      except:
        pass
      
      try:
        post['message'] = clickableURLs(cgi.escape(self.formdata['message']).rstrip()[0:8000])
        post['message'] = checkAllowedHTML(post['message'])
        if post['parent'] != 0:
          post['message'] = checkRefLinks(post['message'], post['parent'])
        post['message'] = checkQuotes(post['message'])
        post['message'] = post['message'].replace("\n", '<br>')
      except:
        pass
      
      try:
        post['password'] = self.formdata['password']
        setCookie(self, 'pyib_password', post['password'])
      except:
        pass
  
      # Create a single datetime now so everything syncs up
      t = datetime.datetime.now()
  
      try:
        if self.formdata['file']:
          post = processImage(post, self.formdata['file'], t)
      except Exception, message:
        raise Exception, 'Unable to process image:\n\n' + str(message)
  
      if not post['file']:
        if not post['parent']:
          raise Exception, 'Please upload an image to create a new thread'
        if not post['message']:
          raise Exception, 'Please upload an image, or enter a message'
  
      post['timestamp_formatted'] = t.strftime("%y/%m/%d(%a)%H:%M:%S")
      post['nameblock'] = nameBlock(post['name'], post['tripcode'], post['email'], post['timestamp_formatted'])
      
      db.query("INSERT INTO posts " \
               "(`boardid`, `parentid`, `name`, `tripcode`, `email`, " \
               "`nameblock`, `subject`, `message`, `file`, `file_hex`, " \
               "`file_mime`, `file_original`, `file_size`, `file_size_formatted`, `image_width`, " \
               "`image_height`, `thumb`, `thumb_width`, `thumb_height`, `thumb_catalog_width`, " \
               "`thumb_catalog_height`, `ip`, `timestamp_formatted`, `timestamp`, `bumped`) " \
               "VALUES " + \
               "(" + board['id']+ ", " + str(post['parent']) + ", '" + _mysql.escape_string(post['name']) + "', '" + _mysql.escape_string(post['tripcode']) + "', '" + _mysql.escape_string(post['email']) + "', " \
               "'" + _mysql.escape_string(post['nameblock']) + "', '" + _mysql.escape_string(post['subject']) + "', '" + _mysql.escape_string(post['message']) + "', '" + _mysql.escape_string(post['file']) + "', '" + _mysql.escape_string(post['file_hex']) + "', " \
               "'" + _mysql.escape_string(post['file_mime']) + "', '" + _mysql.escape_string(post['file_original']) + "', '" + _mysql.escape_string(str(post['file_size'])) + "', '" + _mysql.escape_string(post['file_size_formatted']) + "', '" + _mysql.escape_string(str(post['image_width'])) + "', " \
               "'" + _mysql.escape_string(str(post['image_height'])) + "', '" + _mysql.escape_string(post['thumb']) + "', '" + _mysql.escape_string(str(post['thumb_width'])) + "', '" + _mysql.escape_string(str(post['thumb_height'])) + "', '" + _mysql.escape_string(str(post['thumb_catalog_width'])) + "', " \
               "'" + _mysql.escape_string(str(post['thumb_catalog_height'])) + "', '" + post['ip'] + "', '" + post['timestamp_formatted'] + "', " + str(timestamp(t)) + ", " + str(timestamp(t)) + ")")
  
      postid = db.insert_id()
  
      trimThreads()
        
      if post['parent']:
        if post['email'].lower() != 'sage':
          db.query('UPDATE `posts` SET bumped = ' + str(timestamp(t)) + ' WHERE `id` = ' + str(post['parent']) + ' AND `boardid` = ' + board['id'] + ' LIMIT 1')
          setCookie(self, 'pyib_email', self.formdata['email'])
          
        threadUpdated(post['parent'])
        self.output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(post['parent']) + '.html">--&gt; --&gt; --&gt;'
      else:
        threadUpdated(postid)
        self.output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/">--&gt; --&gt; --&gt;'
    else:
      path_split = self.environ['PATH_INFO'].split('/')
      caught = False
  
      if len(path_split) > 1:
        if path_split[1] == 'manage':
          caught = True
          manage.manage(self, path_split)
          
      if not caught:
        # Redirect the user back to the front page
        self.output += '<meta http-equiv="refresh" content="0;url=' + Settings.HOME_URL + '">--&gt; --&gt; --&gt;'
  
  def handleRequest(self):
    self.headers = [('Content-Type', 'text/html')]
    self.handleCookies()
    
  def handleResponse(self):
    if self._cookies is not None:
      for cookie in self._cookies.values():
        self.headers.append(('Set-Cookie', cookie.output(header='')))
    
  def handleCookies(self):
    self._cookies = SimpleCookie()
    self._cookies.load(self.environ.get('HTTP_COOKIE', ''))
  
if __name__ == '__main__':
  from fcgi import WSGIServer

  # Psyco is not required, however it will be used if available
  try:
    import psyco
    psyco.bind(tenjin.helpers.to_str)
    psyco.bind(pyib.run, 2)
    psyco.bind(getFormData)
    psyco.bind(setCookie)
    psyco.bind(threadUpdated)
    psyco.bind(processImage)
  except ImportError:
    pass
  
  WSGIServer(pyib).run()
