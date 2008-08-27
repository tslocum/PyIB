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
      password = getMD5(self.formdata['pyib_password'])
      
      valid_account = FetchOne("SELECT * FROM `staff` WHERE `username` = '" + _mysql.escape_string(self.formdata['pyib_username']) + "' AND `password` = '" + _mysql.escape_string(password) + "' LIMIT 1")
      if valid_account:
        setCookie(self, 'pyib_manage', self.formdata['pyib_username'] + ':' + valid_account['password'], domain='THIS')
        setCookie(self, 'pyib_staff', 'yes')
        db.query('DELETE FROM `logs` WHERE `timestamp` < ' + str(timestamp() - 604800)) # one week
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
            logAction(staff_account['username'], 'Rebuilt all boards')
          else:
            t1 = time.time()
            board = setBoard(board_dir)
            regenerateBoard()
            
            page += 'Rebuilt /' + board['dir'] + '/ in ' + timeTaken(t1, time.time()) + ' seconds'
            logAction(staff_account['username'], 'Rebuilt /' + board['dir'] + '/')
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
                          logAction(staff_account['username'], 'Updated staff account for ' + self.formdata['username'])
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
                        password = getMD5(self.formdata['password'])
                        db.query("INSERT INTO `staff` (`username`, `password`, `added`, `rights`) VALUES ('" + _mysql.escape_string(self.formdata['username']) + "', '" + _mysql.escape_string(password) + "', " + str(timestamp()) + ", " + self.formdata['rights'] + ")")
                        page += 'Staff member added.'
                        logAction(staff_account['username'], 'Added staff account for ' + self.formdata['username'])
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
              member = FetchOne('SELECT `username` FROM `staff` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
              if member:
                db.query('DELETE FROM `staff` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
                page += 'Staff member deleted.'
                logAction(staff_account['username'], 'Deleted staff account for ' + member['username'])
              else:
                page += 'Unable to locate a staff account with that ID.'
            except:
              pass
              
        if not action_taken:
          page += '<a href="' + Settings.CGI_URL + 'manage/staff/add">Add new</a><br>' + \
          '<table border="1"><tr><th>ID</th><th>Username</th><th>Rights</th><th>Last Active</th><th>&nbsp;</th></tr>'
          staff = FetchAll('SELECT * FROM `staff` ORDER BY `rights`')
          for member in staff:
            page += '<tr><td>' + member['id'] + '</td><td>' + member['username'] + '</td><td>'
            if member['rights'] == '0':
              page += 'Super administrator'
            elif member['rights'] == '1':
              page += 'Administrator'
            elif member['rights'] == '2':
              page += 'Moderator'
            page += '</td><td>'
            if member['lastactive'] != '0':
              page += formatTimestamp(member['lastactive'])
            else:
              page += 'Never'
            page += '</td><td><a href="' + Settings.CGI_URL + 'manage/staff/edit/' + member['id'] + '">edit</a> <a href="' + Settings.CGI_URL + '/manage/staff/delete/' + member['id'] + '">delete</a></td></tr>'
          page += '</table>'
      elif path_split[2] == 'delete':
        do_ban = False
        try:
          if self.formdata['ban'] == 'true':
            do_ban = True
        except:
          pass
        
        board = setBoard(path_split[3])
        post = FetchOne('SELECT `parentid`, `ip` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[4]) + '\' LIMIT 1')
        if not post:
          page += 'Unable to locate a post with that ID.'
        else:
          deletePost(path_split[4])
          if post['parentid'] != '0':
            threadUpdated(post['parentid'])
          else:
            regenerateFrontPages()
          
          page += 'Post successfully deleted.'
          logAction(staff_account['username'], 'Deleted post /' + path_split[3] + '/' + path_split[4])
          
          if do_ban:
            page += '<br>Redirecting to ban page...<meta http-equiv="refresh" content="0;url=' + Settings.CGI_URL + 'manage/ban/' + post['ip'] + '">'
      elif path_split[2] == 'ban':
        if len(path_split) > 4:
          board = setBoard(path_split[3])
          post = FetchOne('SELECT `ip` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = \'' + _mysql.escape_string(path_split[4]) + '\' LIMIT 1')
          if not post:
            page += 'Unable to locate a post with that ID.'
          else:
            page += '<meta http-equiv="refresh" content="0;url=' + Settings.CGI_URL + 'manage/ban/' + post['ip'] + '">'
        else:
          if path_split[3] == '':
            try:
              ip = self.formdata['ip']
            except:
              ip = ''
          else:
            ip = path_split[3]
          if ip != '':
            try:
              reason = self.formdata['reason']
            except:
              reason = None
            if reason is not None:
              ban = FetchOne('SELECT `ip` FROM `bans` WHERE `ip` = \'' + _mysql.escape_string(ip) + '\' LIMIT 1')
              if not ban:
                if self.formdata['seconds'] != '0':
                  until = str(timestamp() + int(self.formdata['seconds']))
                else:
                  until = '0'
                db.query("INSERT INTO `bans` (`ip`, `added`, `until`, `staff`, `reason`) VALUES ('" + _mysql.escape_string(ip) + "', " + str(timestamp()) + ", " + until + ", '" + _mysql.escape_string(staff_account['username']) + "', '" + _mysql.escape_string(self.formdata['reason']) + "')")
                page += 'Ban successfully placed.'
                action = 'Banned ' + ip
                if until != '0':
                  action += ' until ' + formatTimestamp(until)
                else:
                  action += ' permanently'
                logAction(staff_account['username'], action)
              else:
                page += 'There is already a ban in place for that IP.'
            else:
              page += '<form action="' + Settings.CGI_URL + 'manage/ban/' + ip + '" name="banform" method="post">' + \
              '<label for="reason">Reason</label> <input type="text" name="reason"><br>' + \
              '<label for="seconds">Expire in #Seconds</label> <input type="text" name="seconds" value="0"> <a href="#" onclick="document.banform.seconds.value=\'0\';return false;">no expiration</a>&nbsp;<a href="#" onclick="document.banform.seconds.value=\'3600\';return false;">1hr</a>&nbsp;<a href="#" onclick="document.banform.seconds.value=\'604800\';return false;">1w</a>&nbsp;<a href="#" onclick="document.banform.seconds.value=\'1209600\';return false;">2w</a>&nbsp;<a href="#" onclick="document.banform.seconds.value=\'2592000\';return false;">30d</a>&nbsp;<a href="#" onclick="document.banform.seconds.value=\'31536000\';return false;">1yr</a><br>' + \
              '<label for="submit">&nbsp;</label> <input type="submit" value="Place Ban">' + \
              '</form>'
      elif path_split[2] == 'bans':
        if len(path_split) > 4:
          if path_split[3] == 'delete':
            ip = FetchOne('SELECT `ip` FROM `bans` WHERE `id` = \'' + _mysql.escape_string(path_split[4]) + '\' LIMIT 1', 0)[0]
            if ip != '':
              db.query('DELETE FROM `bans` WHERE `id` = ' + _mysql.escape_string(path_split[4]) + ' LIMIT 1')
              page += 'Ban deleted.'
              logAction(staff_account['username'], 'Deleted ban for ' + ip)
            else:
              page += 'There was a problem while deleting that ban.  It may have already been removed, or recently expired.'
        bans = FetchAll('SELECT * FROM `bans` ORDER BY `added` DESC')
        page += '<form action="' + Settings.CGI_URL + 'manage/ban/" name="banform" method="post">' + \
        '<label for="ip">IP address</label> <input type="text" name="ip"><br>' + \
        '<label for="submit">&nbsp;</label> <input type="submit" value="Proceed to ban form">' + \
        '</form><br>'
        if bans:
          page += '<table border="1"><tr><th>IP Address</th><th>Added</th><th>Expires</th><th>Placed by</th><th>Reason</th><th>&nbsp;</th></tr>'
          for ban in bans:
            page += '<tr><td>' + ban['ip'] + '</td><td>' + formatTimestamp(ban['added']) + '</td><td>'
            if ban['until'] == '0':
              page += 'Does not expire'
            else:
              page += formatTimestamp(ban['until'])
            page += '</td><td>' + ban['staff'] + '</td><td>' + ban['reason'] + '</td><td><a href="' + Settings.CGI_URL + 'manage/bans/delete/' + ban['id'] + '">delete</a></td></tr>'
          page += '</table>'
      elif path_split[2] == 'changepassword':
        form_submitted = False
        try:
          if self.formdata['oldpassword'] != '' and self.formdata['newpassword'] != '' and self.formdata['newpassword2'] != '':
            form_submitted = True
        except:
          pass
        if form_submitted:
          if getMD5(self.formdata['oldpassword']) == staff_account['password']:
            if self.formdata['newpassword'] == self.formdata['newpassword2']:
              db.query('UPDATE `staff` SET `password` = \'' + getMD5(self.formdata['newpassword']) + '\' WHERE `id` = ' + staff_account['id'] + ' LIMIT 1')
              page += 'Password successfully changed.  Please log out and log back in.'
            else:
              page += 'Passwords did not match.'
          else:
            page += 'Current password incorrect.'
        else:
          page += '<form action="' + Settings.CGI_URL + 'manage/changepassword" method="post">' + \
          '<label for="oldpassword">Current password</label> <input type="password" name="oldpassword"><br>' + \
          '<label for="newpassword">New password</label> <input type="password" name="newpassword"><br>' + \
          '<label for="newpassword2">New password (confirm)</label> <input type="password" name="newpassword2"><br>' + \
          '<label for="submit">&nbsp;</label> <input type="submit" value="Change Password">' + \
          '</form>'
      elif path_split[2] == 'board':
        board = setBoard('old-b')
        board['settings']['anonymous'] = ''
        board['settings']['forced_anonymous'] = True
        board['settings']['disable_subject'] = True
        board['settings']['postarea_extra_html_top'] = '<small>This is an experiment in creating a /b/ with the feel of a few years ago, by using rule enforcement.<br>If you posted on /b/ before the spread, you\'ll know what is bannable and what isn\'t.<br>If you post like a new user, you will be banned.</small><br>'
        updateBoardSettings()
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
              logAction(staff_account['username'], 'Added board /' + board['dir'] + '/')
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
      elif path_split[2] == 'logs':
        if staff_account['rights'] != '0':
          return

        page += '<table border="1"><tr><th>Date</th><th>Staff Account</th><th>Action</th></tr>'
        logs = FetchAll('SELECT * FROM `logs` ORDER BY `timestamp` DESC')
        for log in logs:
          page += '<tr><td>' + formatTimestamp(log['timestamp']) + '</td><td>' + log['staff'] + '</td><td>' + log['action'] + '</td></tr>'
        page += '</table>'
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
        'added': formatTimestamp(staff_account['added']),
      })
    
    self.output += renderTemplate('manage.html', template_values)

def logAction(staff, action):
  global db
  
  db.query("INSERT INTO `logs` (`timestamp`, `staff`, `action`) VALUES (" + str(timestamp()) + ", '" + _mysql.escape_string(staff) + "\', \'" + _mysql.escape_string(action) + "\')")
