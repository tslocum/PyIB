#!/usr/bin/python2.4
#!/usr/bin/env python

import time
import datetime
import cgi
import md5
import _mysql
from Cookie import SimpleCookie

import tenjin
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
    self.formdata = get_post_form(environ)
    self.output = ''
    self.handleRequest()
    self.run()
  
  def __iter__(self):
    self.handleResponse()
    self.start('200 OK', self.headers)
    yield self.output
  
  def run(self):
    environ = self.environ
    formdata = self.formdata
    
    if environ['PATH_INFO'] == '/post':
      try:
        if formdata['board']:
          board = FetchOne("SELECT * FROM `boards` WHERE `dir` = '" + _mysql.escape_string(formdata['board']) + "' LIMIT 1")
          if not board:
            raise Exception
          board = setBoard(formdata['board'])
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
        'ip': '',
      }
      
      try:
        parent = cgi.escape(formdata['parent']).strip()
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
      
      try:
        if not board['settings']['forced_anonymous']:
          post['name'] = cgi.escape(formdata['name']).strip()
          setCookie(self, 'pyib_name', formdata['name'])
      except:
        pass
      
      if post['name'] != '':
        name_match = re.compile(r'(.*)#(.*)').match(post['name'])
        if name_match:
          if name_match.group(2):
            post['name'] = name_match.group(1)
            post['tripcode'] = tripcode(name_match.group(2))
  
      try:
        post['email'] = cgi.escape(formdata['email']).strip()
      except:
        pass
      
      try:
        if not board['settings']['disable_subject'] and not post['parent']:
          post['subject'] = cgi.escape(formdata['subject']).strip()
      except:
        pass
      
      try:
        post['message'] = clickableURLs(cgi.escape(formdata['message']).rstrip()[0:8000])
        post['message'] = checkAllowedHTML(post['message'])
        if post['parent'] != 0:
          post['message'] = checkRefLinks(post['message'], post['parent'])
        post['message'] = checkQuotes(post['message'])
        post['message'] = post['message'].replace("\n", '<br>')
      except:
        pass
      
      try:
        post['password'] = formdata['password']
        setCookie(self, 'pyib_password', post['password'])
      except:
        pass
  
      # Create a single datetime now so everything syncs up
      t = datetime.datetime.now()
  
      try:
        if formdata['file']:
          post = processImage(post, formdata['file'], t)
      except Exception, message:
        raise Exception, 'Unable to process image:\n\n' + str(message)
  
      if not post['file']:
        if not post['parent']:
          raise Exception, 'Please upload an image to create a new thread'
        if not post['message']:
          raise Exception, 'Please upload an image, or enter a message'
  
      post['timestamp_formatted'] = t.strftime("%y/%m/%d(%a)%H:%M:%S")
      post['nameblock'] = nameBlock(post['name'], post['tripcode'], post['email'], post['timestamp_formatted'])
      post['ip'] = environ['REMOTE_ADDR']
      
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
          setCookie(self, 'pyib_email', formdata['email'])
          
        threadUpdated(post['parent'])
        self.output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(post['parent']) + '.html">--&gt; --&gt; --&gt;'
      else:
        threadUpdated(postid)
        self.output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/">--&gt; --&gt; --&gt;'
    else:
      path_split = environ['PATH_INFO'].split('/')
      caught = False
  
      if len(path_split) > 1:
        caught = True
        
        if path_split[1] == 'manage':
          page = ''
          validated = False
          administrator = False
          skiptemplate = False
          
          try:
            if formdata['pyib_username'] and formdata['pyib_password']:
              m = md5.new()
              m.update(formdata['pyib_password'])
              password = m.hexdigest()
              
              valid_account = FetchOne("SELECT * FROM `staff` WHERE `username` = '" + _mysql.escape_string(formdata['pyib_username']) + "' AND `password` = '" + _mysql.escape_string(password) + "' LIMIT 1")
              if valid_account:
                setCookie(self, 'pyib_manage', formdata['pyib_username'] + ':' + valid_account['password'], domain='THIS')
              else:
                page += 'Incorrect username/password.<hr>'
          except:
            pass
          
          try:
            manage_cookie = self._cookies['pyib_manage'].value
            if manage_cookie != '':
              username, password = manage_cookie.split(':')
              staff_account = FetchOne("SELECT * FROM `staff` WHERE `username` = '" + _mysql.escape_string(username) + "' AND `password` = '" + _mysql.escape_string(password) + "' LIMIT 1")
              if staff_account:
                validated = True
                if staff_account['rights'] == '0' or staff_account['rights'] == '1':
                  administrator = True
                db.query('UPDATE `staff` SET `lastactive` = ' + str(timestamp()) + ' WHERE `id` = ' + staff_account['id'] + ' LIMIT 1')
          except:
            pass
          
          if not validated:
            page += """<div style="text-align: center;">
            <form action=""" + '"' + Settings.CGI_URL + """manage" method="post">
            <label for="username">Username</label> <input type="text" name="pyib_username"><br>
            <label for="password">Password</label> <input type="password" name="pyib_password"><br>
            <label for="submit">&nbsp;</label> <input type="submit" name="submit" value="Log in">
            </form>"""
          else:
            if len(path_split) > 2:
              if path_split[2] == 'rebuild':
                if not administrator:
                  return
                
                try:
                  board_dir = path_split[3]
                except:
                  board_dir = ''
                
                if board_dir == '':
                  page += 'Please click on the board you wish to rebuild:<br><br><a href="' + Settings.CGI_URL + 'manage/rebuild/!ALL">Rebuild all boards</b></a><br>'
                  boards = FetchAll('SELECT * FROM `boards` ORDER BY `dir`')
                  for board in boards:
                    page += '<br><a href="' + Settings.CGI_URL + 'manage/rebuild/' + board['dir'] + '">/' + board['dir'] + '/ - ' + board['name'] + '</a>'
                else:
                  if board_dir == '!ALL':
                    t1 = time.time()
                    boards = FetchAll('SELECT `dir` FROM `boards`')
                    for board in boards:
                      board = setBoard(board['dir'])
                      regenerateBoard()
                    
                    page += 'Rebuilt all boards in ' + timeTaken(t1, time.time()) + ' seconds'
                  else:
                    t1 = time.time()
                    board = setBoard(board_dir)
                    regenerateBoard()
                    
                    page += 'Rebuilt /' + board['dir'] + '/ in ' + timeTaken(t1, time.time()) + ' seconds'
              elif path_split[2] == 'modbrowse':
                skiptemplate = True
                Settings._MODBROWSE = True
                board = setBoard(path_split[3])
                self.output += threadPage(path_split[4])
              elif path_split[2] == 'staff':
                if staff_account['rights'] != '0':
                  return
                action_taken = False
                
                if len(path_split) > 3:
                  if path_split[3] == 'add' or path_split[3] == 'edit':
                    member = None
                    member_username = ''
                    member_rights = '2'
                    
                    if path_split[3] == 'edit':
                      if len(path_split) > 4:
                        member = FetchOne('SELECT * FROM `staff` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
                        if member:
                          member_username = member['username']
                          member_rights = member['rights']
                          action = 'edit/' + member['id']
                          
                          try:
                            if formdata['username'] != '':
                              if formdata['rights'] in ['0', '1', '2']:
                                action_taken = True
                                if not ':' in formdata['username']:
                                  db.query("UPDATE `staff` SET `username` = '" + _mysql.escape_string(formdata['username']) + "', `rights` = " + formdata['rights'] + " LIMIT 1")
                                  page += 'Staff member updated.'
                                else:
                                  page += 'The character : can not be used in usernames.'
                          except:
                            pass
                    else:
                      action = 'add'
                      try:
                        if formdata['username'] != '' and formdata['password'] != '':
                          username_taken = FetchOne('SELECT * FROM `staff` WHERE `username` = \'' + _mysql.escape_string(formdata['username']) + '\' LIMIT 1')
                          if not username_taken:
                            if formdata['rights'] in ['0', '1', '2']:
                              action_taken = True
                              if not ':' in formdata['username']:
                                m = md5.new()
                                m.update(formdata['password'])
                                password = m.hexdigest()
                                db.query("INSERT INTO `staff` (`username`, `password`, `added`, `rights`) VALUES ('" + _mysql.escape_string(formdata['username']) + "', '" + _mysql.escape_string(password) + "', " + str(timestamp()) + ", " + formdata['rights'] + ")")
                                page += 'Staff member added.'
                              else:
                                page += 'The character : can not be used in usernames.'
                          else:
                            action_taken = True
                            page += 'That username is already in use.'
                      except:
                        pass

                    if not action_taken:
                      action_taken = True
                       
                      page += '<form action="' + Settings.CGI_URL + 'manage/staff/' + action + '" method="post">' + \
                      '<label for="username">Username</label> <input type="text" name="username" value="' + member_username + '"><br>'
                      
                      if not member:
                        page += '<label for="password">Password</label> <input type="password" name="password"><br>'
                        
                      page += '<label for="rights">Rights</label> <select name="rights"><option value="2"'
                      if member_rights == '2':
                        page += ' selected'
                      page += '>Moderator</option><option value="1"'
                      if member_rights == '1':
                        page += ' selected'
                      page += '>Administrator</option><option value="0"'
                      if member_rights == '0':
                        page += ' selected'
                      page += '>Super administrator</option></select><br>' + \
                      '<label for="submit">&nbsp;</label> <input type="submit" name="submit" value="'
                      if path_split[3] == 'add':
                        page += 'Add'
                      else:
                        page += 'Edit'
                      page += '">' + \
                      '</form>'
                  elif path_split[3] == 'delete':
                    action_taken = True
                    page += '<a href="' + Settings.CGI_URL + 'manage/staff/delete_confirmed/' + path_split[4] + '">Click here to confirm the deletion of that staff member</a>'
                  elif path_split[3] == 'delete_confirmed':
                    try:
                      action_taken = True
                      db.query('DELETE FROM `staff` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
                      page += 'Staff member deleted.'
                    except:
                      pass
                      
                if not action_taken:
                  page += '<a href="' + Settings.CGI_URL + 'manage/staff/add">Add new</a><br>' + \
                  '<table border="1"><tr><th>ID</th><th>Username</th><th>Rights</th><th>&nbsp;</th></tr>'
                  staff = FetchAll('SELECT * FROM `staff` ORDER BY `rights`')
                  for member in staff:
                    page += '<tr><td>' + member['id'] + '</td><td>' + member['username'] + '</td><td>'
                    if member['rights'] == '0':
                      page += 'Super administrator'
                    elif member['rights'] == '1':
                      page += 'Administrator'
                    elif member['rights'] == '2':
                      page += 'Moderator'
                    page += '</td><td><a href="' + Settings.CGI_URL + 'manage/staff/edit/' + member['id'] + '">edit</a> <a href="' + Settings.CGI_URL + '/manage/staff/delete/' + member['id'] + '">delete</a></td></tr>'
                  page += '</table>'
              elif path_split[2] == 'logout':
                page += 'Logging out...<meta http-equiv="refresh" content="0;url=' + Settings.CGI_URL + 'manage">'
                setCookie(self, 'pyib_manage', '', domain='THIS')
            else:
              page += "I'll think of something to put on the manage home."

          if not skiptemplate:
            template_values = {
              'title': 'Manage',
              'validated': validated,
              'page': page,
              'navbar': False,
            }
            
            if validated:
              template_values.update({
                'username': staff_account['username'],
                'rights': staff_account['rights'],
                'administrator': administrator,
                'added': datetime.datetime.fromtimestamp(int(staff_account['added'])).strftime("%y/%m/%d(%a)%H:%M:%S"),
              })
            
            self.output += renderTemplate('manage.html', template_values)
        else:
          caught = False
          
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
    psyco.bind(renderTemplate)
    psyco.bind(tenjin.Engine.render)
    psyco.bind(tenjin.Template.render)
    psyco.bind(tenjin.helpers.to_str)
  except ImportError:
    pass
  
  WSGIServer(pyib).run()
