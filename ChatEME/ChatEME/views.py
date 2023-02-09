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

import threading
from datasets import Dataset
from json import dumps, loads, dump, load
from os import makedirs
from flask import Flask, request

import torch
from transformers import AutoTokenizer, DataCollatorWithPadding
from transformers import TrainingArguments, Trainer
from transformers import AutoModelForSequenceClassification

from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy, reverse

import plotly.graph_objects as go
from plotly.offline import plot

from .models import CrawlRoot, ClassifierModel, WebPage, QAPair
from .models import CrawlRule_URLContainsString, CrawlRule_URLNotContainsString
from .models import bg_crawl
from .scraper import extract_domain

from .forms import CrawlRootForm, CreateModelForm, UserInputForm, QAPairForm
from .forms import CrawlRule_URLContainsStringForm
from .forms import CrawlRule_URLNotContainsStringForm
from .forms import UploadFileForm

from .files import handle_uploaded_nlu_file, handle_uploaded_save_file
from .files import handle_uploaded_domain_file, create_save_file

from datetime import datetime


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15" # This has to move somewhere else

# Create your views here.

def index(request):
    """
    index view with models
    """

    models = ClassifierModel.objects.all()    

    context = {
        'models': models,
        'no_models': len(models), 

    }

    template = loader.get_template('ChatEME/index.html')
    return HttpResponse(template.render(context, request))


def ClassifierModelDetail(request, model_id):
    """
    Main view of the App: Model and its children
    """

    models = ClassifierModel.objects.all()

    model = get_object_or_404(ClassifierModel, pk=model_id)
    crawl_roots =  model.crawlroots.all()
    web_pages = model.webpages.all()
    qapairs = model.qapairs.all()
    no_active_webpages = len(model.webpages.filter(active=True))
    no_links_processed_webpages = len(model.webpages.filter(links_processed=True))
    urlcontainsstring = []
    urlnotcontainsstring = []
    no_crawl_rules = 0

    for cr in crawl_roots:
        urlcontainsstring.append(cr.crawlrule_urlcontainsstring.all())
        urlnotcontainsstring.append(cr.crawlrule_urlnotcontainsstring.all())

        no_crawl_rules += cr.crawlrule_urlcontainsstring.all().count() + \
            cr.crawlrule_urlnotcontainsstring.all().count()

    # Plotly
    
    if model.plot_labels != "" and model.plot_parents != "":

        graphs = []

        graphs.append(
            go.Treemap(labels = loads(model.plot_labels),
                    parents = loads(model.plot_parents))
        )

        layout = {
            'title': 'Tree view',
            'height': 1000,
            'width': 1800,
        }

        plot_div = plot({'data': graphs, 'layout': layout}, 
                        output_type='div')

    else:

        plot_div = None

    if len(web_pages) == 0:
        web_pages = None

    context = {
        'model': model,
        'qapairs': qapairs,
        'crawl_roots': crawl_roots,
        'no_crawl_roots': len(crawl_roots),
        'web_pages': web_pages,
        'plt_div': plot_div,
        'models' : models,
        'urlcontainsstring': urlcontainsstring,
        'urlnotcontainsstring': urlnotcontainsstring,
        'no_crawl_rules': no_crawl_rules,
        'no_active_webpages': no_active_webpages,
        'no_links_processed_webpages': no_links_processed_webpages
    }


    template = loader.get_template('ChatEME/ClassifierModelDetail.html')
    return HttpResponse(template.render(context, request))


def add_ClassifierModel(request):
    """
    View for adding a Classifier Model
    """

    if request.method == 'POST':
        form = CreateModelForm(request.POST)
        if form.is_valid():
            model = form.save(commit=False)
            model.save()

            return redirect ("ChatEME:index")
      
    form = CreateModelForm()
    return render(request, "ChatEME/generic_model_form.html", {'form':form})


def add_CrawlRoot(request, model_id):
    """
    View for adding a CrawlRoot
    """

    if request.method == 'POST':
        form = CrawlRootForm(request.POST)
        if form.is_valid():
            crawl_root = form.save(commit=False)
            crawl_root.classifier_model = ClassifierModel.objects.get(id=
                model_id)
            crawl_root.save()

            domain = extract_domain(crawl_root.root_url)

            CrawlRule_URLContainsString.objects.create(
                crawl_root=CrawlRoot.objects.get(id=crawl_root.id), 
                filter_string=domain
            )

            for exclude_in_url_string in crawl_root.exclude_in_url_strings.split(","):
                CrawlRule_URLNotContainsString.objects.create(
                crawl_root=CrawlRoot.objects.get(id=crawl_root.id), 
                filter_string=exclude_in_url_string
                )



            return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)

    form = CrawlRootForm()
    return render(request, "ChatEME/generic_model_form.html", {'form':form})


def clear_pages(request, model_id):
    """
    remove all pages from model
    """

    model = get_object_or_404(ClassifierModel, pk=model_id)
    pages = model.webpages.all()

    for page in pages:
        page.delete() 

    model.plot_labels = ""
    model.plot_parents = ""
    model.save()

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def CrawlRootDetail(request, model_id, cr_id):
    """
    view for CrawlRootDetail
    """
    cr = CrawlRoot.objects.get(pk=cr_id)
    urlcontainsstring = cr.crawlrule_urlcontainsstring.all()
    urlnotcontainsstring = cr.crawlrule_urlnotcontainsstring.all()

    context = {
            'model': ClassifierModel.objects.get(pk=model_id),
            'models': ClassifierModel.objects.all(),
            'cr': cr,
            'urlcontainsstring': urlcontainsstring,
            'urlnotcontainsstring': urlnotcontainsstring
        }

    template = loader.get_template('ChatEME/CrawlRootDetail.html')
    return HttpResponse(template.render(context, request))
    

def delete_CrawlRoot(request, model_id, cr_id):
    """
    delete one CrawlRoot
    """
    cr = CrawlRoot.objects.get(pk=cr_id)
    cr.delete()

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def add_CrawlRule_URLContainsString(request, model_id, cr_id):
    """
    add one CrawRule
    """
    if request.method == 'POST':
        form = CrawlRule_URLContainsStringForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.crawl_root = CrawlRoot.objects.get(id=
                cr_id)
            rule.save()

            return redirect ("ChatEME:CrawlRootDetail", model_id = model_id, cr_id=cr_id)
      
    form = CrawlRule_URLContainsStringForm()
    return render(request, "ChatEME/generic_model_form.html", {'form':form})


def add_CrawlRule_URLNotContainsString(request, model_id, cr_id):
    """
    add one CrawRule
    """
    if request.method == 'POST':
        form = CrawlRule_URLNotContainsStringForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.crawl_root = CrawlRoot.objects.get(id=
                cr_id)
            rule.save()

            return redirect ("ChatEME:CrawlRootDetail", model_id = model_id, cr_id=cr_id)
      
    form = CrawlRule_URLNotContainsStringForm()
    return render(request, "ChatEME/generic_model_form.html", {'form':form})


def delete_CrawlRule_URLContainsString(request, model_id, rule_id):
    """
    remove one CrawRule
    """

    rule = get_object_or_404(CrawlRule_URLContainsString, pk=rule_id)

    rule.delete() 

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def delete_CrawlRule_URLNotContainsString(request, model_id, rule_id):
    """
    remove one CrawRule
    """

    rule = get_object_or_404(CrawlRule_URLNotContainsString, pk=rule_id)

    rule.delete() 

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def apply_rules(request, model_id):
    """
    Applies the CrawlRules to webpages (URLs)
    """
    model = ClassifierModel.objects.get(pk=model_id)

    crawl_roots = model.crawlroots.all()

    for cr in crawl_roots:

        contain_rules = cr.crawlrule_urlcontainsstring.all()

        not_contain_rules = cr.crawlrule_urlnotcontainsstring.all()

        webpages = cr.webpages.all()


        for webpage in webpages:

            for rule in contain_rules:
                if (not rule.apply_rule(webpage.page_url)):
                    webpage.active = False
                    webpage.save()

            for rule in not_contain_rules:
                if (not rule.apply_rule(webpage.page_url)):
                    webpage.active = False
                    webpage.save()
            
            # Plot safety

            if webpage.parent is None:
                webpage.active = True
                webpage.save()

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def flip_active(request, model_id, page_id):
    """
    Flips page activity
    """
    
    page = get_object_or_404(WebPage, pk=page_id)

    page.active = not page.active 
    page.save()
    
    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def crawl_pages(request, model_id):
    """
    Starts the crawling process in a separate thread
    """

    model = get_object_or_404(ClassifierModel, pk=model_id)
    crawl_roots = model.crawlroots.all()

    thread = threading.Thread(target=bg_crawl,args=[model.id, crawl_roots], daemon=True)
    thread.start()

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def page_source(request, model_id, page_id):
    """
    Show page source
    """
    context = {
        "page": WebPage.objects.get(id=page_id)
    }

    template = loader.get_template('ChatEME/ShowPageSource.html')
    return HttpResponse(template.render(context, request))


def train_model(request, model_id):
    """
    Starts the model building process in a separate thread
    """

    thread = threading.Thread(target=bg_train_model,args=[model_id], 
        daemon=True)
    thread.start()

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def bg_train_model(model_id):

    model = get_object_or_404(ClassifierModel, pk=model_id)
    model.build_model_in_progress = True
    model.save()
    pages = model.webpages.all().filter(active=True)
    qapairs = model.qapairs.all().filter(active=True)

    counter = 0
    i = 0
    indexes = []
    urls = []
    sentences = []
    labels = []

    label_verbose = []
    label_flask = []

    for qa in qapairs:
        for sentence in qa.questions.split("\n"):
            indexes.append(i)
            labels.append(counter)
            urls.append(qa.answer)
            sentences.append(sentence)
            i += 1

        counter += 1
        label_verbose.append(("QAPair", int(qa.id)))
        label_flask.append(["QAPair", str(qa.intent), str(qa.answer)])

    for page in pages:
        if page.get_len_text() > 0:
            sentences.append(page.get_title())
            indexes.append(i)
            i += 1
            labels.append(counter)
            urls.append(page.page_url)

            for sentence in page.unique_text.split("\n"):
                if sentence == "": 
                    continue
                indexes.append(i)
                labels.append(counter)
                urls.append(page.page_url)
                sentences.append(sentence)
                i += 1

            for sentence in page.additional_text.split("\n"):
                if sentence == "": 
                    continue
                indexes.append(i)
                labels.append(counter)
                urls.append(page.page_url)
                sentences.append(sentence)
                i += 1

            counter += 1
            label_verbose.append(("WebPage", int(page.id)))
            label_flask.append(["WebPage", str(page.get_title()), 
                                str(page.page_url)])

    label2verbose = {l: v for l, v in enumerate(label_verbose)}
    label2flask = {l: v for l, v in enumerate(label_flask)}

    filename = "models/" + str(model.name) + "/label2flask.json"

    makedirs("models/" + str(model.name), exist_ok = True)

    with open(filename, 'w') as fp:
        dump(label2flask, fp)

    model.label2verbose = dumps(label2verbose)

    dataset = dict()
    dataset['idx'] = indexes
    dataset['label'] = labels
    dataset['sentence'] = sentences
    dataset['url'] = urls

    dataset = Dataset.from_dict(dataset)
    train_test = dataset.train_test_split()
    
    chkpnt = model.transformer_model_name
    tokenizer = AutoTokenizer.from_pretrained(chkpnt)

    def tokenize_function(example):
        return tokenizer(example["sentence"], truncation=True)
    
    tokenized_datasets = train_test.map(tokenize_function, batched=True)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    training_args = TrainingArguments(output_dir=str("models/" + model.name), 
        num_train_epochs = model.epochs, 
        save_strategy = "no",
        per_device_train_batch_size=16)

    lang_model = AutoModelForSequenceClassification.from_pretrained(chkpnt, num_labels=counter)

    trainer = Trainer(
        lang_model,
        training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model()

    model.build_model_in_progress = False
    model.model_exists = True
    model.save()


def inspect_model(request, model_id):

    context = None

    if request.method == 'POST':
        form = UserInputForm(request.POST)
        if form.is_valid():
            model = get_object_or_404(ClassifierModel, pk=model_id)
            tokenizer = AutoTokenizer.from_pretrained("models/" +  model.name)
            lang_model = AutoModelForSequenceClassification.from_pretrained("models/" +  model.name)
            label2verbose = {int(k): v for k, v in loads(model.label2verbose).items()}

            text = form.cleaned_data.get('user_input')

            encoding = tokenizer(text, return_tensors="pt")

            outputs = lang_model(**encoding)[0].detach().numpy()

            pages = []
            qapairs = []

            i=0

            for v in outputs[0]:
                t, pk = label2verbose[i]
                if t == "WebPage":
                    pages.append((v, WebPage.objects.get(pk=pk)))
                else:
                    qapairs.append((v, QAPair.objects.get(pk=pk)))
                i+=1

            pages = sorted(pages, key=lambda tup: tup[0], reverse=True)
            qapairs = sorted(qapairs, key=lambda tup: tup[0], reverse=True)

            context = {
                'pages': pages,
                'qapairs': qapairs,
                'model_id': model_id
            }

    else:
        
        form = UserInputForm()

    return render(request, "ChatEME/userinput_for_model.html", {'form':form, 'context':context})


def add_QAPair(request, model_id):
    """
    View for adding a QAPair
    """

    if request.method == 'POST':
        form = QAPairForm(request.POST)
        if form.is_valid():
            qapair = form.save(commit=False)
            qapair.classifier_model = ClassifierModel.objects.get(id=
                model_id)
            qapair.save()

            return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)

    form = QAPairForm()
    return render(request, "ChatEME/generic_model_form.html", {'form':form})

 
class ClassifierModelUpdateView(UpdateView):
    """
    View for updating an existing ClassifierModel
    """

    model = ClassifierModel
    fields = ('name','transformer_model_name','epochs')

    template_name = 'ChatEME/generic_model_form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        return redirect('ChatEME:index')

    def get_context_data(self, *args, **kwargs):
        data = super(ClassifierModelUpdateView, self).get_context_data(*args, **kwargs)
        return data

class WebPageUpdateView(UpdateView):
    """
    View for updating an existing WebPage
    """

    model = WebPage
    fields = ('additional_text', 'unique_text', 'penalty_text')

    template_name = 'ChatEME/generic_model_form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        instance = form.save(commit=False)
        instance.save()
        return redirect ("ChatEME:ClassifierModelDetail", 
            model_id=int(self.kwargs.get("model_id")))

    def get_context_data(self, *args, **kwargs):
        data = super(WebPageUpdateView, self).get_context_data(*args, **kwargs)
        return data


class QAPairUpdateView(UpdateView):
    """
    View for updating an existing QAPair 
    """

    model = QAPair
    fields = ('intent','questions','answer','penalty_text')

    template_name = 'ChatEME/generic_model_form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        instance = form.save(commit=False)
        instance.save()
        return redirect ("ChatEME:ClassifierModelDetail", 
            model_id=int(self.kwargs.get("model_id")))

    def get_context_data(self, *args, **kwargs):
        data = super(QAPairUpdateView, self).get_context_data(*args, **kwargs)
        return data


class CrawlRootUpdateView(UpdateView):
    """
    View for updating an existing QAPair 
    """

    model = CrawlRoot
    fields = ('root_url','short_name','crawl_depth', 'extract_tags', 'focus_tag',
        'exclude_tags')

    template_name = 'ChatEME/generic_model_form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.save()
        return redirect ("ChatEME:ClassifierModelDetail", 
            model_id=int(self.kwargs.get("model_id")))
            
    def get_context_data(self, *args, **kwargs):
        data = super(CrawlRootUpdateView, self).get_context_data(*args, **kwargs)
        return data


class QAPairDeleteView(DeleteView):
    """
    Delete a QAPair view
    """

    template_name = 'ChatEME/generic_delete.html'
    model = QAPair
    success_url = reverse_lazy('ChatEME:index')

    def get_context_data(self, *args, **kwargs):
        data = super(QAPairDeleteView, self).get_context_data(*args, **kwargs)
        return data
    
    def get_success_url(self, *args, **kwargs):
        return reverse('ChatEME:ClassifierModelDetail', 
            kwargs={'model_id': self.kwargs.get("model_id")})


class CrawlRootDeleteView(DeleteView):
    """
    Delete a Crawl Root view
    """

    template_name = 'ChatEME/generic_delete.html'
    model = CrawlRoot
    success_url = reverse_lazy('ChatEME:index')

    def get_context_data(self, *args, **kwargs):
        data = super(CrawlRootDeleteView, self).get_context_data(*args, **kwargs)
        return data


class WebPageDeleteView(DeleteView):
    """
    Delete a WebPage view
    """

    template_name = 'ChatEME/generic_delete.html'
    model = WebPage
    success_url = reverse_lazy('ChatEME:index')

    def get_context_data(self, *args, **kwargs):
        data = super(WebPageDeleteView, self).get_context_data(*args, **kwargs)
        return data
        
    def get_success_url(self, *args, **kwargs):
        return reverse('ChatEME:ClassifierModelDetail', 
            kwargs={'model_id': self.kwargs.get("model_id")})


class ClassifierModelDeleteView(DeleteView):
    """
    Delete a ClassifierModel view
    """

    template_name = 'ChatEME/generic_delete.html'
    model = ClassifierModel
    success_url = reverse_lazy("ChatEME:index")

    def get_context_data(self, *args, **kwargs):
        data = super(ClassifierModelDeleteView, self).get_context_data(*args, **kwargs)
        return data


def import_RasaNLUFile(request, model_id):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_nlu_file(request.FILES['file'], model_id)
            return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)
    else:
        form = UploadFileForm()
    return render(request, 'ChatEME/generic_file_upload.html', {'form': form})

def import_RasaDomainFile(request, model_id):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_domain_file(request.FILES['file'], model_id)
            return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)
    else:
        form = UploadFileForm()
    return render(request, 'ChatEME/generic_file_upload.html', {'form': form})


def export_oos2json(request, model_id):

    model = get_object_or_404(ClassifierModel, pk=model_id)
    pages = model.webpages.all().filter(active=True)
    qapairs = model.qapairs.all().filter(active=True)

    sentences = []

    for qa in qapairs:
        for sentence in qa.questions.split("\n"):
            if sentence != "":
                sentences.append(sentence.replace("- ", ""))

    for page in pages:
        if page.get_len_text() > 0:
            sentences.append(page.get_title())

            for sentence in page.unique_text.split("\n"):
                if sentence != "":
                    sentences.append(sentence)
                    
    line_1 = 'version: "2.0"\n'
    line_2 = 'nlu:\n'
    line_3 = '- intent: out_of_scope\n'
    line_4 = '  examples: |\n'
    line_5 = '    - '

    yaml_string = line_1 + line_2 + line_3 + line_4

    for s in sentences:
        yaml_string += line_5 + s + "\n"

    response = HttpResponse(yaml_string, content_type="application/yaml")
    response['Content-Disposition'] = 'inline; filename=out_of_scope.yml'
    return response


def delete_all_QAPairs(request, model_id):

    model = get_object_or_404(ClassifierModel, pk=model_id)
    qapairs = model.qapairs.all().filter(active=True)    

    for qapair in qapairs:
        qapair.delete()

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def load_model(request):

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_save_file(request.FILES['file'])
            return redirect ("ChatEME:index")
    else:
        form = UploadFileForm()
    return render(request, 'ChatEME/generic_file_upload.html', {'form': form})
    

def save_model(request, model_id):

    model_name, yaml_string = create_save_file(model_id)

    response = HttpResponse(yaml_string, content_type="application/yaml")
    response['Content-Disposition'] = (
        'inline; filename={0}_export_{1}.yml'.
        format(model_name, datetime.now().strftime("%Y%m%d"))
        )

    return response


def serve_model(request, model_id):
    """
    Serves the model via flask in own thread
    """

    thread = threading.Thread(target=bg_serve_model,args=[model_id], 
        daemon=True)
    thread.start()

    return redirect ("ChatEME:ClassifierModelDetail", model_id = model_id)


def bg_serve_model(model_id):

    classifier_model = get_object_or_404(ClassifierModel, pk=model_id)

    MAX_QAPAIRS = 5
    MAX_WEBPAGES = 5

    device = "cpu"
    tokenizer = AutoTokenizer.from_pretrained("models/" + classifier_model.name)
    model = AutoModelForSequenceClassification.from_pretrained("models/" + classifier_model.name)

    with open("models/" + classifier_model.name + "/label2flask.json") as json_file:
        label2flask = load(json_file)

    app = Flask(__name__)

    app.config['JSON_AS_ASCII'] = False

    @app.route("/ChatEME/", methods=['POST', 'GET'])
    def serve_model():
        if request.method == 'POST':

            response = request.get_json()
            encoding = tokenizer(response['text'], return_tensors="pt")
            outputs = model(**encoding)[0].detach().numpy()

            results = []
            i=0

            for confidence in outputs[0]:
                results.append((
                                label2flask[str(i)][0],
                                label2flask[str(i)][1],
                                label2flask[str(i)][2],
                                confidence
                                ))
                i+=1

            qapairs = []
            webpages = []

            for result in results:
                if result[0] == "QAPair":
                    qapairs.append(result)
                else:
                    webpages.append(result)


            qapairs = sorted(qapairs, key=lambda tup: tup[-1], reverse=True)
            webpages = sorted(webpages, key=lambda tup: tup[-1], reverse=True)

            return {"QAPairs": str(qapairs[0:MAX_QAPAIRS]),
                    "WebPages": str(webpages[0:MAX_WEBPAGES])}
        else:
            return '<p>Usage: POST {"text": "text to classify"}</p>'

    app.run()