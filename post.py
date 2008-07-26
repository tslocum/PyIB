import math
import os
import threading
import Queue

from database import *
from template import *
from settings import Settings
from framework import *

class RegenerateThread(threading.Thread):
  def __init__(self, threadid, request_queue):
    threading.Thread.__init__(self, name="RegenerateThread-%d" % (threadid,))
    self.request_queue = request_queue
  def run(self):
    while 1:
      action = self.request_queue.get()
      if action is None:
        break
      if action == 'front':
        regenerateFrontPages()
      else:
        regenerateThreadPage(action)

def threadUpdated(postid):
  """
  Shortcut to update front pages and thread page by passing a thread ID. Uses
  the simple threading module to do both regenerateFrontPages() and
  regenerateThreadPage() asynchronously
  """
  request_queue = Queue.Queue()
  threads = [RegenerateThread(i, request_queue) for i in range(2)]
  for t in threads:
    t.start()

  request_queue.put('front')
  request_queue.put(postid)

  for i in range(2):
    request_queue.put(None)

  for t in threads:
    t.join

def regenerateFrontPages():
  """
  Regenerates index.html and #.html for each page after that according to the number
  of live threads in the database
  """
  board = Settings._BOARD
  threads = []

  database_lock.acquire()
  try:
    op_posts = FetchAll('SELECT * FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = 0 ORDER BY `bumped` DESC')
    for op_post in op_posts:
      thread = {'posts': [op_post], 'omitted': 0}

      try:
        replies = FetchAll('SELECT * FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = ' + op_post['id'] + ' ORDER BY `id` DESC LIMIT ' + str(Settings.REPLIES_SHOWN_ON_FRONT_PAGE))
        if replies:
          if len(replies) == Settings.REPLIES_SHOWN_ON_FRONT_PAGE:
            thread['omitted'] = (int(FetchOne('SELECT COUNT(*) FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = ' + op_post['id'], 0)[0]) - Settings.REPLIES_SHOWN_ON_FRONT_PAGE)
          [thread['posts'].append(reply) for reply in replies[::-1]]
      except:
        pass

      threads.append(thread)
  finally:
    database_lock.release()

  pages = []
  if len(op_posts) > 0:
    page_count = int(math.ceil(float(len(op_posts)) / float(Settings.THREADS_SHOWN_ON_FRONT_PAGE)))
    
    for i in xrange(page_count):
      start = i * Settings.THREADS_SHOWN_ON_FRONT_PAGE
      end = start + Settings.THREADS_SHOWN_ON_FRONT_PAGE
      pages.append([])
      [pages[i].append(thread) for thread in threads[start:end]]
  else:
    page_count = 0
    pages.append({})
  
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
  """
  Regenerates /res/#.html for supplied thread id
  """
  board = Settings._BOARD
  
  page = threadPage(postid)
  
  f = open(Settings.ROOT_DIR + board['dir'] + '/res/' + str(postid) + '.html', 'w')
  try:
    f.write(page)
  finally:
    f.close()

def threadPage(postid):
  board = Settings._BOARD

  database_lock.acquire()
  try:
    postid = int(postid)
    op_post = FetchOne("SELECT * FROM `posts` WHERE `id` = " + str(postid) + " AND `boardid` = " + board['id'] + " LIMIT 1")
    if op_post:
      thread = {'posts': [op_post], 'omitted': 0}

      try:
        replies = FetchAll('SELECT * FROM `posts` WHERE `parentid` = ' + op_post['id'] + ' AND `boardid` = ' + board['id'] + ' ORDER BY `id` ASC')
        if replies:
          [thread['posts'].append(reply) for reply in replies]
      except:
        pass

      threads = [thread]
  finally:
    database_lock.release()

  return renderTemplate('board.html', {'threads': threads, 'replythread': postid})

def regenerateBoard():
  """
  Update front pages and every thread res HTML page
  """
  board = Settings._BOARD
  
  op_posts = FetchAll('SELECT `id` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = 0')

  request_queue = Queue.Queue()
  threads = [RegenerateThread(i, request_queue) for i in range(Settings.MAX_PROGRAM_THREADS)]
  for t in threads:
    t.start()

  request_queue.put('front')

  for post in op_posts:
    request_queue.put(post['id'])

  for i in range(Settings.MAX_PROGRAM_THREADS):
    request_queue.put(None)

  for t in threads:
    t.join()
  
def deletePost(postid):
  """
  Remove post from database and unlink file (if present), along with all replies
  if supplied post is a thread
  """
  global db
  board = Settings._BOARD
  
  post = FetchOne('SELECT `id`, `parentid`, `file`, `thumb` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = ' + str(postid) + ' LIMIT 1')
  if post:
    if int(post['parentid']) == 0:
      replies = FetchAll('SELECT `id` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = ' + str(postid))
      [deletePost(reply['id']) for reply in replies]

    if post['file'] != '':
      deleteFile(post)
      
    db.query('DELETE FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `id` = ' + post['id'] + ' LIMIT 1')
    
    if int(post['parentid']) == 0:
      try:
        os.unlink(Settings.ROOT_DIR + board['dir'] + '/res/' + post['id'] + '.html')
      except:
        pass

def deleteFile(post):
  """
  Unlink file and thumb of supplied post
  """
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
  """
  Delete any threads which have passed the MAX_THREADS setting
  """
  board = Settings._BOARD
  
  op_posts = FetchAll('SELECT `id` FROM `posts` WHERE `boardid` = ' + board['id'] + ' AND `parentid` = 0 ORDER BY `bumped` DESC')
  if len(op_posts) > Settings.MAX_THREADS:
    posts = op_posts[Settings.MAX_THREADS:]
    [deletePost(post['id']) for post in posts]

def pageNavigator(page_num, page_count):
  """
  Create page navigator in the format of [0], [1], [2]...
  """
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

def checkNotFlooding(post):
  if post['parentid'] == 0:
    floodlimit = Settings.SECONDS_BETWEEN_NEW_THREADS
  else:
    floodlimit = Settings.SECONDS_BETWEEN_REPLIES

  try:
    post = FetchOne('SELECT `timestamp` FROM `posts` WHERE `ip` = \'' + post['ip'] + '\' ORDER BY `timestamp` DESC LIMIT 1')
    seconds_since = (timestamp() - int(post['timestamp']))
  except:
    return True
  
  if seconds_since < floodlimit:
    return False
  else:
    return True
  
