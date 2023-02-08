# ChatEME - Chat Engine Made Easy

ChatEME is an open source web application that lets you easily create faq 
chatbots from question/answer pairs as well as from website data. It includes a 
web editor for the question/answer pairs and a user interface for a web scraper 
that can automatically create training data for the classifier. 

By using the scraper module, it is possible to generate a language model that is
able to semantically search your website with little effort. 
The default language model ([rasa/LaBSE](https://huggingface.co/rasa/LaBSE))
allows you to use any language as input once the model is trained. 

The model server provides a convenient way to access the model via an API.

## Installation 
### Ubuntu 22.04

```
git clone https://www.github.com/fdewes/ChatEME
cd ChatEME/ChatEME
pip install -r ../requirements.txt
make init
echo SECRET_KEY=\"`tr -dc A-Za-z0-9 </dev/urandom | head -c 50 ; \
  echo ''`\" >> ChatEME_app/settings.py
./manage.py runserver 0:8000
```
