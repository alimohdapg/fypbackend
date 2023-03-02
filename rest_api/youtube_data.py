# API client library
import googleapiclient.discovery
import os
import environ
import dateutil.parser

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


def get_comments_for_video(video_id):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
    )
    comment_response = request.execute()
    next_page_token = comment_response.get('nextPageToken')
    while 'nextPageToken' in comment_response and len(comment_response['items']) < 1000:
        next_page = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
        ).execute()
        comment_response['items'] = comment_response['items'] + next_page['items']
        if 'nextPageToken' not in next_page:
            comment_response.pop('nextPageToken', None)
        else:
            next_page_token = next_page['nextPageToken']
    comments = []
    if len(comment_response['items']) > 0:
        for item in comment_response['items']:
            # 1400 is the maximum length that can be passed to the sentiment analysis pipeline
            comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'][:1400])
    return comments


def advanced_get_comments_for_video(video_id, priority, comment_count, like_count, min_max_like_count, date):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        order=priority
    )
    comment_response = request.execute()
    add_to_comments(comment_response['items'], comments, comment_count, like_count, min_max_like_count, date)
    next_page_token = comment_response.get('nextPageToken')
    while 'nextPageToken' in comment_response and dateutil.parser.isoparse(
            comment_response['items'][-1]['snippet']['topLevelComment']['snippet']['publishedAt']) < date and \
            len(comments) != comment_count:
        next_page = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            order=priority
        ).execute()
        add_to_comments(next_page['items'], comments, comment_count, like_count, min_max_like_count, date)
        if 'nextPageToken' not in next_page:
            comment_response.pop('nextPageToken', None)
        else:
            next_page_token = next_page['nextPageToken']
    return comments


def add_to_comments(comment_response_items, comments, comment_count, like_count, min_max_like_count, date):
    if len(comment_response_items) > 0:
        for item in comment_response_items:
            # 1400 is the maximum length that can be passed to the sentiment analysis pipeline
            if dateutil.parser.isoparse(item['snippet']['topLevelComment']['snippet']['publishedAt']) > date:
                if min_max_like_count:
                    if item['snippet']['topLevelComment']['snippet']['likeCount'] >= like_count:
                        comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'][:1400])
                else:
                    if item['snippet']['topLevelComment']['snippet']['likeCount'] < like_count:
                        comments.append(item['snippet']['topLevelComment']['snippet']['textOriginal'][:1400])
            if len(comments) == comment_count:
                break
    return comments
