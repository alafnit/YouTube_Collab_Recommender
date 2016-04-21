# YouTube_Collab_Recommender

This project is a YouTube Recommender for Collaborations. What I mean by this is that it looks at the meta data and statistics of a channel and its first few videos and recommends similar channels to work with based on the same data.

The results are easily accessible through web application.

## Motivation

In recent years, YouTube as a platform for artistic expression and self-employment has exploded, creating a wide network of internet celebrities spanning a broad spectrum of topics. As channels continue to expand on the merits of their hosts' products and personalities, they slowly restructure to reflect more standard business models. As such, for a channel to continue its success, it must continuously expand its market or audience. Of course there are several ways to do this as outlined by the [YouTube Creator Academy](https://creatoracademy.withgoogle.com/creatoracademy/page/education), such as mastering Search Engine Optimization or taking advantage of various social media. One of the more complex and creative ways of expanding your audience is the use of the YouTube collaboration.

In working together, creators end up combining their audiences and trading subscribers with one another, mutually benefiting from cooperation. For the best result, creators will often seek out others with similar content and audiences. After all, why try expanding into audiences who aren't as likely to subscribe? But the problem then becomes "Who alreayd has a similar audience?" That's where this recommendation model comes in.

## Pipeline

1. Initial Exploration of YouTube Data API via free test queries available in the [YouTube API Documentation](https://developers.google.com/youtube/v3/docs/), as well as acquisition of a Google Developer YouTube Data API Key.
2. Extraction of basic channel data using the [channels list](https://developers.google.com/youtube/v3/docs/channels/list) functionality of the API, calling on channels that apply for the various Guide Category Ids, available by calling the [Guide Categories List](https://developers.google.com/youtube/v3/docs/guideCategories/list) using the region code 'US'.
3. Using Pandas DataFrames, assemble the data needed for analysis and presentation: id, title, description, country, banner urls, subscriber count, video count, views, and topics. Topics require additional processing before entry in the DataFrames, explained below.
4. In order to extract topics, the topic ids on the channel and in the channels videos must be analyzed and aggregated. This model uses a frequency of topic occurrence over the most recent 25 videos of a channel. A list is created including each occurrence of a topic on the channel or a video and the list is fed into a counter so each topic id is aggregated by summation. Then, a column is made for each distinct topic id and the value in a row's counter for that topic is entered as that columns value for that row, where default values occur as 0, naturally.
5. The DataFrame for each category is then written and stored as individual csv's for future comparisons.
6. For the purpose of recommendation an individual user is extracted using the exact same method but kept separate from the other data sets.
7. The original base data set for any single category is scaled using the StandardScaler from sklearn, and after the scaler has been fitted with the training data, the individual user is scaled as well. The cosine similarity from sklearn is then calculated between the individual user and each other channel in the base DataFrame.
8. The results are sorted by cosine similarity and returned in the form of titles, ids, banners, and descriptions of their respective channels. If the individual channel occurs in the dataset itself, it is removed from the results so that perfect matches are avoided.
