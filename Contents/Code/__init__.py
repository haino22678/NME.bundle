import re, string, datetime
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

VIDEO_PREFIX      = "/video/nme"
PHOTO_PREFIX      = "/photos/nme"

BASE_URL = "http://www.nme.com%s"
PHOTOS_URL = BASE_URL % "/photos"
VIDEO_URL = BASE_URL % "/video"
PAGED_VIDEO_URL = "http://www.nme.com/video/tags/NME/offset/%d"

FLASH_URL = "http://c.brightcove.com/services/viewer/federated_f9?&width=%s&height=%s&flashID=myExperience&bgcolor=%s&playerID=%s&publisherID=%s&isVid=true&autoStart=true&%s"
CACHE_INTERVAL    = 1800
ICON = "icon-default.png"

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenuVideo, "NME", ICON, "art-default.png")
  Plugin.AddPrefixHandler(PHOTO_PREFIX, MainMenuPictures, "NME", ICON, "art-default.png")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("Pictures", viewMode="Pictures", mediaType="photos")
  Plugin.AddViewGroup("ImageStream", viewMode="ImageStream", mediaType="photos")
  MediaContainer.art = R('art-default.png')
  MediaContainer.title1 = 'NME'
  HTTP.SetCacheTime(CACHE_INTERVAL)
  
def MainMenuVideo():
    dir = MediaContainer(viewGroup='Details', mediaType='video')  
    AppendVideos(dir, VIDEO_URL)
    return dir
    
def AppendVideos(dir, url):
    for item in XML.ElementFromURL(url, True, errors='ignore').xpath('//div[@id="content"]/div[@class="main_block"]/div/a'):
        title = item.xpath('img')[0].get('alt')
        thumb = item.xpath('img')[0].get('src')
        videoPath = item.get('href')
        #
        # This approach extracts data from destination page which is slow but worth it for the extra
        # meta-data obtained.
        videoPageUrl = BASE_URL % videoPath
        summary = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@class="media_details"]/p')[0].text.strip()
        durationText = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//p[@class="time"]')[0].text.strip()
        duration = durationText[1+durationText.find(':'):].strip()
        mins = duration[:duration.find(":")]
        secs = duration[1+duration.find(":"):]
        milsecs = 1000*(int(secs) + 60*int(mins))
        
        bgcolor = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@class="media_container"]//object/param[@name="bgcolor"]')[0].get('value')
        bgcolor = bgcolor.replace('#', '%23')
        width = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@class="media_container"]//object/param[@name="width"]')[0].get('value')
        height = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@class="media_container"]//object/param[@name="height"]')[0].get('value')
        playerId = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@class="media_container"]//object/param[@name="playerID"]')[0].get('value')
        publisherId = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@class="media_container"]//object/param[@name="publisherID"]')[0].get('value')
        videoPlayer = XML.ElementFromURL(videoPageUrl, True, errors='ignore').xpath('//div[@class="media_container"]//object/param[@name="@videoPlayer"]')[0].get('value')
        flashUrl = FLASH_URL %(width, height, bgcolor, playerId, publisherId, "@videoPlayer="+videoPlayer)
        dir.Append(WebVideoItem(flashUrl, title=title, summary=summary, thumb=thumb, duration=milsecs))
    if(XML.ElementFromURL(url, True, errors='ignore').xpath('//ul[@class="prev_next"]/li[@class="next"]/a')):
        nextUrl = XML.ElementFromURL(url, True, errors='ignore').xpath('//ul[@class="prev_next"]/li[@class="next"]/a')[0].get('href')
        dir.Append(Function(DirectoryItem(Videos, title="More Videos ...", thumb=R(ICON)), path=nextUrl))
    
# Pagination
def Videos(sender, path):
    dir = MediaContainer(viewGroup='Details', mediaType='pictures')
    url = BASE_URL % path
    AppendVideos(dir, url)
    return dir

#########################################################
def MainMenuPictures():
  dir = MediaContainer(viewGroup='Pictures', mediaType='pictures')
  AppendAlbums(dir, PHOTOS_URL)
  return dir

##########################################
# Have to deal with the entry page separate from the rest since the
# first entry isn't in the list
def AppendAlbums(dir, url):
  frontPageTitle = XML.ElementFromURL(url, True, errors='ignore').xpath('//meta[@name="Description"]')[0].get('content').strip()
  albumUrl = XML.ElementFromURL(url, True, errors='ignore').xpath('//div[@class="media_container"]//a')[0].get('href')
  thumb = XML.ElementFromURL(url, True, errors='ignore').xpath('//div[@class="media_container"]//a/img')[0].get('src')
  dir.Append(Function(DirectoryItem(Album, title=frontPageTitle, thumb=thumb), path=albumUrl))
  for item in XML.ElementFromURL(url, True, errors='ignore').xpath('//div[@class="main_block"]/div[@class="article_small last"]'):
      title = item.xpath('h3/a')[0].text.strip()
      albumUrl = item.xpath('h3/a')[0].get('href')
      thumb = item.xpath('a/img')[0].get('src').replace(' ','%20')
      dir.Append(Function(DirectoryItem(Album, title=title, thumb=thumb), path=albumUrl))
  if(XML.ElementFromURL(url, True, errors='ignore').xpath('//ul[@class="prev_next"]/li[@class="next"]/a')):
     nextUrl = XML.ElementFromURL(url, True, errors='ignore').xpath('//ul[@class="prev_next"]/li[@class="next"]/a')[0].get('href')
     dir.Append(Function(DirectoryItem(Albums, title="More Albums ...", thumb=R(ICON)), path=nextUrl))
  return dir

##########################################
# The enables pagination since I don't think
# we can recurse on the main menu function (no sender)
def Albums(sender, path):
  dir = MediaContainer(viewGroup='Pictures', mediaType='pictures')
  url = BASE_URL % path
  AppendAlbums(dir, url)
  return dir
  
#########################################################
# Actually extract the images and add a photo element. Deals with
# image pagination using a replacement of the image number in
# the original url. Can enter this on image 2 since this is the
# only url extractable from the landing page
#
def Album(sender, path):
  dir = MediaContainer(viewGroup='ImageStream', title2=sender.itemTitle)
  url = BASE_URL % path
  countStr = XML.ElementFromURL(url,True, errors='ignore').xpath('//ul[@class="prev_next top"]/li[@class="count"]')[0].text
  tokens = countStr.split()
  count = int(tokens[2])
  for i in range(1,count):
    # Deal with image navigation
    replacement = "/"+str(i)+"/"
    newUrl = ""
    if url.find("/1/") > -1:
      newUrl = url.replace("/1/", replacement)
    elif url.find("/2/") > -1:
      newUrl = url.replace("/2/", replacement)
    if len(newUrl) > 0:
      photoUrl = XML.ElementFromURL(newUrl,True, errors='ignore').xpath('//div[@id="media"]/div//img')[0].get('src').replace(' ','%20')
      summary = ""
      if(XML.ElementFromURL(newUrl,True, errors='ignore').xpath('//div[@class="media_details InSkinHide"]/h1/span')):
        summary = XML.ElementFromURL(newUrl,True, errors='ignore').xpath('//div[@class="media_details InSkinHide"]/p')[0].text.strip()
      dir.Append(PhotoItem(photoUrl, title=None, summary=summary))
  return dir
  
