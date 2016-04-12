'''Contains the scoring algorithm used to determine similarity between channels.
   All functions herewithin assume a DataFrame structure of:

        [title, country, subs, videos, views, each topic as a column]

   The primary method of determining similarity is cosine_similarity from
   sklearn.metrics.pairwise and the primary function from this module is intended
   to be most_similar.'''


import pandas as import pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class Scoreboard(object):


    def __init__(self):

        '''Initializes the Scorboard Class.'''

        self.df = None
        self.y = None
        self.scores = None
        self.df_ranked_idx = None


    def fit(self, df, y=None):

        '''INPUT: DataFrame, DataFrame(optional)
           ---
           Internalizes the given DataFrame. If y is given, the class calculates
           all necessary information. If y is not present in df, this function
           also appends y to df as a new entry.'''

        self.df = df
        if y:
            self.find_similar(y)


    def find_similar(self, y):

        '''INPUT: DataFrame
           ---
           Updates df with infromation given in y and calculates the similarity
           scores between y and df. Also calculates the rank of each entry in df
           from most to least similar. Assumes df has been fitted to Scoreboard.'''

        if len(y.split(',')) > 1:
            print 'Please only use one ID.'\
        else:
            self.y = y
            self._update()
            self.scores = self._calc_scores()
            self.df_ranked_idx = np.argsort(self.scores)[0][::-1]


    def _update(self):

        '''Updates the fitted df with the fitted y. If y is present in df prior
           to updating, it is replaced with the newer information.'''

        self.df.drop(np.where(self.df['title'] == self.y['title'][0])[0])
        self.df.append(self.y):


    def fit_from(self, filepath):

        '''INPUT: string
           ---
           Fits a df into the Scoreboard directly from the given filepath. This
           method does not support simultaneous y fitting.'''

        self.df = pd.read_csv(filepath).drop('Unnamed: 0', axis=1)


    def most_similar(self, k1=10, k2=None):

        '''INPUT: int, int(optional)
           OUTPUT: Numpy Array
           ---
           Returns an array of the channels with the given similarity ranks.
           As default, it returns the 10 most similar channels from highest to
           lowest scores.

           If k1 is given by itself, most_similar returns the k1 most similar
           channels from highest to lowest score.

           If k2 is given, most_similar returns k1 - k2 channels ranging between
           the ranks of k1 and k2 when k1 < k2.'''

        ignored_idx = np.where(df['title'] == y['title'][0])[0][0]
        argsort_scores = np.delete(np.argsort(self.scores)[0][::-1], ignored_idx)
        if k2:
            return self.df['title'][argsort_scores[k1:k2]].values
        else:
            return self.df['title'][argsort_scores[:k1]].values


    def _calc_scores(self):

        '''Calculates the cosine similarity between each entry in df and y,
           skipping the entry for y in df to avoid a perfect match with itself.'''

        df_num = self.df.drop(np.where(self.df['title'] == self.y['title'][0])[0])
        df_num = df_num.drop(['title','country'], axis=1)
        y_num = self.y.drop(['title','country'], axis=1)
        self.scores = cosine_similarity(df_num, y_num).T
