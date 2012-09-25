BASE_URL = 'http://www.nme.com%s'
PHOTOS_URL = BASE_URL % '/photos'
VIDEO_URL = BASE_URL % '/nme-video'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

TITLE = 'NME'

####################################################################################################
def Start():

  Plugin.AddViewGroup('Details', viewMode='InfoList', mediaType='items')
  Plugin.AddViewGroup('Pictures', viewMode='Pictures', mediaType='photos')

  ObjectContainer.art = R(ART)
  ObjectContainer.title1 = TITLE

  DirectoryObject.thumb = R(ICON)
  NextPageObject.thumb = R(ICON)

  VideoClipObject.thumb = R(ICON)

  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.14 (KHTML, like Gecko) Version/6.0.1 Safari/536.26.14'

####################################################################################################
@handler('/video/nme', TITLE, art = ART, thumb = ICON)
def MainMenuVideo(page_number = 1):

  oc = ObjectContainer(view_group = 'Details')

  url = 'http://www.nme.com/nme-video/search/NME/page/%d' % page_number
  page = HTML.ElementFromURL(url)

  for item in page.xpath('//div[@id="content"]/div[@class="main_block"]//div[contains(@class, "video")]/div/..'):
    title = item.xpath('.//img')[0].get('alt').strip()
    thumb = item.xpath('.//img')[0].get('src')

    url = item.xpath('.//h3/a')[0].get('href')
    if not url.startswith('http://'):
      url = BASE_URL % url

    oc.add(VideoClipObject(
      url = url,
      title = title,
      thumb = thumb
    ))

  # Paging...
  if page.xpath('//a[contains(@title,"Go To The Next Page")]'):
    oc.add(NextPageObject(
      key = Callback(MainMenuVideo, page_number = page_number + 1),
      title = "Next..."
    ))

  return oc

####################################################################################################
@handler('/photos/nme', TITLE, art = ART, thumb = ICON)
def MainMenuPictures(offset = 0):

  oc = ObjectContainer(view_group = 'Pictures')

  url = 'http://www.nme.com/photos/offset/%d' % offset
  page = HTML.ElementFromURL(url)

  for item in page.xpath('//div[@class="gallery_large"]'):
    title = item.xpath('.//h3/a')[0].text.strip()
    thumb = item.xpath('.//img')[0].get('src').replace(' ','%20')

    url = item.xpath('.//h3/a')[0].get('href')
    if not url.startswith('http://'):
      url = BASE_URL % url

    oc.add(PhotoAlbumObject(
      url = url,
      title = title,
      thumb = thumb
    ))

  # Paging...
  if page.xpath('//ul[@class="prev_next"]/li[@class="next"]/a'):
    oc.add(NextPageObject(
      key = Callback(MainMenuPictures, offset = offset + len(oc)),
      title = "Next..."
    ))

  return oc
