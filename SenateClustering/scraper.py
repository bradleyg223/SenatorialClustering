# import packages for web scraping
from bs4 import BeautifulSoup
import requests
import re

# sklearn
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# data processing
import pandas as pd
from numpy import where

# class for scraping, and storing data
class Scrape():
    def __init__(self, congress=117, session=1, votes=10) -> None:
        self.congress = congress
        self.session = session
        self.session_url = f'https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{str(self.congress)}_{str(self.session)}.htm'
        self.votes=votes
        self.vote_urls = self.get_votes_url()


    def get_votes_url(self) -> list:
        '''
        Given the current Congress and Session, this function will return a list of all roll call vote URLs
        '''
        page = requests.get(self.session_url)
        soup = BeautifulSoup(page.content, 'html.parser')

        # find table with id of 'listOfVotes_info'
        table = soup.find('table', id='listOfVotes')
        table = table.prettify()

        # get urls from scraped link. Each URL we will use contains votes
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', table)
        urls = [url for url in urls if 'roll_call_votes' in url]

        return urls

    # return a df
    def get_data(self) -> pd.DataFrame:
        '''
        n_votes is the number of votes to scrape. Put -1 for all votes
        given the urls, this function will return a dataframe with all the data
        '''
        votes = []

        # for loop, scraping each page
        for url in self.vote_urls[:self.votes]:
            vote_url = 'https://www.senate.gov{vote}'.format(vote=url)

            page = requests.get(vote_url)
            soup = BeautifulSoup(page.content, 'html.parser')

                # get div with class newspaperDisplay_3column
            div = soup.find('div', class_='newspaperDisplay_3column')
            vote_det = div.prettify().split('\n  </b>')
            voter = [i.split('\n')[2] for i in vote_det]
            casted = [i.split('\n')[4] for i in vote_det]
            id_vote = [url.split('/')[-1].split('.')[0]] * len(voter)

            votes.append([voter, casted, id_vote])

        self.df = self.__clean_data(votes)

    def __clean_data(self, votes):
        '''
        This function will clean the dataframe
        '''
        yea_vals = ['Yea', 'Guilty']
        nay_vals = ['Nay', 'Not Guilty']
        abstain_vals = ['Abstain', 'Absent', 'Not Voting', 'Present', 'Present, Giving Live Pair']

        df = pd.concat([pd.DataFrame(votes[i]).T for i in range(len(votes))])
        df.columns=['Senator', 'Cast', 'Vote']
        df = df[df['Cast']!='']
        df['Cast'] = df['Cast'].str.strip()

        df['cast_recode'] = where(df['Cast'].str.contains('Yea'), 1, df.Cast)
        df['cast_recode'] = where(df['Cast'].str.contains('Guilty'), 1, df.cast_recode)
        df['cast_recode'] = where(df['Cast'].str.contains('Nay'), 0, df.cast_recode)
        df['cast_recode'] = where(df['Cast'].str.contains('Not Guilty'), 0, df.cast_recode)
        # if not voting or present, then 0
        df['cast_recode'] = where(df['Cast'].str.contains('Not Voting|Present, Giving Live Pair'), 0, df.cast_recode)
        df['cast_recode'] = where(df['Cast'] == 'Present', 0, df.cast_recode)
        df['cast_recode'] = df['cast_recode'].astype(int)
        return df

    def cluster(self, vote_threshold = 1, n_clusters = 2):
        '''
        This function will return a dataframe with the senators clustered together
        '''
        df_pivot = self.df.pivot(index='Senator', columns='Vote', values='cast_recode').reset_index()

        # gets number of non-zero votes, and will remove senators with less than the vote_threshold
        drop_id = df_pivot[df_pivot.columns[2:]].abs().sum(axis=1).where(df_pivot[df_pivot.columns[2:]].abs().sum(axis=1)<vote_threshold).dropna().index
        df_pivot = df_pivot.drop(drop_id, axis=0)
        
        # get records of senators who voted
        df_pivot.reset_index(inplace=True, drop=True)        

        # get's votes from the dataframes, and decomposes using Prinicpal Component Analysis
        X = df_pivot.drop(['Senator'], axis=1).values.astype(int)
        X_transform = PCA().fit_transform(X)

        # cluster
        kmeans = KMeans(n_clusters=4, random_state=0).fit(X_transform)
        df_pivot['cluster'] = kmeans.labels_

        # import plotly
        import plotly.express as px

        # plot the above, with an interactive legend
        fig = px.scatter_3d(df_pivot, x=X_transform[:, 0], y=X_transform[:, 1], z=X_transform[:, 2],
                            color = kmeans.labels_,
                            
                            hover_name='Senator'
        )

        import os
        # if not in current directory make new directory 'export'
        if not os.path.exists('export'):
            os.makedirs('export')
        fig.write_html(f"export/{self.congress}_{self.session}_{self.votes}.html")