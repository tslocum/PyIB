import math
import os

from database import *
from template import *
from settings import Settings

def threadUpdated(postid):
  regenerateFrontPages()
  regenerateThreadPage(postid)

def regenerateFrontPages():
  board = Settings._BOARD
  threads = []
  
  op_posts = FetchAll('SELECT * FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = 0 ORDER BY `bumped` DESC')
  for op_post in op_posts:
    thread = {'posts': [op_post], 'omitted': 0}

    try:
      replies = FetchAll('SELECT * FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = ' + op_post['id'] + ' ORDER BY `id` DESC LIMIT ' + str(Settings.REPLIES_SHOWN_ON_FRONT_PAGE))
      if replies:
        if len(replies) == Settings.REPLIES_SHOWN_ON_FRONT_PAGE:
          thread['omitted'] = (int(FetchOne('SELECT COUNT(*) FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = ' + op_post['id'], 0)[0]) - Settings.REPLIES_SHOWN_ON_FRONT_PAGE)
        for reply in replies[::-1]:
          thread['posts'].append(reply)
    except:
      pass

    threads.append(thread)

  page_count = int(math.ceil(float(len(op_posts)) / float(Settings.THREADS_SHOWN_ON_FRONT_PAGE)))
  
  pages = []
  for i in xrange(page_count):
    start = i * Settings.THREADS_SHOWN_ON_FRONT_PAGE
    end = start + Settings.THREADS_SHOWN_ON_FRONT_PAGE
    pages.append([])
    for thread in threads[start:end]:
      pages[i].append(thread)
  
  page_num = 0
  for page in pages:
    if page_num == 0:
      file_name = 'index'
    else:
      file_name = str(page_num)
    page_rendered = renderTemplate('board.html', {'threads': page, 'page_navigator': pageNavigator(page_num, page_count)})
    
    f = open(Settings.ROOT_DIR + board['dir'] + '/' + file_name + '.html', 'w')
    try:
      f.write(page_rendered)
    finally:
      f.close()

    page_num += 1
  
def regenerateThreadPage(postid):
  board = Settings._BOARD
  
  try:
    postid = int(postid)
    op_post = FetchOne("SELECT * FROM `posts` WHERE `id` = " + str(postid) + " AND `boardid` = " + board['id'] + " LIMIT 1")
    if op_post:
      thread = {'posts': [op_post], 'omitted': 0}

      try:
        replies = FetchAll('SELECT * FROM `posts` WHERE `parentid` = ' + op_post['id'] + ' AND `boardid` = ' + board['id'] + ' ORDER BY `id` ASC')
        if replies:
          for reply in replies:
            thread['posts'].append(reply)
      except:
        pass

      threads = [thread]

    page = renderTemplate('board.html', {'threads': threads, 'replythread': postid})
    
    f = open(Settings.ROOT_DIR + board['dir'] + '/res/' + str(postid) + '.html', 'w')
    try:
      f.write(page)
    finally:
      f.close()
      
  except Exception, message:
    raise Exception, message
  
def deletePost(postid):
  global db
  board = Settings._BOARD
  
  post = FetchOne('SELECT * FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = ' + postid + ' LIMIT 1')
  if post:
    if post['parentid'] != 0:
      replies = FetchAll('SELECT `id` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = ' + postid + ' LIMIT 1')
      for reply in replies:
        deletePost(reply['id'])

    if post['file'] != '':
      deleteFile(post)
      
    db.query('DELETE FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = ' + post['id'] + ' LIMIT 1')

def deleteFile(post):
  board = Settings._BOARD

  try:
    os.unlink(Settings.ROOT_DIR + board['dir'] + '/src/' + post['file'])
  except:
    pass

  try:
    os.unlink(Settings.ROOT_DIR + board['dir'] + '/thumb/' + post['thumb'])
  except:
    pass

def trimThreads():
  board = Settings._BOARD
  
  op_posts = FetchAll('SELECT `id` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = 0 ORDER BY `bumped` DESC')
  if len(op_posts) > Settings.MAX_THREADS:
    posts_to_trim = op_posts[Settings.MAX_THREADS:]
    for post_to_trim in posts_to_trim:
      deletePost(post_to_trim['id'])

def pageNavigator(page_num, page_count):
  board = Settings._BOARD
  
  page_navigator = '<td>'
  if page_num == 0:
    page_navigator += 'Previous'
  else:
    previous = str(page_num - 1)
    if previous == '0':
      previous = ''
    else:
      previous = previous + '.html'
    page_navigator += '<form method="get" action="' + Settings.BOARDS_URL + board['dir'] + '/' + previous + '"><input value="Previous" type="submit"></form>'

  page_navigator += '</td><td>'

  for i in xrange(page_count):
    if i == page_num:
      page_navigator += '[' + str(i) + '] '
    else:
      if i == 0:
         page_navigator += '[<a href="' + Settings.BOARDS_URL + board['dir'] + '/">' + str(i) + '</a>] '
      else:
        page_navigator += '[<a href="' + Settings.BOARDS_URL + board['dir'] + '/' + str(i) + '.html">' + str(i) + '</a>] '
        
  page_navigator += '</td><td>'

  next = (page_num + 1)
  if next == 10 or next == page_count:
    page_navigator += 'Next</td>'
  else:
    page_navigator += '<form method="get" action="' + Settings.BOARDS_URL + board['dir'] + '/' + str(next) + '.html"><input value="Next" type="submit"></form></td>'

  return page_navigator
