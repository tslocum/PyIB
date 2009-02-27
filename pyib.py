#!/usr/bin/python2.4
#!/usr/bin/env python
# Remove the first line to use the env command to locate python

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

# Set to True to disable PyIB's exception routing and enable profiling
_DEBUG = False

# Set to True to save performance data to pyib.txt
_LOG = False

class pyib(object):
  def __init__(self, environ, start_response):
    global _DEBUG
    self.environ = environ
    if self.environ["PATH_INFO"].startswith("/pyib.py/"):
      self.environ["PATH_INFO"] = self.environ["PATH_INFO"][8:]
      
    self.start = start_response
    self.formdata = getFormData(self)
    self.output = ""
    self.handleRequest()

    logTime("**Start**")
    if _DEBUG:
      import hotshot
      prof = hotshot.Profile("pyib.prof")
      prof.runcall(self.run)
      prof.close()
    else:
      try:
        self.run()
      except Exception, message:
        self.error(message)
    logTime("**End**")
    
    if _LOG:
      logfile = open(Settings.ROOT_DIR + "/pyib.txt", "w")
      logfile.write(logTimes())
      logfile.close()
      
  def __iter__(self):
    self.handleResponse()
    self.start("200 OK", self.headers)
    yield self.output

  def error(self, message):
    self.output += renderTemplate("error.html", {"error": message, "navbar": False})
  
  def handleRequest(self):
    self.headers = [("Content-Type", "text/html")]
    self.handleCookies()
    
  def handleResponse(self):
    if self._cookies is not None:
      for cookie in self._cookies.values():
        self.headers.append(("Set-Cookie", cookie.output(header="")))
    
  def handleCookies(self):
    self._cookies = SimpleCookie()
    self._cookies.load(self.environ.get("HTTP_COOKIE", ""))

  def run(self):
    UpdateDb("DELETE FROM `bans` WHERE `until` != 0 AND `until` < " + str(timestamp())) # Delete expired bans
    if self.environ["PATH_INFO"] == "/post":
      try:
        if self.formdata["board"]:
          board = FetchOne("SELECT * FROM `boards` WHERE `dir` = '%s' LIMIT 1" % _mysql.escape_string(self.formdata["board"]))
          if not board:
            raise Exception
          board = setBoard(self.formdata["board"])
        else:
          raise Exception
      except:
        raise Exception, "Invalid board supplied"

      if addressIsBanned(self, self.environ["REMOTE_ADDR"], board["dir"]):
        return
      
      post = Post(board["id"])
      post["ip"] = self.environ["REMOTE_ADDR"]
      
      try:
        parent = cleanString(self.formdata["parent"])
        try:
          parent_post = FetchOne("SELECT COUNT(*) FROM `posts` WHERE `id` = %s AND `parentid` = 0 AND `boardid` = %s LIMIT 1" % (parent, board["id"]), 0)
          if int(parent_post[0]) > 0:
            post["parentid"] = parent
          else:
            raise Exception
        except:
          raise Exception, "That parent post ID is invalid."
      except:
        pass
      
      if not checkNotFlooding(post):
        raise Exception, "Flood detected.  Please try again"
      
      try:
        if not board["settings"]["forced_anonymous"]:
          post["name"] = cleanString(self.formdata["name"])
          setCookie(self, "pyib_name", self.formdata["name"])
      except:
        pass
      
      if post["name"] != "":
        name_match = re.compile(r"(.*)#(.*)").match(post["name"])
        if name_match:
          if name_match.group(2):
            post["name"] = name_match.group(1)
            post["tripcode"] = tripcode(name_match.group(2))
  
      try:
        post["email"] = cleanString(self.formdata["email"])
      except:
        pass
      
      try:
        if not board["settings"]["disable_subject"] and not post["parentid"]:
          post["subject"] = cleanString(self.formdata["subject"])
      except:
        pass
      
      try:
        post["message"] = clickableURLs(cgi.escape(self.formdata["message"]).rstrip()[0:8000])
        post["message"] = onlyAllowedHTML(post["message"])
        if Settings.USE_MARKDOWN:
          post["message"] = markdown(post["message"])
        if post["parentid"] != 0:
          post["message"] = checkRefLinks(post["message"], post["parentid"])
        post["message"] = checkQuotes(post["message"])
        if not Settings.USE_MARKDOWN:
          post["message"] = post["message"].replace("\n", "<br>")
      except:
        pass
      
      try:
        post["password"] = self.formdata["password"]
        setCookie(self, "pyib_password", post["password"])
      except:
        pass
  
      # Create a single datetime now so everything syncs up
      t = datetime.datetime.now()
  
      try:
        if self.formdata["file"]:
          post = processImage(post, self.formdata["file"], t)
      except Exception, message:
        raise Exception, "Unable to process image:\n\n" + str(message)
  
      if not post["file"]:
        if not post["parentid"]:
          raise Exception, "Please upload an image to create a new thread"
        if not post["message"]:
          raise Exception, "Please upload an image, or enter a message"
  
      post["timestamp_formatted"] = formatDate(t)
      post["timestamp"] = post["bumped"] = timestamp(t)
      post["nameblock"] = nameBlock(post["name"], post["tripcode"], post["email"], post["timestamp_formatted"])

      # Insert the post, then run the timThreads function to make sure the board doesn't exceed the page limit
      logTime("Inserting post")
      postid = post.insert()
      logTime("Trimming threads")
      trimThreads()

      logTime("Updating thread")
      if post["parentid"]:
        if post["email"].lower() != "sage":
          UpdateDb("UPDATE `posts` SET bumped = %d WHERE `id` = '%s' AND `boardid` = '%s' LIMIT 1" % (timestamp(t), str(post["parentid"]), board["id"]))
          setCookie(self, "pyib_email", self.formdata["email"])
          
        threadUpdated(post["parentid"])
        self.output += '<meta http-equiv="refresh" content="0;url=%s/res/%s.html">--&gt; --&gt; --&gt;' % (Settings.BOARDS_URL + board["dir"], str(post["parentid"]))
      else:
        threadUpdated(postid)
        self.output += '<meta http-equiv="refresh" content="0;url=%s/">--&gt; --&gt; --&gt;' % (Settings.BOARDS_URL + board["dir"])
    else:
      path_split = self.environ["PATH_INFO"].split("/")
      caught = False
  
      if len(path_split) > 1:
        if path_split[1] == "delete":
          caught = True
          board = None
          delete_id = 0
          imageonly = False
          try:
            if self.formdata["board"]:
              board = setBoard(self.formdata["board"])
          except:
            pass
          if board:
            if self.formdata["password"] != "":
              try:
                delete_id = int(self.formdata["delete"])
              except:
                pass
              if delete_id > 0:
                post = FetchOne("SELECT * FROM `posts` WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], str(delete_id)))
                if post:
                  if post["password"] == self.formdata["password"]:
                    try:
                      if self.formdata["imageonly"]:
                        # They just want to delete the associated image, not the whole post
                        imageonly = True
                    except:
                      pass
                    if imageonly:
                      if post["file"] != "":
                        if post["message"] != "":
                          deleteFile(post)
                          UpdateDb("UPDATE `posts` SET `file` = '', `file_hex` = '' WHERE `boardid` = %s AND `id` = %s LIMIT 1" % (board["id"], str(delete_id)))
                        else:
                          # The post has no message, we should delete the entire post
                          deletePost(delete_id)
                    else:
                      deletePost(delete_id)
                    if post["parentid"] == "0":
                      regenerateFrontPages()
                    else:
                      threadUpdated(post["parentid"])
                    if imageonly:
                      self.output += "File successfully deleted from post."
                    else:
                      self.output += "Post successfully deleted."
                  else:
                    self.error("Incorrect password.")
                else:
                  self.error("Unable to locate a post with that ID.  The post may have already been deleted.")
              else:
                self.error("Unable to detect selected post.  You may have not checked a checkbox, or checked more than one checkbox.")
            else:
              self.error("Please enter a password.")
          else:
            self.error("Invalid board supplied.")
        elif path_split[1] == "manage":
          caught = True
          manage.manage(self, path_split)
          
      if not caught:
        # Redirect the user back to the front page
        self.output += '<meta http-equiv="refresh" content="0;url=%s">--&gt; --&gt; --&gt;' % Settings.HOME_URL
        
if __name__ == "__main__":
  from fcgi import WSGIServer

  # Psyco is not required, however it will be used if available
  try:
    import psyco
    logTime("Psyco has been installed")
    psyco.bind(tenjin.helpers.to_str)
    psyco.bind(pyib.run, 2)
    psyco.bind(getFormData)
    psyco.bind(setCookie)
    psyco.bind(threadUpdated)
    psyco.bind(processImage)
  except:
    pass
  
  WSGIServer(pyib).run()
