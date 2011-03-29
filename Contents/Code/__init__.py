VIDEO_PREFIX = '/video/nme'
PHOTO_PREFIX = '/photos/nme'

BASE_URL = 'http://www.nme.com%s'
PHOTOS_URL = BASE_URL % '/photos'
VIDEO_URL = BASE_URL % '/nme-video'

FLASH_URL = 'http://c.brightcove.com/services/viewer/federated_f9?&width=%s&height=%s&flashID=myExperience&bgcolor=%s&playerID=%s&publisherID=%s&isVid=true&autoStart=true&%s'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenuVideo, 'NME', ICON, ART)
  Plugin.AddPrefixHandler(PHOTO_PREFIX, MainMenuPictures, 'NME', ICON, ART)

  Plugin.AddViewGroup('Details', viewMode='InfoList', mediaType='items')
  Plugin.AddViewGroup('Pictures', viewMode='Pictures', mediaType='photos')
  Plugin.AddViewGroup('ImageStream', viewMode='ImageStream', mediaType='photos')

  MediaContainer.art = R(ART)
  MediaContainer.title1 = 'NME'
  DirectoryItem.thumb = R(ICON)

  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27'

####################################################################################################
def MainMenuVideo():
  dir = MediaContainer(viewGroup='Details')
  AppendVideos(dir, VIDEO_URL)
  return dir

####################################################################################################
def AppendVideos(dir, url):
  for item in HTML.ElementFromURL(url, errors='ignore').xpath('//div[@id="content"]/div[@class="main_block"]/div//img'):
    title = item.get('alt')
    thumb = item.get('src')
    videoPath = item.xpath('./../../a')[0].get('href')

    # This approach extracts data from destination page which is slow but worth it for the extra meta-data obtained.
    videoPageUrl = HTML.ElementFromURL(BASE_URL % videoPath, errors='ignore', cacheTime=CACHE_1WEEK) # We can cache detail pages longer
    summary = videoPageUrl.xpath('//div[@class="media_details"]/p')[0].text.strip()
    durationText = videoPageUrl.xpath('//p[@class="time"]')[0].text.strip()
    duration = durationText[1+durationText.find(':'):].strip()
    mins = duration[:duration.find(":")]
    secs = duration[1+duration.find(":"):]
    milsecs = 1000*(int(secs) + 60*int(mins))

    bgcolor = videoPageUrl.xpath('//div[@class="media_container"]//object/param[@name="bgcolor"]')[0].get('value')
    bgcolor = bgcolor.replace('#', '%23')
    width = videoPageUrl.xpath('//div[@class="media_container"]//object/param[@name="width"]')[0].get('value')
    height = videoPageUrl.xpath('//div[@class="media_container"]//object/param[@name="height"]')[0].get('value')
    playerId = videoPageUrl.xpath('//div[@class="media_container"]//object/param[@name="playerID"]')[0].get('value')
    publisherId = videoPageUrl.xpath('//div[@class="media_container"]//object/param[@name="publisherID"]')[0].get('value')
    videoPlayer = videoPageUrl.xpath('//div[@class="media_container"]//object/param[@name="@videoPlayer"]')[0].get('value')
    flashUrl = FLASH_URL % (width, height, bgcolor, playerId, publisherId, "@videoPlayer="+videoPlayer)
    dir.Append(WebVideoItem(flashUrl, title=title, summary=summary, thumb=thumb, duration=milsecs))

  if HTML.ElementFromURL(url, errors='ignore').xpath('//a[contains(@title,"Next Page")]'):
    nextUrl = HTML.ElementFromURL(url, errors='ignore').xpath('//a[contains(@title,"Next Page")]')[0].get('href')
    dir.Append(Function(DirectoryItem(Videos, title="More Videos ..."), path=nextUrl))

  return dir

####################################################################################################
# Pagination
def Videos(sender, path):
  dir = MediaContainer(viewGroup='Details')
  url = BASE_URL % path
  AppendVideos(dir, url)
  return dir

####################################################################################################
def MainMenuPictures():
  dir = MediaContainer(viewGroup='Pictures')
  AppendAlbums(dir, PHOTOS_URL)
  return dir

####################################################################################################
def AppendAlbums(dir, url):
  albumPageUrl = HTML.ElementFromURL(url, errors='ignore')

  for item in albumPageUrl.xpath('//div[@class="main_block"]/div[@class="gallery_large"]'):
    title = item.xpath('./h3/a')[0].text.strip()
    albumUrl = item.xpath('./h3/a')[0].get('href')
    thumb = item.xpath('./a/img')[0].get('src').replace(' ','%20')
    dir.Append(Function(DirectoryItem(Album, title=title, thumb=thumb), path=albumUrl))

  if albumPageUrl.xpath('//ul[@class="prev_next"]/li[@class="next"]/a'):
    nextUrl = albumPageUrl.xpath('//ul[@class="prev_next"]/li[@class="next"]/a')[0].get('href')
    dir.Append(Function(DirectoryItem(Albums, title="More Albums ..."), path=nextUrl))
  return dir

####################################################################################################
def Albums(sender, path):
  dir = MediaContainer(viewGroup='Pictures')
  url = BASE_URL % path
  AppendAlbums(dir, url)
  return dir

####################################################################################################
# Actually extract the images and add a photo element. Deals with
# image pagination using a replacement of the image number in
# the original url. Can enter this on image 2 since this is the
# only url extractable from the landing page
def Album(sender, path):
  dir = MediaContainer(viewGroup='ImageStream', title2=sender.itemTitle)
  url = BASE_URL % path
  countStr = HTML.ElementFromURL(url, errors='ignore').xpath('//ul[@class="prev_next top"]/li[@class="count"]')[0].text
  tokens = countStr.split()
  count = int(tokens[2])
  for i in range(1,count):
    # Deal with image navigation
    replacement = '/' + str(i) + '/'
    newUrl = ''
    if url.find('/1/') > -1:
      newUrl = url.replace('/1/', replacement)
    elif url.find('/2/') > -1:
      newUrl = url.replace('/2/', replacement)
    if len(newUrl) > 0:
      photoUrl = HTML.ElementFromURL(newUrl, errors='ignore').xpath('//div[@id="media"]/div//img')[0].get('src').replace(' ','%20')
      try: summary = HTML.ElementFromURL(newUrl, errors='ignore').xpath('//div[@class="media_details InSkinHide"]/p')[0].text_content().strip()
      except: summary = ''
      dir.Append(PhotoItem(photoUrl, title=None, summary=summary))
  return dir
