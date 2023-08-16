import scrapy
from ..settings import unsplash_api, unsplash_views
import json
from datetime import datetime
from scrapy import Selector
from ..utils import utils
class UnsplashSpider(scrapy.Spider):
    http = 'user'
    
    name = 'unsplash'
    init_url = 'https://unsplash.com'
    headers = {
            'Accept'            : '*/*',
            'Accept-Encoding'   : 'gzip, deflate, br',
            'Accept-Language'   : 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type'      : 'application/json',
            'Cookie'            : 'xp-promote-plus-photos=control; uuid=51033900-01b8-11ee-a295-339a6f11fd53; azk=51033900-01b8-11ee-a295-339a6f11fd53; azk-ss=true; _gid=GA1.2.419151968.1686059455; _ga_21SLH4J369=GS1.1.1686230946.11.0.1686230946.0.0.0; _sp_ses.0295=*; _ga=GA1.2.1657556800.1685507100; _gat=1; lux_uid=168623094872833036; _sp_id.0295=ccfdf856-461e-4de3-bf98-081e60d86b47.1685507099.11.1686230957.1686197549.cd275a59-a298-4ad6-98b0-e4f36d371d1e.d5ea7bcc-7823-4add-8a52-24c940176209.11d24d37-6a7a-4613-8582-25ad8a6328bc.1686230947184.3',
            'User-Agent'        : utils.random_user_agent(),
    }  
    photo_detail_api = 'https://unsplash.com/napi/photos/{}'
    

    def format_datetime(self, date_string):      
        datetime_obj   = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        fomartted_date = datetime_obj.strftime("%Y-%m-%d")
        return fomartted_date
    
    def get_image_size(self, image_dict, initial_width, initial_height):
        size   = []
        for value in list(image_dict.values()):
            width  = 0
            height = 0
            if '&w=' in value:
                width  = int(value.split('&w=')[-1])
                ratio  = initial_width / width
                height = int(initial_height / ratio)
            else:
                continue
            url = value
            size.append({
                'width'  : width,
                'height' : height,
                'url'    : url
            })
        return size

    def start_requests(self):
        tag = self.tag
        for i in range(1, 2001):
            yield scrapy.Request(
                url      = unsplash_api.format(tag, i),
                headers  = self.headers,
                callback = self.get_all_photos,
                meta     = {'delay_request_by': 3}
            )

    def get_all_photos(self, response):
        
        data = json.loads(response.body)
        photos = data['results']

        for photo in photos:

            item     = {}
            width    = photo['width']
            height   = photo['height']

            photo_id = photo['id']
            owner_id = photo['user']['id']
            owner    = photo['user']['username']
            image    = f'{self.name}_{photo_id}_{owner_id}'
            page     = photo['links']['html']
            uploaded = self.format_datetime(photo['created_at'])
            size = self.get_image_size(photo['urls'], width, height )
            size.append({
                'url'   : photo['urls']['full'],
                'height': height,
                'width' : width 
            })

            image_urls = [ size[0].get('url') ]

            item = {
                **item,
                'image': image,
                'page': page,
                'uploaded': uploaded,
                'owner': owner,
                'size': size,
                'image_urls': image_urls
            }

            yield scrapy.Request(
                url = self.photo_detail_api.format(photo_id),
                callback = self.get_photo_details,
                meta = {
                    'item': item,
                    'delay_request_by': 3
                }
            )
    
    def get_photo_details(self, response):

        item  = response.meta['item']
        photo = json.loads(response.body)

        exif  = photo.get('exif')
        # Return if don't have exif or all values of exif are null
        if (
            not exif 
            or
            all(value is None for value in exif.values())
        ) : return

        views = int(photo['views'])

        # Return when views don't match condition
        # if not (views >= unsplash_views): return

        likes = int(photo['likes'])
        download = int(photo['downloads'])
        stat = {
            'views'   : views,
            'likes'   : likes,
            'download': download,
            'comments': None
        }

        exif = {
            'make'         : exif.get('make') or "",
            'model'        : exif.get('model') or "",
            'shutterspeed' : f"{exif.get('exposure_time')}s" or "",
            'fstop'        : f"f/{exif.get('aperture')}" or "",
            'iso'          : str(exif.get('iso')) or "",
            'focallength'  : f"{exif.get('focal_length')}mm" or "",
            "lens"         : ""
        }

        title = photo['alt_description']

        position = photo['location']['position']
        gps = {
            'latitude': position.get('latitude') or 0,
            'longitude': position.get('longitude') or 0
        }

        tags = [ tag.get('title') for tag in photo['tags'] ]
        license = ""

        item = {
            **item,
            'exif': exif,
            'stat': stat,
            'tags': tags,
            'license': license,
            'title': title,
            'gps': gps,        
        }
        
        tag = ""
        if self.tag == 'long%20exposure':
            tag = 'long exposure'
        else:
            tag = self.tag

 
        yield {
            "image"      : item['image'],                        # Specify the name of the image (we can point out the image_id and owner_id)
            "source"     : self.init_url,                        # Specify the source
            "page"       : item['page'],                         # Specify the url
            "exif"       : item['exif'],                         # Specify the exif of the image: make, model, lens, shutterspeed, fstop, iso, focallength
            "stat"       : item['stat'],                         # Specify the statistic based on client's requirements: downloads, views, likes comments
            "tags"       : item['tags'],                         # Specify all tags having on website of this image
            "license"    : item['license'],                      # Specify the lisence on the image website
            "uploaded"   : item['uploaded'],                     # Specify the date of image uploaded
            "owner"      : item['owner'],                        # Specify the owner of the image
            "title"      : item['title'],                        # Specify the title of image
            "gps"        : item['gps'],                          # Specify the longtitude and latitude
            "size"       : item['size'],                         # Specify all sizes of this image
            "root_class" : tag,                             # Specify the root_class (the tag when you search for it)
            "sub_class"  : tag,                             # Specify some subclass of the image
            "rating"     : None,                                 # Specify the rating of the image
            "crawl_id"   : 1,                                    # Generate crawl id
            "crawl_note" : "No",                                 # Generate crawl note

            #"crawl_count": self.count,                          # Crawl Count Is Set Based on the Pipelines

            "image_urls" : item['image_urls'],                   # Field to download image
        }