# API client library
import googleapiclient.discovery
from googleapiclient.model import HttpError
from urllib.parse import urlparse, parse_qs
import os
import environ

env = environ.Env()
environ.Env.read_env('.env')

# API information
api_service_name = "youtube"
api_version = "v3"
# API key
DEVELOPER_KEY = os.environ.get('DEVELOPER_KEY', default=env('DEVELOPER_KEY'))
# API client
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=DEVELOPER_KEY)


# def get_video_id(url):
#     parsed = urlparse(url)
#     query = parse_qs(parsed.query)
#     print(query)
#     return query["video_url"][0]


def get_comments_for_video(video_id):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id
    )
    comment_response = request.execute()
    next_page_token = comment_response.get('nextPageToken')
    while 'nextPageToken' in comment_response:
        next_page = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        comment_response['items'] = comment_response['items'] + next_page['items']
        if 'nextPageToken' not in next_page:
            comment_response.pop('nextPageToken', None)
        else:
            next_page_token = next_page['nextPageToken']
    if len(comment_response['items']) > 0:
        for item in comment_response['items']:
            # 2155 is the maximum length that can be passed to the sentiment analysis pipeline
            comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'][:2155])
    return comments
