import dateutil.parser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from transformers import pipeline, AutoTokenizer
from optimum.onnxruntime import ORTModelForSequenceClassification
from .youtube_data import get_comments_for_video, advanced_get_comments_for_video
from googleapiclient.model import HttpError

MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = ORTModelForSequenceClassification.from_pretrained("rest_api/onnx")
troberta = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, max_length=512, truncation=True)


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


def get_percentages(preds):
    pos_count = 0
    neg_count = 0
    neu_count = 0
    for pred in preds:
        if pred['label'] == 'positive':
            pos_count += 1
        elif pred['label'] == 'negative':
            neg_count += 1
        else:
            neu_count += 1
    total = pos_count + neg_count + neu_count

    def to_percentage(count):
        return round(count / total * 100, 1)

    return {'Positive': to_percentage(pos_count), 'Negative': to_percentage(neg_count),
            'Neutral': to_percentage(neu_count)}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def index(request):
    video_id = request.query_params.get('video_id')
    if video_id is None:
        return Response({"detail": "video_id parameter not supplied"})
    priority = request.query_params.get('priority')
    if priority:
        comment_count = int(request.query_params.get('comment_count'))
        like_count = int(request.query_params.get('like_count'))
        min_max_like_count = True if request.query_params.get('min_max_like_count') == 'min' else False
        date = dateutil.parser.isoparse(request.query_params.get('date'))
        try:
            comments = advanced_get_comments_for_video(video_id, priority, comment_count, like_count,
                                                       min_max_like_count, date)
        except HttpError:
            return Response({"detail": "one or more parameter is invalid"})
    else:
        try:
            comments = get_comments_for_video(video_id)
        except HttpError:
            return Response({"detail": "one or more parameter is invalid"})
    if len(comments) == 0:
        return Response({"detail": "video has no comments"})
    output = get_percentages(troberta(preprocess(comments)))
    return Response(output)
