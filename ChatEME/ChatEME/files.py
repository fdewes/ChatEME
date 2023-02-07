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

from django.shortcuts import redirect, get_object_or_404

import ruamel.yaml as yaml
from ruamel.yaml import Loader as yamlLoader
from regex import sub

from .models import ClassifierModel, CrawlRoot, WebPage, QAPair
from .models import CrawlRule_URLContainsString
from .models import CrawlRule_URLNotContainsString

def handle_uploaded_nlu_file(file, model_id):

    nlu_file = ""

    for chunk in file.chunks():
        nlu_file += chunk.decode("utf-8") 

    nlu_yaml = yaml.load(nlu_file, Loader=yamlLoader)

    if "nlu" not in  nlu_yaml.keys():
        print("Not an NLU file.")
        return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)

    for item in nlu_yaml['nlu']:

        examples = sub("^- ", "", item['examples'])
        examples = sub("\n- ", "\n", examples)

        if QAPair.objects.filter(classifier_model=model_id, intent=item['intent']).exists():
            qapair = QAPair.objects.get(intent=item['intent'])
            qapair.questions = examples
        else:
            qapair = QAPair.objects.create(
                classifier_model = ClassifierModel.objects.get(id=model_id), 
                intent=item['intent'],
                questions=examples,
                answer="" )
            
    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def handle_uploaded_domain_file(file, model_id):

    domain_file = ""

    for chunk in file.chunks():
        domain_file += chunk.decode("utf-8") 

    domain_yaml = yaml.load(domain_file, Loader=yamlLoader)

    responses = domain_yaml['responses']

    for response in responses:

        answer = responses[response][0]['text']

        response_str = str(response).replace("utter_faq", "faq") #this has to be changed!

        if QAPair.objects.filter(classifier_model=model_id, intent=response_str).exists():
            qapair = QAPair.objects.get(classifier_model=model_id, intent=response_str)
            qapair.answer = answer
            qapair.save()
            
    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def handle_uploaded_save_file(file):

    save_file = ""

    for chunk in file.chunks():
        save_file += chunk.decode("utf-8") 

    save_yaml = yaml.load(save_file, Loader=yamlLoader)

    model = save_yaml['ClassifierModel']
    qapairs = save_yaml['QAPairs']
    crawlroots = save_yaml['CrawlRoots']


    cm = ClassifierModel.objects.create(
            name = model['name'],
            transformer_model_name = model['transformer_model_name'], 
            epochs = model['epochs'],
            plot_labels = model['plot_labels'],
            plot_parents = model['plot_parents']
        )

    for short_name in crawlroots.keys():
        cr = CrawlRoot.objects.create(
            classifier_model = cm,
            short_name = short_name,
            root_url = crawlroots[short_name]['root_url'],
            crawl_depth = crawlroots[short_name]['crawl_depth'],
            extract_tags = crawlroots[short_name]['extract_tags'],
            focus_tag = crawlroots[short_name]['focus_tag'],
            exclude_tags = crawlroots[short_name]['exclude_tags'],
            exclude_in_url_strings = crawlroots[short_name]['exclude_in_url_strings']
        )

        webpages =  crawlroots[short_name]['webpages']
        crawlrule_urlcontainsstring =  crawlroots[short_name]['CrawlRule_URLContainsString']
        crawlrule_urlnotcontainsstring =  crawlroots[short_name]['CrawlRule_URLNotContainsString']

        for page_url in webpages.keys(): 
            WebPage.objects.create(
                parent = None,
                classifier_model = cm,
                crawl_root = cr,
                page_url = page_url,
                active = webpages[page_url]['active'],
                links_processed = webpages[page_url]['links_processed'],
                crawl_depth = webpages[page_url]['crawl_depth'],
                html = webpages[page_url]['html'].decode("utf-8"),
                additional_text = webpages[page_url]['additional_text'],
                unique_text = webpages[page_url]['unique_text'],
                penalty_text = webpages[page_url]['penalty_text'],
            )

        for k in crawlrule_urlcontainsstring.keys(): 
            CrawlRule_URLContainsString.objects.create(
                crawl_root = cr,
                filter_string = crawlrule_urlcontainsstring[k]['filter_string'],
            )

        for k in crawlrule_urlnotcontainsstring.keys(): 
            CrawlRule_URLNotContainsString.objects.create(
                crawl_root = cr,
                filter_string = crawlrule_urlnotcontainsstring[k]['filter_string'],
            )


    for qapair_intent in qapairs.keys():
        QAPair.objects.create(
            classifier_model = cm,
            intent = qapair_intent,
            answer = qapairs[qapair_intent]['Answer'],
            questions = qapairs[qapair_intent]['Questions'],
            penalty_text = qapairs[qapair_intent]['penalty_text']
        )

def create_save_file(model_id):

    model = get_object_or_404(ClassifierModel, pk=model_id)
    crawlroots = model.crawlroots.all()
    qapairs = model.qapairs.all().filter(active=True)

    Export_QAPairs = dict()
    Export_ClassifierModel = dict()
    Export_CrawlRoots = dict()

    Export_ClassifierModel['name'] = model.name 
    Export_ClassifierModel['transformer_model_name'] = model.transformer_model_name
    Export_ClassifierModel['epochs'] = model.epochs
    Export_ClassifierModel['plot_labels'] = model.plot_labels
    Export_ClassifierModel['plot_parents'] = model.plot_parents
     
    for crawlroot in crawlroots:

        Export_WebPages = dict()
        Export_ContainRules = dict()
        Export_NotContainRules = dict()

        webpages = crawlroot.webpages.all()
        crawlrule_urlcontainsstring = crawlroot.crawlrule_urlcontainsstring.all()
        crawlrule_urlnotcontainsstring = crawlroot.crawlrule_urlnotcontainsstring.all()

        for webpage in webpages:
            Export_WebPages[webpage.page_url] = {
                "active": webpage.active,
                "links_processed": webpage.links_processed,
                "crawl_depth": int(webpage.crawl_depth),
                "unique_text": webpage.unique_text,
                "additional_text": webpage.additional_text, 
                "penalty_text": webpage.penalty_text, 
                "html": webpage.html.encode(encoding = 'UTF-8', errors = 'strict')
            }
        
        for rule in crawlrule_urlcontainsstring:
            Export_ContainRules[rule.id] = {
                "rule_type": rule.rule_type,
                "filter_string": rule.filter_string
            }

        for rule in crawlrule_urlnotcontainsstring:
            Export_NotContainRules[rule.id] = {
                "rule_type": rule.rule_type,
                "filter_string": rule.filter_string
            }

        Export_CrawlRoots[crawlroot.short_name] = {
            "root_url": crawlroot.root_url, 
            "crawl_depth": crawlroot.crawl_depth, 
            "extract_tags": crawlroot.extract_tags,
            "focus_tag": crawlroot.focus_tag,
            "exclude_tags": crawlroot.exclude_tags,
            "exclude_in_url_strings": crawlroot.exclude_in_url_strings,
            "webpages": Export_WebPages,
            "CrawlRule_URLContainsString": Export_ContainRules,
            "CrawlRule_URLNotContainsString": Export_NotContainRules,
            }

    for qapair in qapairs:
        Export_QAPairs[qapair.intent] = {"Questions": qapair.questions, 
                                         "Answer":    qapair.answer,
                                         "penalty_text":    qapair.penalty_text}

    yaml_data = {
        "QAPairs" : Export_QAPairs,
        "CrawlRoots": Export_CrawlRoots, 
        "ClassifierModel" : Export_ClassifierModel,
    }

    return (model.name, yaml.dump(yaml_data, allow_unicode=True, 
                            default_flow_style=False))