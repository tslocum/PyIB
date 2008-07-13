#!/usr/bin/env python

import datetime
import cgi
import _mysql

from database import *
from settings import Settings
from framework import *
from formatting import *
from post import *
from img import *

def pyib(environ, start_response):
  global db
  start_response('200 OK', [('Content-Type', 'text/html')])
  
  output = ''

  if environ['PATH_INFO'] == '/post':
    formdata = get_post_form(environ)

    try:
      if formdata['board']:
        board = FetchOne("SELECT * FROM `boards` WHERE `dir` = '" + _mysql.escape_string(formdata['board']) + "' LIMIT 1")
        if not board:
          raise Exception
        Settings._BOARD = board
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
      if not Settings.FORCED_ANONYMOUS:
        post['name'] = cgi.escape(formdata['name']).strip()
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
      if not Settings.DISABLE_SUBJECT:
        post['subject'] = cgi.escape(formdata['subject']).strip()
    except:
      pass
    
    try:
      post['message'] = clickableURLs(cgi.escape(formdata['message']).rstrip()[0:8000])
      post['message'] = checkQuotes(post['message'])
      post['message'] = checkAllowedHTML(post['message'])
      if post['parent'] != 0:
        post['message'] = checkRefLinks(post['message'], post['parent'])
      post['message'] = post['message'].replace("\n", '<br>')
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
      threadUpdated(post['parent'])
      output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(post['parent']) + '.html">--&gt; --&gt; --&gt;'
    else:
      threadUpdated(postid)
      output += '<meta http-equiv="refresh" content="0;url=' + Settings.BOARDS_URL + board['dir'] + '/">--&gt; --&gt; --&gt;'
  elif environ['PATH_INFO'] == '/admin':
    output += 'f'
  elif environ['PATH_INFO'] == '/rebuild':
    board = FetchOne("SELECT * FROM `boards` WHERE `dir` = 'b' LIMIT 1")
    Settings._BOARD = board
    op_posts = FetchAll('SELECT `id` FROM `posts` WHERE `boardid` = ' + board['id'])
    for op_post in op_posts:
      regenerateThreadPage(op_post['id'])
    regenerateFrontPages()
    output += 'Done.'
  else:
    output += '<meta http-equiv="refresh" content="0;url=' + Settings.HOME_URL + '">--&gt; --&gt; --&gt;'

  return [output]
  
if __name__ == '__main__':
  from fcgi import WSGIServer
  WSGIServer(pyib).run()
