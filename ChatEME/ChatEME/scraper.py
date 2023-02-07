    # ChatEME - Chat Engine Made Easy
    # Copyright (C) 2023  Florian Dewes

    # This program is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with this program.  If not, see <https://www.gnu.org/licenses/>.

from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from tldextract import extract


from bs4 import BeautifulSoup
from time import sleep
from random import randint
import logging
import socket

def extract_domain(url):
    return extract(url).domain

def get_html(url, user_agent, timeout=10, wait=False):
    """
    downloads the html file and catches various exceptions that can occur
    when crawling the web
    """
    if(wait):
        sleep(randint(1,3))

    try:
        html = urlopen(Request(url, headers={"User-Agent": user_agent}),
                       timeout=timeout)
        return html

    except HTTPError as e:
        logging.warning(url, "HTTPError exception:", e)
        return None
    except URLError as e:
        logging.warning(url, "URLError exception: ", e)
        return None
    except socket.timeout as e:
        logging.warning(url, "socket.timeout exception: ", e)
        return None
    except:
        return None


def get_webpage_links(focus, exclude_tags, url, user_agent):
    """
    extracts all links from a web page and returns them as a unique list.
    """

    links = []

    try:
        html = get_html(url, user_agent)
        soup = soupit(html)

        if focus != "": #was: "article"
            focus = soup.find(focus)
        else:
            focus = soup

        for tag in exclude_tags.split(","):
            if tag == "":
                continue
            else:
                t = focus.find(tag) # was: nav
                t.clear()

        for link in focus.findAll("a"):
            links.append((link.get("href")))

        return soup.prettify(), list(set(links))
        
    except: 

        return "", []

def soupit(html, parser="html.parser"):
    """
    converts the raw html to BeautifulSoup and catches exceptions.
    """

    try:
        page = BeautifulSoup(html.read(), "html.parser", from_encoding="utf-8")
        return page

    except socket.timeout as e:
        logging.warning("Timeout: ", e)
        return None
    except AttributeError as e:
        logging.warning("AttributeError: ", e)
        return None
    except:
        return None

