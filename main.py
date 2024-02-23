# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from newsapi import NewsApiClient
import requests


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Init
    newsapi = NewsApiClient(api_key='3cdec57655f74099b1992696cd971a15')

    url = "https://newsapi.org/v2/top-headlines?country=cn&apiKey=3cdec57655f74099b1992696cd971a15"

    # /v2/top-headlines
    top_headlines = newsapi.get_top_headlines(language='zh',
                                              country='cn')

    # # /v2/everything
    # all_articles = newsapi.get_everything(q='bitcoin',
    #                                       sources='bbc-news,the-verge',
    #                                       domains='bbc.co.uk,techcrunch.com',
    #                                       from_param='2017-12-01',
    #                                       to='2017-12-12',
    #                                       language='en',
    #                                       sort_by='relevancy',
    #                                       page=2)

    # /v2/top-headlines/sources
    # sources = newsapi.get_sources()
    print(top_headlines)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
