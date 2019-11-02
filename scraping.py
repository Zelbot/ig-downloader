# BUILTIN
import json
import os
import random
import re
import string
import time
# PIP
import requests
import youtube_dl
from bs4 import BeautifulSoup


class YDLLogger:
    """
    (Do not) log specific messages.
    Raise error if a file is already present so we can catch it
    and say if a file was downloaded or not.
    """
    already_downloaded = 'has already been downloaded'

    def debug(self, msg):
        if msg.endswith(self.already_downloaded):
            file = msg.replace('[download]', '')
            file = file.replace(self.already_downloaded, '')
            raise youtube_dl.utils.SameFileError(f'{file.strip()} already present!')

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class Scraper:

    __slots__ = (
        'log_text', 'download_tracking_label',
        'download_links', 'display_links', 'tracking_links',
        'last_download', 'youtube_ids',
        )

    def __init__(self, log_text, download_tracking_label):
        self.log_text = log_text  # tk.Widget of the Application class
        self.download_tracking_label = download_tracking_label  # tk.Widget of the Application class

        self.display_links = []  # Links to be displayed in the GUI (gets reset after dl loop)
        self.download_links = []  # DOES get reset after a download loop
        self.tracking_links = []  # Does NOT get reset after a download loop

        self.last_download = ''  # Track the last downloaded URL to update widgets
        self.youtube_ids = []  # Track YouTube video-IDs to add them to the file names

    @staticmethod
    def get_random_string(amount=10):
        """
        Generate a random string.
        Used to avoid same file names when downloading.
        """
        return ''.join([random.choice(string.ascii_letters + string.digits)
                        for _ in range(amount)])

    def append_link(self, link, type_='image', index=None, list_=None):
        """
        Append a link to the link lists and log info.
        """
        self.download_links.append(link)
        self.tracking_links.append(self.download_links[-1])

        if index is not None and list_ is not None:
            self.log_text.newline(f'Added {type_} of post #{index+1} / {len(list_)}:')
        else:
            self.log_text.newline(f'Added singular {type_}:')
        self.log_text.newline(f' -  {self.download_links[-1]}\n')

        self.download_tracking_label.configure(
            text=f'Downloaded 0 / {len(self.download_links)} files'
        )

    def get_imgur_data(self, soup):
        """
        Extract the JSON data from an Imgur post's HTML source code.
        """
        # The split for the data_str has multiple spaces after 'image'
        # to avoid errors due to "image " being in the title/description
        # Multiple spaces will get escaped in the html source code, like so:
        # "title":"image image\u00a0 \u00a0 \u00a0image"

        script_tags = soup.find_all('script')
        # The index of the script tag varies so a loop is safest
        for script in script_tags:
            try:
                text = script.get_text()
                data_str = text.split('image   ')[1].strip(' :').split('group')[0].strip(' \n,')
                break
            except IndexError:
                pass
        else:
            message = 'Could not locate JSON data in Imgur post'
            self.log_text.newline(message)
            # raise ValueError(message)
            return None

        # Log the script tag's index for debugging purposes
        self.log_text.newline('Script tag of Imgur post containing JSON data'
                              f' is at index {script_tags.index(script)}'
                              f' / {len(script_tags)}')

        return json.loads(data_str)

    def is_private(self, data):
        """
        Check a soup of an Instagram page to see if the page is private.
        We need to account for scraping a profile as a user gets redirected to a profile
        if they try to access a private post which they are not verified for.
        """
        user = self.get_ig_user(data)
        return user['is_private']

    def is_followed(self, data):
        """
        Check if an Instagram page is being followed.
        """
        user = self.get_ig_user(data)
        return user['followed_by_viewer']

    @staticmethod
    def get_ig_data(soup):
        """
        Extract the JSON data from an Instagram page's HTML source code.
        """
        # Private profiles have their JSON data stored in a different tag
        for s in soup.find_all('script'):
            if s.text.startswith('window.__additionalDataLoaded'):
                script = s

                # Strip string around the JSON object
                data = json.loads(','.join(script.text.split(',')[1:])[:-2])
                return data

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
    def make_ig_data_uniform(data):
        """
        Make sure the data keys are uniform between different tags.
        Adjust the data from public profiles to fit that of private profiles.
        """
        # Data was pulled from a public profile
        if 'entry_data' in data.keys():
            if 'ProfilePage' in data['entry_data'].keys():
                data = data['entry_data']['ProfilePage'][0]
            elif 'PostPage' in data['entry_data'].keys():
                data = data['entry_data']['PostPage'][0]

        return data

    @staticmethod
    def get_ig_user(data):
        """
        Get the user dict from JSON data.
        """
        # Scraped a private profile that is being followed
        if 'entry_data' not in data.keys():
            user = data['graphql']['shortcode_media']['owner']
        # Scraped a profile
        elif 'ProfilePage' in data['entry_data'].keys():
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
        data = self.make_ig_data_uniform(data)

        # Private page which is not being followed
        if self.is_private(data) is True and self.is_followed(data) is False:
            user = self.get_ig_user(data)
            self.log_text.newline(f'Cannot access profile of {user["username"]} - Skipping!')
            return

        shortcode_media = data['graphql']['shortcode_media']

        # Album
        if 'edge_sidecar_to_children' in shortcode_media.keys():
            edges = shortcode_media['edge_sidecar_to_children']['edges']

            for index, edge in enumerate(edges):
                self.append_link(edge['node']['display_url'],
                                 type_='image', index=index, list_=edges)

                if 'video_url' in edge['node'].keys():
                    self.append_link(edge['node']['video_url'],
                                     type_='video', index=index, list_=edges)

        # Single image/video
        else:
            self.append_link(shortcode_media['display_url'], type_='image')

            if 'video_url' in shortcode_media.keys():
                self.append_link(shortcode_media['video_url'], type_='video')

    def extract_ig_avatar(self, soup):
        """
        Extract the image link pointing to an Instagram user's avatar
        (from the source code of instadp.com).
        """
        avatar_url = soup.find('img', {'class': 'picture'})['src']
        self.append_link(avatar_url)

    def extract_imgur_images(self, soup):
        """
        Extract all images from an imgur post.
        JSON data handling taken from here:
        https://old.reddit.com/r/learnpython/comments/93yiti/
        scraping_images_from_imgur_using_selenium_and/e3h19xl/
        """
        data = self.get_imgur_data(soup)
        # No JSON data could be found - post was deleted
        if data is None:
            return

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
        self.youtube_ids.append(video_id)

        maxres_url = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
        hqdefault_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        self.append_link(maxres_url)
        self.append_link(hqdefault_url)

    @staticmethod
    def extract_reddit_link(data):
        """
        Extract the URL which a Reddit post links to.
        """
        # Return the fallback URL for the v.redd.it video if possible
        # else return the URL which the post links to
        try:
            data_key = data[0]['data']['children'][0]['data']

            if 'crosspost_parent_list' in data_key.keys():
                media = data[0]['data']['children'][0]['data']['crosspost_parent_list'][0]['media']
            else:
                media = data[0]['data']['children'][0]['data']['media']

            return media['reddit_video']['fallback_url']
        # media does not have 'reddit_video' key or is None
        except (KeyError, TypeError):
            return data[0]['data']['children'][0]['data']['url']

    def extract_reddit_video(self, data):
        """
        Extract the video of a v.redd.it upload.
        JSON data is acquired by appending '.json' to the end of a Reddit URL.
        """
        try:
            media = data[0]['data']['children'][0]['data']['media']
            video_url = media['reddit_video']['fallback_url']
            self.append_link(video_url, type_='video')
        # media is None
        except TypeError:
            self.log_text.newline('Not a v.redd.it video - Skipping!')

    def extract_gfycat_video(self, url):
        """
        Nothing to extract, this is just to keep the method calls uniform.
        Note that Gfycat videos have to be downloaded using youtube_dl instead of requests.
        """
        self.append_link(url, type_='video')

    def extract_tumblr_links(self, soup):
        """
        Extract the link(s) to the images/videos of a Tumblr post.
        """
        slideshow = soup.find_all('div', {'class': 'photo-slideshow'})

        # Single file
        if not slideshow:
            photo = soup.find_all('div', {'class': 'photo'})
            video = soup.find_all('div', {'class': 'tumblr_video_container'})

            if photo:
                self.append_link(photo[0].find_next('img')['src'], type_='file')
            else:
                self.extract_tumblr_video(video[0])
            return

        # Multiple files
        imgs = slideshow[0].find_all('img')
        for index, img in enumerate(imgs):
            self.append_link(img['src'], type_='file', index=index, list_=imgs)

    def extract_tumblr_video(self, container):
        """
        Extract the link to a Tumblr video using the URL
        specified in the div with the class "tumblr_video_container"
        in the source code of the original Tumblr post.
        """
        container_src = container.find_next('iframe')['src']
        res = requests.get(container_src)
        soup = BeautifulSoup(res.text, features='html.parser')

        video_source = soup.find('video').find_next('source')
        self.append_link(video_source['src'], type_='video')

    def extract_twitter_images(self, soup):
        """
        Extract image links of a Twitter post.
        """
        image_links = soup.find_all('meta', {'property': 'og:image'})
        for index, link in enumerate(image_links):
            self.append_link(link['content'], index=index, list_=image_links)

    def get_download_method(self, url):
        """
        Get the appropriate download method to execute as some
        files require modules other than requests to be downloaded.
        """
        # Special criteria for non-requests downloads
        criteria = {
            url.startswith('https://gfycat.com'): self.youtube_dl_download,
        }
        for crit, method in criteria.items():
            if crit is True:
                return method

        # Standard download method
        return self.requests_download

    def requests_download(self, url):
        """
        Download a file using the requests module.
        Return a bool on whether or not the file was downloaded.
        """
        file_name = self.prep_filename(url)
        file_dst = os.path.join(os.getcwd(), file_name)

        if os.path.exists(file_dst):
            return False

        with open(file_dst, 'wb') as dl_file:
            res = requests.get(url)
            dl_file.write(res.content)
        return True

    @staticmethod
    def youtube_dl_download(url):
        """
        Download a file using the youtube_dl module.
        Return a bool on whether or not the file was downloaded.
        """
        try:
            ydl_opts = {'logger': YDLLogger()}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True

        except youtube_dl.utils.SameFileError:
            return False

    def download_files(self):
        """
        Download all the collected files.
        """
        if not self.download_links:
            return

        dl_folder = 'downloads'
        if not os.path.exists(dl_folder) or not os.path.isdir(dl_folder):
            os.mkdir(dl_folder)
        os.chdir(dl_folder)

        for index, url in enumerate(self.download_links):
            dl_method = self.get_download_method(url)
            is_file_new = dl_method(url)

            if is_file_new is True:
                self.log_text.newline(f'Downloaded file {index+1}'
                                      f' / {len(self.download_links)}')
            else:
                self.log_text.newline(f'File {index+1} / {len(self.download_links)}'
                                      ' already present, skipping')

            self.last_download = url
            time.sleep(0.5)

        os.chdir('..')

    def prep_filename(self, url):
        """
        Prepare the name of the file to download
        by using the link/URL.
        """
        ig_name_re = re.compile(r'.+\.(?:jpg|png|gif|mp4)')
        twimg_re = re.compile(r'https://pbs\.twimg\.com/media/(.+\.(?:png|jpg)):large')
        file_name = url.split('/')[-1]

        # Strip ?-arguments from IG file names
        if ig_name_re.match(file_name):
            file_name = ig_name_re.match(file_name).group(0)

        # Strip 'large' suffix from Twitter file names
        if twimg_re.match(file_name):
            file_name = twimg_re.match(file_name).group(1)

        # Need to avoid same file names for YouTube thumbnails
        if file_name == 'maxresdefault.jpg':
            video_id = self.youtube_ids[0]
            file_name = f'maxresdefault_{video_id}.jpg'

        # More YouTube thumbnails
        if file_name == 'hqdefault.jpg':
            # maxresdefault equivalents get downloaded immediately before hqdefaults
            # due to them being added one after another
            # so we can remove the video ID from the list
            video_id = self.youtube_ids.pop(0)
            file_name = f'hqdefault_{video_id}.jpg'

        # Reddit videos contain this argument but no file extension
        if file_name.endswith('?source=fallback'):
            rnd_str = self.get_random_string()
            file_name = file_name.replace('?source=fallback', f'{rnd_str}.mp4')

        return file_name
