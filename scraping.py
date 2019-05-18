# BUILTIN
import json
import os
import random
import re
import string
import time
# PIP
import requests


class Scraper:

    __slots__ = (
        'log_text',
        'download_links', 'display_links', 'image_links',
        'last_download'
        )

    def __init__(self, log_text):
        self.log_text = log_text

        self.display_links = []  # Links to be displayed in the GUI (gets reset after dl loop)
        self.download_links = []  # DOES get reset after a download loop
        self.image_links = []  # Does NOT get reset after a download loop

        self.last_download = ''  # Track the last downloaded URL to update widgets

    def is_private(self, data):
        """
        Check a soup of an Instagram page to see if the page is private.
        We need to account for scraping a profile as a user gets redirected to a profile
        if they try to access a private post which they are not verified for.
        """
        user = self.get_user(data)
        return user['is_private']

    @staticmethod
    def get_data(soup):
        """
        Extract the JSON data from an Instagram page's HTML source code.
        """
        # Look for script tag holding JSON data, raise if none found
        for s in soup.find_all('script'):
            if s.text.startswith('window._sharedData'):
                script = s
                break
        else:
            raise ValueError('Could not find appropriate script tag in BeautifulSoup'
                             '(None starting with "window._sharedData").')

        # Remove 'window._sharedData = ' from the start, as well as the trailing semicolon
        # data = json.loads(script.text[21:-1])
        data = json.loads('='.join(script.text.split('=')[1:]).strip()[:-1])
        return data

    @staticmethod
    def get_user(data):
        """
        Get the user dict from JSON data.
        """
        # Scraped a profile
        if 'ProfilePage' in data['entry_data'].keys():
            user = data['entry_data']['ProfilePage'][0]['graphql']['user']
        # Scraped a post
        else:
            user = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['owner']

        return user

    def extract_ig_images(self, data):
        """
        Extract all image URLs from the HTML source code of an Instagram post.
        (Also extracts video URLs (got added later on))
        """
        # Private page which is not being followed
        if 'PostPage' not in data['entry_data'].keys():
            user = self.get_user(data)
            self.log_text.newline(f'Cannot access profile of {user["username"]} - Skipping!')
            return

        # Bunch of fucking magic right here
        shortcode_media = data['entry_data']['PostPage'][0]['graphql']['shortcode_media']

        # Album
        if 'edge_sidecar_to_children' in shortcode_media.keys():
            edges = shortcode_media['edge_sidecar_to_children']['edges']

            for index, edge in enumerate(edges):
                self.append_link(edge['node']['display_url'],
                                 type_='image', index=index, list_=edges)

                if 'video_url' in edge['node'].keys():
                    self.append_link(edge['node']['video'],
                                     type_='video', index=index, list_=edges)

        # Single image/video
        else:
            self.append_link(shortcode_media['display_url'], type_='image')

            if 'video_url' in shortcode_media.keys():
                self.append_link(shortcode_media['video_url'], type_='video')

    def extract_imgur_images(self, soup):
        """
        Extract all images from an imgur post.
        JSON data handling taken from here:
        https://old.reddit.com/r/learnpython/comments/93yiti/
        scraping_images_from_imgur_using_selenium_and/e3h19xl/
        """
        # The split has multiple spaces after 'image'
        # to avoid errors due to "image " being in the title/description
        # Multiple spaces will get escaped in the html source code, like so:
        # "title":"image image\u00a0 \u00a0 \u00a0image"
        try:
            script = soup.find_all('script')[13]
            text = script.get_text()
            data_str = text.split('image   ')[1].strip(' :').split('group')[0].strip(' \n,')
        # Sometimes the index for the script is different, not sure why though :(
        except IndexError:
            script = soup.find_all('script')[29]
            text = script.get_text()
            data_str = text.split('image   ')[1].strip(' :').split('group')[0].strip(' \n,')
        data = json.loads(data_str)

        # Log the script tag's index for debugging purposes
        script_tags = soup.find_all('script')
        self.log_text.newline('Script tag of Imgur post containing JSON data'
                              f' is at index {script_tags.index(script)} / {len(script_tags)}')

        if 'album_images' in data.keys():
            urls = [f'https://i.imgur.com/{image["hash"]}{image["ext"]}'
                    for image in data['album_images']['images']]
            for index, url in enumerate(urls):
                self.append_link(url, type_='image', index=index, list_=urls)
        else:
            url = f'https://i.imgur.com/{data["hash"]}{data["ext"]}'
            self.append_link(url)

    def extract_yt_thumbnail(self, url):
        """
        Construct a link for the maxresdefault thumbnail of a YouTube video.
        """
        # Second splits to get rid of additional arguments in the URL
        if 'watch?v=' in url:
            video_id = url.split('watch?v=')[1].split('?')[0]
        else:
            video_id = url.split('/')[-1].split('?')[0]

        thumbnail_url = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
        # thumbnail_url = f'https://img.youtube.com/vi/{video_id}/0.jpg'
        self.append_link(thumbnail_url)

    def append_link(self, link, type_='image', index=None, list_=None):
        """
        Append a link to the link lists and log info.
        """
        self.download_links.append(link)
        self.image_links.append(self.download_links[-1])

        if index is not None and list_ is not None:
            self.log_text.newline(f'Added {type_} of post #{index+1} / {len(list_)}:')
        else:
            self.log_text.newline(f'Added singular {type_}:')
        self.log_text.newline(f' -  {self.download_links[-1]}\n')

    def download_files(self):
        """
        Download all the collected files.
        """
        if not self.download_links:
            return

        file_name_re = re.compile(r'.+.(?:jpg|png|gif|mp4)')
        dl_folder = 'downloads'

        if not os.path.exists(dl_folder) or not os.path.isdir(dl_folder):
            os.mkdir(dl_folder)

        for index, link in enumerate(self.download_links):
            file_name = link.split('/')[-1]
            # Extra check needed for IG file names
            file_name = file_name_re.match(file_name).group(0)

            # Need to avoid same file names for YouTube thumbnails
            if file_name == 'maxresdefault.jpg':
                rnd_str = ''.join([random.choice(string.ascii_letters + string.digits)
                                   for _ in range(10)])
                file_name = f'maxresdefault_{rnd_str}.jpg'
            file_dst = os.path.join(os.getcwd(), dl_folder, file_name)

            if os.path.exists(file_dst):
                self.log_text.newline(f'File {index+1} / {len(self.download_links)}'
                                      ' already present, skipping')
            else:
                with open(file_dst, 'wb') as dl_file:
                    res = requests.get(link)
                    dl_file.write(res.content)

                    self.log_text.newline(f'Downloaded file {index+1}'
                                          f' / {len(self.download_links)}')

            self.last_download = link
            time.sleep(0.5)
