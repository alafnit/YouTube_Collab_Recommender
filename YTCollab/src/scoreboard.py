'''Contains the scoring algorithm used to determine similarity between channels.
   All functions herewithin assume a DataFrame structure of:

        [id,title,desc,country,banner,subs,videos,views,each topic as a column]

   The primary method of determining similarity is cosine_similarity from
   sklearn.metrics.pairwise and the primary function from this module is intended
   to be most_similar.'''


import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler


class Scoreboard(object):


    def __init__(self):

        '''Initializes the Scorboard Class.'''

        self.X = None
        self.scaled_X = None
        self.y = None
        self.scaled_y = None
        self._scaler = StandardScaler()
        self.replacement = False
        self.scores = None
        self.ranks = None


    def fit(self, X, y):

        '''INPUT: DataFrame, DataFrame
           ---
           Internalizes the given DataFrame. Scaling information uses X but a
           copy of X is stored as df for the purpose of updating information
           each time a new y is passed. If y is not present in df, this function
           also appends y to df as a new entry.'''

        self.X = X
        self.find_similar(y)


    def find_similar(self, y):

        '''INPUT: DataFrame
           ---
           Determines similarity between users and stores the information to be
           called out from the most_similar method.

           To do this, find_similar stores the given DataFrame, scales the
           numerical data in X as a new numpy array scaled_X, scales the
           numerical data in y as a new numpy array scaled_y, and finally
           calculates the cosine similarity scores from the scaled data.

           During this process, the information in y is appended to the internal
           DataFrame df. At the end, df is used to replace the outdated
           DaraFrame X.'''

        self.y = y
        self._scale_X()
        self._scale_y()
        self._calc_scores()


    def _scale_X(self):

        '''Creates an internal variable by scaling the current information in
           X. This scaling of the numerical values of X is used in determining
           the cosine similarity between y and each row of X.'''

        #removing non-numerical data for the scaler
        prepped_X = self.X.drop(['id','title','country','banner','desc'], axis=1)
        self._scaler.fit(prepped_X)
        self.scaled_X = self._scaler.transform(prepped_X)


    def _scale_y(self):

        '''Creates an internal variable by scaling the current information in
           y. This scaling of the numerical values of y is used in determining
           the cosine similarity between y and each row of X.

           In order to achieve this, certain values must be implanted and
           removed from the y DataFrame as not all columns in X are in y, and
           vice versa.'''

        #removing non-numerical data for the scaler
        prepped_y = pd.DataFrame(self.y, columns=self.X.columns).fillna(0)
        self.scaled_y = self._scaler.transform(prepped_y.drop(['id',
                                                               'title',
                                                               'country',
                                                               'banner',
                                                               'desc'],
                                                              axis=1))


    def _calc_scores(self):

        '''Calculates the cosine similarity between each entry in df and y, and
           also determines the ranks of each entry in X based on how similar the
           entry is with user y, putting the name of each user into a list
           ordered from highest to lowest score. The entry for y in X is skipped
           to avoid returning a match with itself.'''

        self.scores = cosine_similarity(self.scaled_X, self.scaled_y).T
        iranks = np.argsort(self.scores)[0][::-1]
        #Ignore case where entry is already in large dataset
        try:
            dup_i = np.where(self.X['title'] == self.y['title'][0])[0]
        except:
            dup_i = None
        self.ranks = [{'url':'https://www.youtube.com/channel/'+self.X['id'][i],
                       'title':self.X['title'][i],
                       'desc':str(self.X['desc'][i]).split('\n'),
                       'bannerurl':self.X['banner'][i]} for i in iranks if not i == dup_i]


    def most_similar(self, k1=10, k2=None):

        '''INPUT: int(default=10), int(optional)
           OUTPUT: list
           ---
           Returns a list of the channels with the given similarity ranks. As
           default, it returns the 10 most similar channels from highest to
           lowest score.

           If k1 is given by itself, most_similar returns the k1 most similar
           channels from highest to lowest score.

           If k2 is given, most_similar returns k1 - k2 channels ranging between
           the ranks of k1 and k2 when k1 < k2.'''

        if k2:
            try:
                return self.ranks[k1:k2]
            except:
                return self.ranks[k1:]
        else:
            try:
                return self.ranks[:k1]
            except:
                return self.ranks
