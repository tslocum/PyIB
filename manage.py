import md5
import _mysql
import os

from database import *
from settings import Settings
from framework import *
from template import *
from post import *

def manage(self, path_split):
  global db
  page = ''
  validated = False
  administrator = False
  skiptemplate = False
  
  try:
    if self.formdata['pyib_username'] and self.formdata['pyib_password']:
      m = md5.new()
      m.update(self.formdata['pyib_password'])
      password = m.hexdigest()
      
      valid_account = FetchOne("SELECT * FROM `staff` WHERE `username` = '" + _mysql.escape_string(self.formdata['pyib_username']) + "' AND `password` = '" + _mysql.escape_string(password) + "' LIMIT 1")
      if valid_account:
        setCookie(self, 'pyib_manage', self.formdata['pyib_username'] + ':' + valid_account['password'], domain='THIS')
        setCookie(self, 'pyib_staff', 'yes')
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
        board_dir = ''
        thread_id = 0
        try:
          board_dir = path_split[3]
          thread_id = path_split[4]
        except:
          pass

        if board_dir == '':
          try:
            board_dir = self.formdata['dir']
            thread_id = self.formdata['postid']
          except:
            pass
          
        if board_dir == '':
          page += """<div style="text-align: center;">
          <form action=""" + '"' + Settings.CGI_URL + """manage/modbrowse" method="post">
          <label for="dir">Board</label> <select name="dir">"""
          boards = FetchAll('SELECT * FROM `boards` ORDER BY `dir`')
          for board in boards:
            page += '<option value="' + board['dir'] + '">/' + board['dir'] + '/ - ' + board['name'] + '</option>'
          page += '</select><br>' + \
          '<label for="postid">Thread ID</label> <input type="text" name="postid"><br>' \
          '<label for="submit">&nbsp;</label> <input type="submit" name="submit" value="Modbrowse">' \
          '</form>'
        else:
          skiptemplate = True
          Settings._MODBROWSE = True
          board = setBoard(board_dir)
          self.output += threadPage(thread_id)
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
                    if self.formdata['username'] != '':
                      if self.formdata['rights'] in ['0', '1', '2']:
                        action_taken = True
                        if not ':' in self.formdata['username']:
                          db.query("UPDATE `staff` SET `username` = '" + _mysql.escape_string(self.formdata['username']) + "', `rights` = " + self.formdata['rights'] + " LIMIT 1")
                          page += 'Staff member updated.'
                        else:
                          page += 'The character : can not be used in usernames.'
                  except:
                    pass
            else:
              action = 'add'
              try:
                if self.formdata['username'] != '' and self.formdata['password'] != '':
                  username_taken = FetchOne('SELECT * FROM `staff` WHERE `username` = \'' + _mysql.escape_string(self.formdata['username']) + '\' LIMIT 1')
                  if not username_taken:
                    if self.formdata['rights'] in ['0', '1', '2']:
                      action_taken = True
                      if not ':' in self.formdata['username']:
                        m = md5.new()
                        m.update(self.formdata['password'])
                        password = m.hexdigest()
                        db.query("INSERT INTO `staff` (`username`, `password`, `added`, `rights`) VALUES ('" + _mysql.escape_string(self.formdata['username']) + "', '" + _mysql.escape_string(password) + "', " + str(timestamp()) + ", " + self.formdata['rights'] + ")")
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
      elif path_split[2] == 'addboard':
        action_taken = False
        board_dir = ''
        
        try:
          if self.formdata['name'] != '':
            board_dir = self.formdata['dir']
        except:
          pass

        if board_dir != '':
          action_taken = True
          board_exists = FetchOne('SELECT * FROM `boards` WHERE `dir` = \'' + _mysql.escape_string(board_dir) + '\' LIMIT 1')
          if not board_exists:
            os.mkdir(Settings.ROOT_DIR + board_dir)
            os.mkdir(Settings.ROOT_DIR + board_dir + '/res')
            os.mkdir(Settings.ROOT_DIR + board_dir + '/src')
            os.mkdir(Settings.ROOT_DIR + board_dir + '/thumb')
            if os.path.exists(Settings.ROOT_DIR + board_dir) and os.path.isdir(Settings.ROOT_DIR + board_dir):
              db.query('INSERT INTO `boards` (`dir`, `name`) VALUES (\'' + _mysql.escape_string(board_dir) + '\', \'' + _mysql.escape_string(self.formdata['name']) + '\')')
              board = setBoard(board_dir)
              f = open(Settings.ROOT_DIR + board['dir'] + '/.htaccess', 'w')
              try:
                f.write('DirectoryIndex index.html')
              finally:
                f.close()
              regenerateFrontPages()
              page += 'Board added'
            else:
              page += 'There was a problem while making the directories'
          else:
            page += 'There is already a board with that directory'

        if not action_taken:
          page += '<form action="' + Settings.CGI_URL + 'manage/addboard" method="post">' + \
          '<label for="dir">Directory</label> <input type="text" name="dir"><br>' + \
          '<label for="name">Name</label> <input type="text" name="name"><br>' + \
          '<label for="submit">&nbsp;</label> <input type="submit" name="submit" value="Add board">' + \
          '</form>'
      elif path_split[2] == 'logout':
        page += 'Logging out...<meta http-equiv="refresh" content="0;url=' + Settings.CGI_URL + 'manage">'
        setCookie(self, 'pyib_manage', '', domain='THIS')
        setCookie(self, 'pyib_staff', '')
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

