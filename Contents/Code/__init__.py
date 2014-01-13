BASE_URL = 'http://www.nme.com'
VIDEO_URL = '%s/nme-video' % BASE_URL
TITLE = 'NME'

####################################################################################################
def Start():

  ObjectContainer.title1 = TITLE
  HTTP.CacheTime = CACHE_1HOUR
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.14 (KHTML, like Gecko) Version/6.0.1 Safari/536.26.14'

####################################################################################################
@handler('/video/nme', TITLE)
def MainMenuVideo(page=1):

  oc = ObjectContainer()
  url = 'http://www.nme.com/nme-video/search/NME/page/%d' % page
  html = HTML.ElementFromURL(url)

  for item in html.xpath('//div[@id="content"]/div[@class="main_block"]//div[contains(@class, "video")]/div/..'):
    title = item.xpath('.//img/@alt')[0].strip()
    thumb = item.xpath('.//img/@src')[0]
    url = item.xpath('.//h3/a/@href')[0]

    if not url.startswith('http://'):
      url = '%s%s' % (BASE_URL, url)

    oc.add(VideoClipObject(
      url = url,
      title = title,
      thumb = thumb
    ))

  # Paging...
  if html.xpath('//a[contains(@title,"Go To The Next Page")]'):
    oc.add(NextPageObject(
      key = Callback(MainMenuVideo, page=page+1),
      title = "Next..."
    ))

  return oc
