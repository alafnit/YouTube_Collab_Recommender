'''Calls on the YouTube API to generate csv files of specific categories of
   YouTube videos. First it calls for channels of the given categories, then
   for each channel the algorithm pulls it's statistics data and playlists, takes
   the first video in the playlist for the purpose of generating topic ids, and
   wraps everything it finds up into an appropriately named csv.'''

import os
import sys
import numpy as np
import pandas as pd
from apiclient.discovery import build
from collections import Counter
import time

def _channel_categories():

    '''OUTPUT: dictionary
       ---
       Utility function. Returns a premade dictionary of YouTube video categories
       from US, with the categories as keys and the respective IDs as values.'''

    d = {"Music":"GCTXVzaWM", "Comedy":"GCQ29tZWR5", "From TV":"GCRnJvbSBUVg",
         "Film & Entertainment":"GCRmlsbSAmIEVudGVydGFpbm1lbnQ",
         "Gaming":"GCR2FtaW5n", "Beauty & Fashion":"GCQmVhdXR5ICYgRmFzaGlvbg",
         "Automotive":"GCQXV0b21vdGl2ZQ", "Animation":"GCQW5pbWF0aW9u",
         "Sports": "GCU3BvcnRz", "How-to & DIY":"GCSG93LXRvICYgRElZ",
         "Tech":"GCVGVjaA", "Science & Education":"GCU2NpZW5jZSAmIEVkdWNhdGlvbg",
         "Cooking & Health":"GCQ29va2luZyAmIEhlYWx0aA",
         "Causes & Non-profits":"GCQ2F1c2VzICYgTm9uLXByb2ZpdHM",
         "News & Politics":"GCTmV3cyAmIFBvbGl0aWNz", "Lifestyle":"GCTGlmZXN0eWxl"}
    return d

def get_channel_data(category):

    '''INPUT: string
       OUTPUT: Pandas DataFrame
       ---
       Creates a DataFrame from YouTube channel data including: channel name,
       country, subscriber count, video count, view count, and list of recent
       topics.'''

    DEVELOPER_KEY = os.environ["COLLAB_CLIENT_KEY"]
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    d = _channel_categories()
    try:
        d[category]
    except:
        print "Not a valid channel category. Try one of these:"
        print d.keys()
        sys.exit()

    df = pd.DataFrame()
    nextPage = None
    sections = "id,snippet,contentDetails,statistics,topicDetails,brandingSettings"
    for _ in xrange(100):
        results = youtube.channels().list(part=sections,
                                          categoryId=d[category],
                                          maxResults=50,
                                          pageToken=nextPage).execute()
        df = df.append(process_results(youtube, results), ignore_index=True)
        try:
            nextPage = results['nextPageToken']
        except:
            break
    return df


def process_results(youtube, results):

    '''INPUT: YouTube Query Builder, YouTube Response
       OUTPUT: Pandas DataFrame
       ---
       Assembles a DataFrame using the current page of results acquired in
       get_channel_data by passing each channel to a vectorizer:
       process_channel.'''

    df = pd.DataFrame()
    for channel in results["items"]:
        df = df.append(process_channel(youtube, channel), ignore_index=True)
    return df


def process_channel(youtube, channel):

    '''INPUT: YouTube Query Builder, YouTube Response
       OUTPUT: Pandas DataFrame
       ---
       Assembles a dictionary from the channel supplied and returns a DataFrame
       row created from said dictionary.'''

    row = {}
    row['id'] = channel["id"]
    row['title'] = channel["snippet"]["title"]
    row['desc'] = channel["snippet"]["description"]
    try:
        row['country'] = channel["snippet"]["country"]
    except:
        row['country'] = 'n/a'
    row['banner'] = channel["brandingSettings"]["image"]["bannerMobileExtraHdImageUrl"]
    row['subs'] = int(channel["statistics"]["subscriberCount"])
    row['videos'] = int(channel["statistics"]["videoCount"])
    row['views'] = int(channel["statistics"]["viewCount"])
    row['topics'] = [channel_topics(youtube, channel)]
    cols = ['id','title','desc','country','banner','subs','videos','views','topics']
    return pd.DataFrame(row, columns=cols)


def channel_topics(youtube, channel):

    '''INPUT: YouTube Query Builder, YouTube Response
       OUTPUT: list
       ---
       Returns a list of topic ids related to the channel. Pulls topics directly
       from the channel response given but also uses the YouTube Query Builder
       to pull topics from the channel's playlists, if any exist.'''

    topics = []
    try:
        topics.extend(channel["topicDetails"]["topicIds"])
    except:
        pass
    """playlists = youtube.playlists().list(part='id',
                                         channelId=channel['id'],
                                         maxResults=5).execute()
    for playlist in playlists['items']:
        topics.extend(sample_playlist(youtube, playlist['id']))
    return Counter(topics)"""
    """videos = youtube.search().list(part='id',
                                   channelId=channel['id'],
                                   order='date',
                                   type='video',
                                   maxResults=25).execute()
    videoIds = ','.join([vid['id']['videoId'] for vid in videos['items']])
    topics.extend(sample_videos(youtube, videoIds))
    return Counter(topics)"""
    uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    topics.extend(sample_playlist(youtube, uploads))
    return Counter(topics)


def sample_playlist(youtube, playlist):

    '''INPUT: YouTube Query Builder, string
       OUTPUT: list
       ---
       Returns a list of topics present in the first few videos of a given
       playlist.'''

    results = youtube.playlistItems().list(playlistId=playlist,
                                           part='contentDetails',
                                           maxResults=25).execute()
    videos = [vid['contentDetails']['videoId'] for vid in results['items']]
    topics = sample_videos(youtube, ','.join(videos))
    return topics


def sample_videos(youtube, videoIds):

    '''INPUT: YouTube Query Builder, string
       OUTPUT: list
       ---
       Returns a list of topics present in the given videos.'''

    topics = []
    results = youtube.videos().list(part='topicDetails',
                                    id=videoIds,
                                    maxResults=25).execute()
    for video in results['items']:
        try:
            topics.extend(video['topicDetails']['topicIds'])
        except:
            pass
        try:
            topics.extend(video['topicDetails']['relevantTopicIds'])
        except:
            pass
    return topics


def get_specific_channel(channel, unpack=True):

    '''INPUT: string
       OUTPUT:
       ---
       Returns a DataFrame of a single channel's YouTube data, following the
       same pipeline as get_channel_data. Default is to unpack the topics for
       this channel, but this can be deactivated to return the Counter in
       the "topics" column instead.'''

    start = time.time()

    DEVELOPER_KEY = os.environ["COLLAB_CLIENT_KEY"]
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    youtube = build(YOUTUBE_API_SERVICE_NAME,
                    YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    sections = "id,snippet,contentDetails,statistics,topicDetails,brandingSettings"
    results = youtube.channels().list(part=sections,
                                      id=channel).execute()
    df_row = process_results(youtube, results)

    print time.time() - start

    if (unpack) & (not df_row.empty):
        return unpack_topics(df_row)
    else:
        return df_row


def unpack_topics(df):

    '''INPUT: Pandas DataFrame
       OUTPUT: Pandas DataFrame
       ---
       Returns a version of the given DataFrame where all topics in each row's
       topic column has been converted into a boolean dummy variable.'''

    df_new = df.copy()
    allTopics = set()
    for row in df_new['topics']:
        allTopics.update(row.keys())
    for topic in allTopics:
        df_new[topic] = 0
    for i, row in enumerate(df_new['topics']):
        for topic, count in row.iteritems():
            df_new[topic][i] = count
    return df_new.drop(['topics'], axis=1)


def write_file(category, s=None):

    '''INPUT: string
       ---
       Runs get_channel_data on the given category and unpacks the topics in the
       resulting DataFrame. Then, it writes the entire DataFrame to a csv in the
       data folder of the repository.'''
    if s:
        print s
    else:
        print 'No string.'
    df = get_channel_data(category)
    if df.empty:
        print category, 'is empty.'
    else:
        df = unpack_topics(df)
        if s:
            df.to_csv('../data/'+s+'.csv', encoding='utf-8')
        else:
            s = category.replace(' ', '_').replace('&', 'and')
            df.to_csv('../data/YT'+s+'_data.csv', encoding='utf-8')

def _write_user(userId):

    '''INPUT: string
       ---
       Same as write_file, but on one person given their channelId.
       For testing writing functionality.'''

    df = get_specific_channel(userId)
    df = unpack_topics(df)
    df.to_csv('../data/YT_'+userId+'_data.csv', encoding='utf-8')


def match_topics(X, y):

    '''INPUT: DataFrame, DataFrame
       OUTPUT: DataFrame, DataFrame
       ---
       Unpacks the topics of y to match the format of the current X. If y has a
       topic not yet present in X, that topic is added to X. Returns the results
       of this unpacking, in this order: X, then y. Assumes that y has a 'topics'
       column and X does not.'''

    X_new = X.copy()
    y_new = y.copy()
    for topic in X_new.columns[5:]:
        y_new[topic] = 0
    for row in y_new['topics']:
        for i, topic in enumerate(row):
            try:
                y_new[topic][i] = 1
            except:
                y_new[topic] = 0
                y_new[topic][i] = 1
                X_new[topic] = 0
    y_new = y_new.drop('topics', axis=1)
    return X_new, y_new
