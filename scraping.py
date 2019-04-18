# BUILTIN
import json
import os
import re
# PIP
import requests
# from bs4 import BeautifulSoup
# CUSTOM
# import config


class Scraper:

    __slots__ = (
        'log_text',
        'download_links', 'display_links', 'instagram_links', 'image_links',
        )

    def __init__(self, log_text):
        self.log_text = log_text

        self.display_links = []  # Links to be displayed in the GUI (gets reset after dl loop)
        self.download_links = []  # DOES get reset after a download loop
        self.instagram_links = []  # Does NOT get reset after a download loop
        self.image_links = []  # Does NOT get reset after a download loop

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

    def extract_images(self, data):
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
                                 type_='image', index=index, edges=edges)

                if 'video_url' in edge['node'].keys():
                    self.append_link(edge['node']['video'],
                                     type_='image', index=index, edges=edges)

        # Single image/video
        else:
            self.append_link(shortcode_media['display_url'], type_='image')

            if 'video_url' in shortcode_media.keys():
                self.append_link(shortcode_media['video_url'], type_='video')

    def append_link(self, link, type_='image', index=None, edges=None):
        """
        Append a link to the link lists and log info.
        """
        self.download_links.append(link)
        self.image_links.append(self.download_links[-1])

        if index is not None and edges is not None:
            self.log_text.newline(f'Added {type_} of post #{index+1} / {len(edges)}:')
        else:
            self.log_text.newline(f'Added singular {type_}:')
        self.log_text.newline(f' -  {self.download_links[-1]}\n')

    def download_files(self, dl_bar=None):
        """
        Download all the collected files.
        """
        file_name_re = re.compile(r'.+.(?:jpg|png|gif|mp4)')
        dl_folder = 'downloads'

        if dl_bar is not None:
            dl_bar['maximum'] = len(self.download_links)
            dl_bar['value'] = 0

        if not os.path.exists(dl_folder) or not os.path.isdir(dl_folder):
            os.mkdir(dl_folder)

        for index, link in enumerate(self.download_links):
            file_name = link.split('/')[-1]
            # Extra check needed for IG file names
            file_name = file_name_re.match(file_name).group(0)
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

            if dl_bar is not None:
                dl_bar['value'] += 1
