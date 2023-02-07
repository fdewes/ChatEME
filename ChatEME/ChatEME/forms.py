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

from django.forms import ModelForm, Form, CharField, FileField

from .models import CrawlRoot, ClassifierModel, QAPair
from .models import CrawlRule_URLNotContainsString, CrawlRule_URLContainsString

class CrawlRootForm(ModelForm):

	class Meta:

		model = CrawlRoot
		fields = ('root_url', 'short_name', 'crawl_depth', 'extract_tags', 
			'focus_tag', 'exclude_tags', 'exclude_in_url_strings')

class CreateModelForm(ModelForm):

	class Meta:

		model = ClassifierModel
		fields = ('name', 'transformer_model_name', 'epochs')


class CrawlRule_URLContainsStringForm(ModelForm):

	class Meta:

		model = CrawlRule_URLContainsString
		fields = ('filter_string',)

class CrawlRule_URLNotContainsStringForm(ModelForm):

	class Meta:

		model = CrawlRule_URLNotContainsString
		fields = ('filter_string',)

class UserInputForm(Form):

     user_input = CharField(label='Input')

class QAPairForm(ModelForm):

	class Meta:

		model = QAPair
		fields = ('intent', 'questions', 'answer', 'penalty_text')

class UploadFileForm(Form):

	file = FileField()

