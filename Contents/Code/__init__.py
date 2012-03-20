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

  resultsDict = {}

  @parallelize
  def GetVideos():
    content = HTML.ElementFromURL(url, errors='ignore')
    videos = content.xpath('//div[@id="content"]/div[@class="main_block"]/div//img')

    for num in range(len(videos)):
      video = videos[num]

      @task
      def GetVideo(num=num, resultsDict=resultsDict, video=video):
        title = video.get('alt')
        thumb = video.get('src')

        videoPath = video.xpath('./../..//a')[0].get('href')
        videoPage = HTML.ElementFromURL(BASE_URL % videoPath, errors='ignore', cacheTime=CACHE_1WEEK)
        summary = videoPage.xpath('//div[@class="media_details"]/p')[0].text.strip()
        durationText = videoPage.xpath('//p[@class="time"]')[0].text.strip()
        duration = durationText[1+durationText.find(':'):].strip()
        mins = duration[:duration.find(":")]
        secs = duration[1+duration.find(":"):]
        milsecs = 1000*(int(secs) + 60*int(mins))

        bgcolor = videoPage.xpath('//div[@class="media_container"]//object/param[@name="bgcolor"]')[0].get('value')
        bgcolor = bgcolor.replace('#', '%23')
        width = videoPage.xpath('//div[@class="media_container"]//object/param[@name="width"]')[0].get('value')
        height = videoPage.xpath('//div[@class="media_container"]//object/param[@name="height"]')[0].get('value')
        playerId = videoPage.xpath('//div[@class="media_container"]//object/param[@name="playerID"]')[0].get('value')
        publisherId = videoPage.xpath('//div[@class="media_container"]//object/param[@name="publisherID"]')[0].get('value')
        videoPlayer = videoPage.xpath('//div[@class="media_container"]//object/param[@name="@videoPlayer"]')[0].get('value')
        flashUrl = FLASH_URL % (width, height, bgcolor, playerId, publisherId, "@videoPlayer="+videoPlayer)

        resultsDict[num] = WebVideoItem(flashUrl, title=title, summary=summary, thumb=thumb, duration=milsecs)

  keys = resultsDict.keys()
  keys.sort()
  for key in keys:
    dir.Append(resultsDict[key])

  content_page = HTML.ElementFromURL(url, errors='ignore')
  if content_page.xpath('//a[contains(@title,"Next Page")]'):
    nextUrl = content_page.xpath('//a[contains(@title,"Next Page")]')[0].get('href')
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
      photoPage = HTML.ElementFromURL(newUrl, errors='ignore')
      photoUrl = photoPage.xpath('//div[@id="media"]/div//img')[0].get('src').replace(' ','%20')
      photoTitle = photoPage.xpath('//meta[@property="og:title"]')[0].get('content')
      try: summary = HTML.ElementFromURL(newUrl, errors='ignore').xpath('//div[@class="media_details InSkinHide"]/p')[0].text_content().strip()
      except: summary = ''
      dir.Append(PhotoItem(photoUrl, title = photoTitle, summary = summary))
  return dir
