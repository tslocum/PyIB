import struct
import math
import random
import os
from StringIO import StringIO

from settings import Settings
from database import *
from framework import *

def processImage(post, data, t):
  """
  Take all post data from <post>, process uploaded file in <data>, and calculate
  file names using datetime <t>
  Returns updated <post> with file and thumb values
  """
  board = Settings._BOARD
  
  content_type, width, height = getImageInfo(data)
  if content_type in ['image/png', 'image/jpeg', 'image/gif']:
    is_not_duplicate = checkFileNotDuplicate(data)
    if is_not_duplicate[0]:
      if content_type == 'image/png':
        file_extension = '.png'
      elif content_type == 'image/jpeg':
        file_extension = '.jpg'
      elif content_type == 'image/gif':
        file_extension = '.gif'
          
      file_name = str(timestamp(t)) + str(random.randint(10, 99))
      file_thumb_name = file_name + 's' + file_extension
      file_name += file_extension
  
      file_path = Settings.ROOT_DIR + board['dir'] + '/src/' + file_name
      file_thumb_path = Settings.ROOT_DIR + board['dir'] + '/thumb/' + file_thumb_name
        
      f = open(file_path, 'w')
      try:
        f.write(data)
      finally:
        f.close()
  
      if post['parentid'] == 0:
        maxsize = Settings.MAX_DIMENSION_FOR_OP_IMAGE
      else:
        maxsize = Settings.MAX_DIMENSION_FOR_REPLY_IMAGE
      
      file_thumb_width, file_thumb_height = getThumbDimensions(width, height, maxsize)
      
      os.system('convert ' + file_path + ' -resize ' + str(file_thumb_width) + 'x' + str(file_thumb_height) + ' -quality 90 ' + file_thumb_path)
      
      try:
        open(file_thumb_path)
      except:
        raise Exception, 'Thumbnail creation failed'
  
      post['file'] = file_name
      post['image_width'] = width
      post['image_height'] = height
      
      post['thumb'] = file_thumb_name
      post['thumb_width'] = file_thumb_width
      post['thumb_height'] = file_thumb_height
      
      post['file_size'] = len(data)
      if Settings.IMAGE_SIZE_UNIT == 'B':
        post['file_size_formatted'] = str(post['file_size']) + ' B'
      else:
        post['file_size_formatted'] = str(long(post['file_size'] / 1024)) + ' KB'
  
      post['file_hex'] = getMD5(data)

      return post
    else:
      raise Exception, 'That image has already been posted <a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(is_not_duplicate[1]) + '.html#' + str(is_not_duplicate[2]) + '">here</a>.'
  else:
    raise Exception, 'Invalid file type'

def getImageInfo(data):
  data = str(data)
  size = len(data)
  height = -1
  width = -1
  content_type = ''

  # handle GIFs
  if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
    # Check to see if content_type is correct
    content_type = 'image/gif'
    w, h = struct.unpack("<HH", data[6:10])
    width = int(w)
    height = int(h)

  # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
  # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
  # and finally the 4-byte width, height
  elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
        and (data[12:16] == 'IHDR')):
    content_type = 'image/png'
    w, h = struct.unpack(">LL", data[16:24])
    width = int(w)
    height = int(h)

  # Maybe this is for an older PNG version.
  elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
    # Check to see if we have the right content type
    content_type = 'image/png'
    w, h = struct.unpack(">LL", data[8:16])
    width = int(w)
    height = int(h)

  # handle JPEGs
  elif (size >= 2) and data.startswith('\377\330'):
    content_type = 'image/jpeg'
    jpeg = StringIO(data)
    jpeg.read(2)
    b = jpeg.read(1)
    try:
      while (b and ord(b) != 0xDA):
        while (ord(b) != 0xFF): b = jpeg.read
        while (ord(b) == 0xFF): b = jpeg.read(1)
        if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
          jpeg.read(3)
          h, w = struct.unpack(">HH", jpeg.read(4))
          break
        else:
          jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
        b = jpeg.read(1)
      width = int(w)
      height = int(h)
    except struct.error:
      pass
    except ValueError:
      pass

  return content_type, width, height

def getThumbDimensions(width, height, maxsize):
  """
  Calculate dimensions to use for a thumbnail with maximum width/height of
  <maxsize>, keeping aspect ratio
  """
  wratio = (float(maxsize) / float(width))
  hratio = (float(maxsize) / float(height))
  
  if (width <= maxsize) and (height <= maxsize):
    return width, height
  else:
    if (wratio * height) < maxsize:
      thumb_height = math.ceil(wratio * height)
      thumb_width = maxsize
    else:
      thumb_width = math.ceil(hratio * width)
      thumb_height = maxsize
  
  return int(thumb_width), int(thumb_height)

def checkFileNotDuplicate(data):
  """
  Check that the file <data> does not already exist in a live post on the
  current board by calculating its hex and checking it against the database
  """
  board = Settings._BOARD
  
  file_hex = getMD5(data)
  post = FetchOne("SELECT `id`, `parentid` FROM `posts` WHERE `file_hex` = '" + file_hex + "' AND `boardid` = " + board['id'] + " LIMIT 1")
  if post:
    if int(post['parentid']) != 0:
      return False, post['parentid'], post['id']
    else:
      return False, post['id'], post['id']
  else:
    return True, 0, 0
