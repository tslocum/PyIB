import string
import re

from settings import Settings

def tripcode(pw):
  import crypt
  from crypt import crypt
  pw = pw.encode('sjis', 'ignore')	\
    .replace('"', '&quot;')		\
    .replace("'", '\'')		\
    .replace('<', '&lt;')		\
    .replace('>', '&gt;')		\
    .replace(',', ',')
  salt = re.sub(r'[^\.-z]', '.', (pw + 'H..')[1:3])
  salt = salt.translate(string.maketrans(r':;=?@[\]^_`', 'ABDFGabcdef'))
    
  return crypt(pw, salt)[-10:]

def nameBlock(post_name, post_tripcode, post_email, post_timestamp_formatted):
  nameblock = ''
  if post_name == '' and post_tripcode == '':
    post_anonymous = True
  else:
    post_anonymous = False
  
  if Settings.ANONYMOUS == '' and (post_anonymous or Settings.FORCED_ANONYMOUS):
    if post_email:
      nameblock += '<a href="mailto:' + post_email + '">'
    nameblock += post_timestamp_formatted
    if post_email:
      nameblock += '</a>'
  else:
    if post_anonymous:
      nameblock += '<span class="postername">'
      if post_email:
        nameblock += '<a href="mailto:' + post_email + '">' + Settings.ANONYMOUS + '</a>'
      else:
        nameblock += Settings.ANONYMOUS
      nameblock += '</span>'
    else:
      nameblock += '<span class="postername">'
      if post_email:
        nameblock += '<a href="mailto:' + post_email + '">'
      if post_name:
        nameblock += post_name
      else:
        if not post_tripcode:
          nameblock += Settings.ANONYMOUS
      if post_tripcode:
        nameblock += '</span><span class="postertrip">' + Settings.POST_TRIPCODE_CHARACTER + post_tripcode
      if post_email:
        nameblock += '</a>'
      nameblock += '</span>'
    nameblock += post_timestamp_formatted
    
  return nameblock

def clickableURLs(message):
  prog = re.compile(r'\b(http|ftp|https)://\S+(\b|/)|\b[-.\w]+@[-.\w]+')
  i = 0
  urllist = []
  while 1:
    m = prog.search(message, i)
    if not m:
      break
    j = m.start()
    urllist.append(message[i:j])
    i = j
    url = m.group(0)
    while url[-1] in '();:,.?\'"<>':
      url = url[:-1]
    i = i + len(url)
    if ':' in url:
      repl = '<a href="%s">%s</a>' % (url, url)
    else:
      repl = '<a href="mailto:%s">&lt;%s&gt;</a>' % (url, url)
    urllist.append(repl)
  j = len(message)
  urllist.append(message[i:j])
  return string.join(urllist, '')

def checkRefLinks(message, parentid):
  board = Settings._BOARD
  # TODO: Make this use a callback and allow reference links to posts in other threads
  message = re.compile(r'&gt;&gt;([0-9]+)').sub('<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(parentid) + r'.html#\1" onclick="javascript:highlight(' + '\'' + r'\1' + '\'' + r', true);">&gt;&gt;\1</a>', message)
  
  return message

def checkQuotes(message):
  message = re.compile(r'^&gt;(.*)$', re.MULTILINE).sub(r'<span class="unkfunc">&gt;\1</span>', message)
  
  return message

def checkAllowedHTML(message):
  message = re.compile(r'&lt;b&gt;(.*)&lt;/b&gt;', re.DOTALL | re.IGNORECASE).sub(r'<b>\1</b>', message)
  message = re.compile(r'&lt;i&gt;(.*)&lt;/i&gt;', re.DOTALL | re.IGNORECASE).sub(r'<i>\1</i>', message)
  message = re.compile(r'&lt;u&gt;(.*)&lt;/u&gt;', re.DOTALL | re.IGNORECASE).sub(r'<u>\1</u>', message)
  message = re.compile(r'&lt;strike&gt;(.*)&lt;/strike&gt;', re.DOTALL | re.IGNORECASE).sub(r'<strike>\1</strike>', message)
  # TODO: Fix double newlines
  message = re.compile(r'&lt;pre&gt;(.*)&lt;/pre&gt;', re.DOTALL | re.IGNORECASE).sub(r'<pre>\1</pre>', message)
  
  return message
