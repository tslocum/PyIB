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

_DEBUG = True

class pyib(object):
  def __init__(self, environ, start_response):
    global _DEBUG
    self.environ = environ
    self.start = start_response
    self.formdata = getFormData(self)
    self.output = ''
    self.handleRequest()

    if _DEBUG:
      self.run()
    else:
      try:
        self.run()
      except Exception, message:
        self.error(message)
      
  def __iter__(self):
    self.handleResponse()
    self.start('200 OK', self.headers)
    yield self.output

  def error(self, message):
    self.output += renderTemplate('error.html', {'error': message, 'navbar': False})
    
  def run(self):
    db.query('DELETE FROM `bans` WHERE `until` != 0 AND `until` < ' + str(timestamp()))
    if self.environ['PATH_INFO'] == '/post':
      ban = FetchOne('SELECT * FROM `bans` WHERE `ip` = \'' + self.environ['REMOTE_ADDR'] + '\' LIMIT 1')
      if ban:
        message = 'You have been banned from posting on this board.<br>'
        if ban['reason'] != '':
          message += 'Reason: ' + ban['reason'] + '<br>'
        else:
          message += 'No reason was given for this ban.<br>'
        message += 'Your ban was placed <b>' + formatTimestamp(ban['added']) + '</b>, and '
        if ban['until'] != '0':
          message += 'will expire <b>' + formatTimestamp(ban['until']) + '</b>.<br>'
        else:
          message += '<b>will not expire</b>.<br>'
        message += 'Your IP address is <b>' + self.environ['REMOTE_ADDR'] + '</b>.'
          
        self.error(message)
        return
        
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
  
      post = Post(board['id'])
      post['ip'] = self.environ['REMOTE_ADDR']
      
      try:
        parent = cgi.escape(self.formdata['parent']).strip()
        try:
          parent_post = FetchOne('SELECT COUNT(*) FROM `posts` WHERE `id` = ' + parent + ' AND `parentid` = 0 AND `boardid` = ' + board['id'] + ' LIMIT 1', 0)
          if int(parent_post[0]) > 0:
            post['parentid'] = parent
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
        if not board['settings']['disable_subject'] and not post['parentid']:
          post['subject'] = cgi.escape(self.formdata['subject']).strip()
      except:
        pass
      
      try:
        post['message'] = clickableURLs(cgi.escape(self.formdata['message']).rstrip()[0:8000])
        post['message'] = checkAllowedHTML(post['message'])
        if post['parentid'] != 0:
          post['message'] = checkRefLinks(post['message'], post['parentid'])
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
        if not post['parentid']:
          raise Exception, 'Please upload an image to create a new thread'
        if not post['message']:
          raise Exception, 'Please upload an image, or enter a message'
  
      post['timestamp_formatted'] = formatDate(t)
      post['timestamp'] = timestamp(t)
      post['bumped'] = timestamp(t)
      post['nameblock'] = nameBlock(post['name'], post['tripcode'], post['email'], post['timestamp_formatted'])

      postid = post.insert()
      trimThreads()
      
      if post['parentid']:
        if post['email'].lower() != 'sage':
          db.query('UPDATE `posts` SET bumped = ' + str(timestamp(t)) + ' WHERE `id` = ' + str(post['parentid']) + ' AND `boardid` = ' + board['id'] + ' LIMIT 1')
          setCookie(self, 'pyib_email', self.formdata['email'])
          
        threadUpdated(post['parentid'])
        self.output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(post['parentid']) + '.html">--&gt; --&gt; --&gt;'
      else:
        threadUpdated(postid)
        self.output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/">--&gt; --&gt; --&gt;'
    else:
      path_split = self.environ['PATH_INFO'].split('/')
      caught = False
  
      if len(path_split) > 1:
        if path_split[1] == 'delete':
          caught = True
          board = None
          delete_id = 0
          imageonly = False
          try:
            if self.formdata['board']:
              board = setBoard(self.formdata['board'])
          except:
            pass
          if board:
            if self.formdata['password'] != '':
              try:
                delete_id = int(self.formdata['delete'])
              except:
                pass
              if delete_id > 0:
                post = FetchOne('SELECT * FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = ' + str(delete_id) + ' LIMIT 1')
                if post:
                  if post['password'] == self.formdata['password']:
                    try:
                      if self.formdata['imageonly']:
                        imageonly = True
                    except:
                      pass
                    if imageonly:
                      if post['file'] != '':
                        if post['message'] != '':
                          deleteFile(post)
                          db.query('UPDATE `posts` SET `file` = \'\', `file_hex` = \'\' WHERE `boardid` = ' + board['id'] + ' AND `id` = ' + str(delete_id) + ' LIMIT 1')
                        else:
                          deletePost(delete_id)
                    else:
                      deletePost(delete_id)
                    if post['parentid'] == '0':
                      regenerateFrontPage()
                    else:
                      threadUpdated(post['parentid'])
                    if imageonly:
                      self.output += 'File successfully deleted from post.'
                    else:
                      self.output += 'Post successfully deleted.'
                  else:
                    self.error('Incorrect password.')
                else:
                  self.error('Unable to locate a post with that ID.  The post may have already been deleted.')
              else:
                self.error('Unable to detect selected post.  You may have not checked a checkbox, or checked more than one checkbox.')
            else:
              self.error('Please enter a password.')
          else:
            self.error('Invalid board supplied.')
        elif path_split[1] == 'manage':
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
