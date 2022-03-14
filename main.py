
from SenateClustering.scraper import Scrape

def main():
    s = Scrape()
    s.get_data()
    s.cluster()
    
if __name__ == "__main__":
    main()