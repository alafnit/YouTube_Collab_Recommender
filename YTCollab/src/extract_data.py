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
    for _ in xrange(100):
        results = youtube.channels().list(part="snippet,statistics,topicDetails",
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
    row['title'] = channel["snippet"]["title"]
    try:
        row['country'] = channel["snippet"]["country"]
    except:
        row['country'] = 'n/a'
    row['subs'] = int(channel["statistics"]["subscriberCount"])
    row['videos'] = int(channel["statistics"]["videoCount"])
    row['views'] = int(channel["statistics"]["viewCount"])
    row['topics'] = [channel_topics(youtube, channel)]
    cols = ['title','country','subs','videos','views','topics']
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
    playlists = youtube.playlists().list(part='id',
                                         channelId=channel['id'],
                                         maxResults=5).execute()
    for playlist in playlists['items']:
        topics.extend(sample_playlist(youtube, playlist['id']))
    return list(set(topics))


def sample_playlist(youtube, playlist):

    '''INPUT: YouTube Query Builder, string
       OUTPUT: list
       ---
       Returns a list of topics present in the first few videos of a given
       playlist.'''

    topics = []
    videos = []
    results = youtube.playlistItems().list(playlistId=playlist,
                                           part='contentDetails').execute()
    for video in results['items']:
        videos.append(video['contentDetails']['videoId'])

    topics.extend(sample_videos(youtube, ','.join(videos)))
    return topics


def sample_videos(youtube, videoIds):

    '''INPUT: YouTube Query Builder, string
       OUTPUT: list
       ---
       Returns a list of topics present in the given videos.'''

    topics = []
    results = youtube.videos().list(part='topicDetails', id=videoIds).execute()
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


def get_specific_channel(channel):

    '''INPUT: string
       OUTPUT:
       ---
       Returns a DataFrame of a single channel's YouTube data, following the
       same pipeline as get_channel_data.'''

    DEVELOPER_KEY = os.environ["COLLAB_CLIENT_KEY"]
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    results = youtube.channels().list(part="snippet,statistics,topicDetails",
                                      id=channel).execute()
    return process_results(youtube, results)


def unpack_topics(df):

    '''INPUT: Pandas DataFrame
       OUTPUT: Pandas DataFrame
       ---
       Returns a version of the given DataFrame where all topics in each row's
       topic column has been converted into a boolean dummy variable.'''

    df_new = df.copy()
    allTopics = set()
    for row in df_new['topics']:
        allTopics.update(row)
    print allTopics
    for topic in allTopics:
        df_new[topic] = 0
        print topic
    for i, row in enumerate(df_new['topics']):
        print 'line %d processing' % i
        for topic in row:
            df_new[topic][i] = 1
    return df_new.drop(['topics'], axis=1)


def write_file(category):

    '''INPUT: string
       ---
       Runs get_channel_data on the given category and unpacks the topics in the
       resulting DataFrame. Then, it writes the entire DataFrame to a csv in the
       data folder of the repository.'''

    df = get_channel_data(category)
    df = unpack_topics(df)
    s = category.replace(' ', '_').replace('&', 'and')
    df.to_csv('../data/YT'+s+'_base.csv', encoding='utf-8')

def _write_user(userId):

    '''INPUT: string
       ---
       Same as write_file, but on one person given their channelId.
       For testing writing functionality.'''

    df = get_specific_channel(userId)
    df = unpack_topics(df)
    df.to_csv('../data/YT_'+userId+'_data.csv', encoding='utf-8')
