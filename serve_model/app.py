from flask import Flask, request
from json import load
from transformers import AutoTokenizer,AutoModelForSequenceClassification
import torch

MODEL_NAME = "F1"
MAX_QAPAIRS = 5
MAX_WEBPAGES = 5

device = "cpu"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)


with open(MODEL_NAME + "/label2flask.json") as json_file:
    label2flask = load(json_file)

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False

@app.route("/ChatEME/", methods=['POST', 'GET'])
def tag_nes():
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
