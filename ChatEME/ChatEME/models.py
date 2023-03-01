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

from django.db import models
from django.shortcuts import get_object_or_404

from bs4 import BeautifulSoup

from datetime import datetime

from regex import search, sub
from json import dumps

from .scraper import get_webpage_links


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15"

# Create your models here.

class ClassifierModel(models.Model):

    name = models.CharField(max_length=100)
    transformer_model_name = models.CharField(max_length=100, default="rasa/LaBSE")
    epochs =  models.IntegerField(default=25)
    date = models.DateTimeField(default=datetime.now, blank=True)
    crawl_in_progress = models.BooleanField(default=False)
    build_model_in_progress = models.BooleanField(default=False)
    model_exists = models.BooleanField(default=False)
    label2verbose = models.TextField(default="")
    plot_labels = models.TextField(default="")
    plot_parents = models.TextField(default="")

    def __str__(self):
        return self.name

    def get_crawl_status(self):
        if self.crawl_in_progress:
            return "Currently crawling web pages."
        else:
            return "Crawler idle."
    
    def get_model_builder_status(self):
        if self.build_model_in_progress:
            return "Currently builing model."
        else:
            return "Model builder idle."

class CrawlRoot(models.Model):

    classifier_model = (
        models.ForeignKey(ClassifierModel, 
        related_name='crawlroots', 
        on_delete=models.CASCADE)
    )
    root_url = models.URLField()
    short_name = models.CharField(max_length=50)
    crawl_depth = models.IntegerField(default=2)
    extract_tags =  models.CharField(max_length=100, default="p,title")
    exclude_in_url_strings = models.CharField(max_length=100,
        default=".pdf,mailto",blank=True)
    focus_tag = models.CharField(max_length=100, default="article",blank=True)
    exclude_tags = models.CharField(max_length=100, default="nav",blank=True)

    def __str__(self):
        return self.short_name

class CrawlRule_URLContainsString(models.Model):

    crawl_root = (
        models.ForeignKey(CrawlRoot, 
        related_name='crawlrule_urlcontainsstring', 
        on_delete=models.CASCADE)
    )
    rule_type = models.CharField(default="URL CONTAINS", max_length=20)
    filter_string = models.CharField(max_length=100)

    def __str__(self) -> str:
        return "URL must contain: '" + self.filter_string + "'"

    def apply_rule(self, url):
        return (self.filter_string in url)

class CrawlRule_URLNotContainsString(models.Model):

    crawl_root = (
        models.ForeignKey(CrawlRoot, 
        related_name='crawlrule_urlnotcontainsstring', 
        on_delete=models.CASCADE)
    )
    rule_type = models.CharField(default="URL NOT CONTAINS", max_length=20)
    filter_string = models.CharField(max_length=100)

    def __str__(self) -> str:
        return "URL must not contain: '" + self.filter_string + "'"

    def apply_rule(self, url):
        return (self.filter_string not in url)

class WebPage(models.Model):

    crawl_root = (
        models.ForeignKey(CrawlRoot, 
        related_name='webpages', 
        on_delete=models.CASCADE)
    )
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE)

    classifier_model = (
        models.ForeignKey(ClassifierModel, 
        related_name='webpages', 
        on_delete=models.CASCADE)
    )

    page_url = models.CharField(max_length=4)
    page_title = models.TextField(default="", blank=True)
    active = models.BooleanField(default=True)
    links_processed = models.BooleanField(default=False)
    crawl_depth = models.IntegerField(default=0)
    additional_text = models.TextField(default="", blank=True)
    penalty_text = models.TextField(default="", blank=True)

    html = models.TextField(default="")
    title = models.TextField(default="")
    unique_text = models.TextField(default="")

    def get_len_html(self):
        return len(self.html)
    
    def get_html(self):
        return BeautifulSoup(self.html, features="html.parser").prettify()

    def get_len_text(self):
        return len(self.unique_text)

    def get_text(self):
        return self.unique_text

    def display_text(self):
        return self.unique_text.replace("\n", "<br>")

    def get_title(self):
        return self.page_title
        #s = search("<title>(.+?)</title>", self.html)
        #if s is None:
        #    return "#" 
        #else:
        #    return s.group(1)

    def get_short_title(self):
        return self.page_title[0:30]
        #s = search("<title>(.+?)</title>", self.html)
        #if s is None:
        #    return "#" 
        #else:
        #    return s.group(1)[0:30]

    def __str__(self):
        return self.page_url

    def crawl(self):

        filter_list = []

        crawl_root = CrawlRoot.objects.get(pk=self.crawl_root.id) 
        crawl_rules_contain = crawl_root.crawlrule_urlcontainsstring.all()
        crawl_rules_not_contain = crawl_root.crawlrule_urlnotcontainsstring.all()

        html, links = get_webpage_links(crawl_root.focus_tag, crawl_root.exclude_tags, self.page_url, USER_AGENT)# article nav

        for link in links:

            if link is None:
                filter_list.append(None)
                continue

            for rule in crawl_rules_contain:
                if not rule.apply_rule(link):
                    filter_list.append(link)           
        
            for rule in crawl_rules_not_contain:
                    if not rule.apply_rule(link):
                        filter_list.append(link)

        filter_list, links = set(filter_list), set(links)
        links = list(links - filter_list)

        return html, links

class QAPair(models.Model):

    classifier_model = (
        models.ForeignKey(ClassifierModel, 
        related_name='qapairs', 
        on_delete=models.CASCADE)
    )

    intent = models.CharField(max_length=100)
    questions = models.TextField(default="")
    answer = models.TextField(default="")
    penalty_text = models.TextField(default="", blank=True)


    active = models.BooleanField(default=True)

    def __str__(self):
        return self.intent

    
def bg_crawl(model_id, crawl_roots):
    """
    Crawl in the background
    """
    model = get_object_or_404(ClassifierModel, pk=model_id)
    model.crawl_in_progress = True
    model.save()

    for crawl_root in crawl_roots:

        webpage = WebPage.objects.create(
            crawl_root=CrawlRoot.objects.get(id=crawl_root.id), 
            classifier_model = ClassifierModel.objects.get(id=model_id), 
            page_url=crawl_root.root_url,
            crawl_depth=crawl_root.crawl_depth,
        )

    while(WebPage.objects.filter(links_processed=False)):

        for webpage in model.webpages.all().order_by('?'):

            if not webpage.links_processed:

                webpage.links_processed = True
                webpage.save()

                html, links = webpage.crawl()
                webpage.html = str(html)
                webpage.save()

                s = search("<title>(.+?)</title>", webpage.html)
                if s is None:
                   webpage.page_title = "#" 
                else:
                   webpage.page_title = s.group(1)
                webpage.save()

                if webpage.crawl_depth > 0:

                    for link in links:

                        if model.webpages.filter(classifier_model=model_id, 
                                                 page_url=link):
                            continue

                        new_webpage = WebPage.objects.create(
                        crawl_root=CrawlRoot.objects.get(id=webpage.crawl_root.id), 
                        classifier_model = ClassifierModel.objects.get(id=model.id), 
                        parent = WebPage.objects.get(id=webpage.id),
                        page_url=link,
                        crawl_depth=webpage.crawl_depth - 1,
                    )
    
    extract_text_from_html(model_id)

    # Create plot data

    web_pages = model.webpages.all()

    if len(web_pages) > 0:
        labels = [] 
        parents = []

        for page in web_pages:
            if page.active:
                labels.append(str(page))
                parents.append(str(page.parent))


        parents = ["" if str(x) == "None" else str(x) for x in parents]

    model.plot_labels = dumps(labels)
    model.plot_parents = dumps(parents)
     
    model.crawl_in_progress = False
    model.save()

def extract_text_from_html(model_id):

    model = get_object_or_404(ClassifierModel, pk=model_id)
    pages = model.webpages.all()

    for page in pages:

        extract_tags = page.crawl_root.extract_tags

        page_text = ""
    
        html = page.get_html()
        soup = BeautifulSoup(html,features="html.parser")

        for extract_tag in extract_tags.split(","):
            
            for tag in soup.findAll(extract_tag):
                page_text = page_text.lstrip(' ') + tag.text.lstrip(' ')

        page_text = sub("\s\s+", " ",  page_text)

        page.unique_text = page_text.replace(". ", ".\n")
        page.save()