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

from django.urls import path

from . import views
from .models import extract_text_from_html

app_name = 'ChatEME'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:model_id>/', views.ClassifierModelDetail, name='ClassifierModelDetail'),
    path('<int:model_id>/add_CrawlRoot/', views.add_CrawlRoot, name='add_CrawlRoot'),
    path('<int:model_id>/add_QAPair/', views.add_QAPair, name='add_QAPair'),
    path('<int:pk>/update_ClassifierModel/', views.ClassifierModelUpdateView.as_view(), name='update_ClassifierModel'),
    path('add_ClassifierModel/', views.add_ClassifierModel, name='add_ClassifierModel'),
    path('<int:model_id>/crawl_pages/', views.crawl_pages, name='crawl_pages'),
    path('<int:model_id>/clear_pages/', views.clear_pages, name='clear_pages'),
    path('<int:model_id>/extract_text_from_html/', extract_text_from_html, name='extract_text_from_html'),
    path('<int:model_id>/train_model/', views.train_model, name='train_model'),
    path('<int:model_id>/inspect_model/', views.inspect_model, name='inspect_model'),
    path('<int:model_id>/serve_model/', views.serve_model, name='serve_model'),
    path('<int:model_id>/<int:cr_id>/', views.CrawlRootDetail, name='CrawlRootDetail'),
    path('<int:model_id>/<int:cr_id>/delete', views.delete_CrawlRoot, name='delete_CrawlRootDetail'),
    path('<int:model_id>/<int:cr_id>/add_CrawlRule_URLContainsString', views.add_CrawlRule_URLContainsString, name='add_CrawlRule_URLContainsString'),
    path('<int:model_id>/<int:cr_id>/add_CrawlRule_URLNotContainsString', views.add_CrawlRule_URLNotContainsString, name='add_CrawlRule_URLNotContainsString'),   
    path('<int:model_id>/<int:rule_id>/delete_CrawlRule_URLContainsString', views.delete_CrawlRule_URLContainsString, name='delete_CrawlRule_URLContainsString'),
    path('<int:model_id>/<int:rule_id>/delete_CrawlRule_URLNotContainsString', views.delete_CrawlRule_URLNotContainsString, name='delete_CrawlRule_URLNotContainsString'),
    path('<int:model_id>/apply_rules/', views.apply_rules, name='apply_rules'),
    path('<int:model_id>/<int:page_id>/flip_active', views.flip_active, name='flip_active'),
    path('<int:model_id>/<int:page_id>/page_source', views.page_source, name='page_source'),
    path('<int:model_id>/update_QAPair/<int:pk>/', views.QAPairUpdateView.as_view(), name='update_QAPair'),
    path('<int:model_id>/delete_QAPair/<int:pk>/', views.QAPairDeleteView.as_view(), name='delete_QAPair'),    
    path('<int:model_id>/delete_all_QAPairs/', views.delete_all_QAPairs, name='delete_all_QAPairs'),    
    path('<int:model_id>/update_CrawlRoot/<int:pk>/', views.CrawlRootUpdateView.as_view(), name='update_CrawlRoot'),
    path('<int:model_id>/update_WebPage/<int:pk>/', views.WebPageUpdateView.as_view(), name='update_WebPage'),
    path('<int:model_id>/delete_CrawlRoot/<int:pk>/', views.CrawlRootDeleteView.as_view(), name='delete_CrawlRoot'),
    path('<int:model_id>/delete_WebPage/<int:pk>/', views.WebPageDeleteView.as_view(), name='delete_WebPage'),
    path('<int:pk>/delete_ClassifierModel/', views.ClassifierModelDeleteView.as_view(), name='delete_ClassifierModel'),
    path('<int:model_id>/save_model/', views.save_model, name='save_model'),
    path('load_model/', views.load_model, name='load_model'),
    path('<int:model_id>/import_RasaNLUFile/', views.import_RasaNLUFile, name='import_RasaNLUFile'),
    path('<int:model_id>/import_RasaDomainFile/', views.import_RasaDomainFile, name='import_RasaDomainFile'),
    path('<int:model_id>/export_oos2json/', views.export_oos2json, name='export_oos2json'),
    path('<int:model_id>/<int:page_id>/penalize_WebPage/<str:user_input>', views.penalize_WebPage, name='penalize_webpage'),
    path('<int:model_id>/<int:pair_id>/penalize_QAPair/<str:user_input>', views.penalize_QAPair, name='penalize_qapair'),

]