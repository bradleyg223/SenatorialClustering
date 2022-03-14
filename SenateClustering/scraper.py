# import packages for web scraping
from bs4 import BeautifulSoup
import requests

# class for scraping, and storing data
class Scrape():
    def __init__(self, congress=117, session=1) -> None:
        self.congress = congress.astype(str)
        self.session = session.astype(str)
        self.session_url = f'https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{self.congress}_{self.session}.htm'
        self.vote_urls = self.get_votes_url()


    def get_votes_url(self) -> list:
        page = requests.get(self.session_url)
        soup = BeautifulSoup(page.content, 'html.parser')

        # find table with id of 'listOfVotes_info'
        table = soup.find('table', id='listOfVotes')
        table = table.prettify()

        import re

        # get urls from scraped link. Each URL we will use contains votes
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', table)
        urls = [url for url in urls if 'roll_call_votes' in url]

        return urls


    def get_data(self) -> None:
        votes = []

        # for loop, scraping each page
        for url in urls:
            vote_url = 'https://www.senate.gov{vote}'.format(vote=url)

            page = requests.get(vote_url)
            soup = BeautifulSoup(page.content, 'html.parser')

                # get div with class newspaperDisplay_3column
            div = soup.find('div', class_='newspaperDisplay_3column')
            vote_det = div.prettify().split('\n  </b>')
            voter = [i.split('\n')[2] for i in vote_det]
            casted = [i.split('\n')[4] for i in vote_det]
            votes.append([voter, casted])

        df = pd.concat([pd.DataFrame(votes[i]).T for i in range(len(votes))])
        df = df[df['Cast']!='']
        df['Cast'] = df['Cast'].str.strip()

            id_vote = [url.split('/')[-1].split('.')[0]] * len(voter)

        votes.append([voter, casted, id_vote])