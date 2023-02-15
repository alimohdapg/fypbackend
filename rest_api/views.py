from rest_framework import viewsets, generics
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from transformers import pipeline, AutoTokenizer
from optimum.onnxruntime import ORTModelForSequenceClassification

MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = ORTModelForSequenceClassification.from_pretrained("./onnx")
troberta = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)


def preprocess(comments):
    new_comments = []
    for comment in comments:
        new_text = []
        for t in comment.split(" "):
            t = '@user' if t.startswith('@') and len(t) > 1 else t
            t = 'http' if t.startswith('http') else t
            new_text.append(t)
        new_comments.append(" ".join(new_text))
    return new_comments


@api_view(['GET'])
def index(request):
    video_url = request.query_params.get('video_url')
    output = troberta('Covid cases are increasing')[0]
    return Response(output)
