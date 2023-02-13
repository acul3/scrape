import requests
from bs4 import BeautifulSoup
import json

headers = {
    'authority': 'www.sehatq.com',
    'cache-control': 'max-age=0',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en,de;q=0.9,en-US;q=0.8,id;q=0.7'
}


def print_site(url):
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    print(soup.prettify())


def article_get(url):
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    script = json.loads(soup.find_all('script')[2].string)
    article = {}
    article["title"] = script['mainentity']['name']
    article["question"] = {}
    article["question"]["text"] = script['mainentity']['text']
    article["question"]["author"] = script['mainentity']['author']['name']
    article["question"]["answerCount"] = script['mainentity']['answerCount']
    article["question"]["upvoteCount"] = script['mainentity']['upvoteCount']
    article["question"]["dateCreated"] = script['mainentity']['dateCreated'].replace(" Question sent", "")
    article["answer"] = {}
    article["answer"]["text"] = script['mainentity']['acceptedAnswer']['text']
    article["answer"]["author"] = script['mainentity']['acceptedAnswer']['author']['name']
    article["answer"]["upvoteCount"] = script['mainentity']['acceptedAnswer']['upvoteCount']
    article["answer"]["dateCreated"] = script['mainentity']['acceptedAnswer']['dateCreated']
    return article

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
#    article_name = "tespack-hasil-samar-q41769"
#    article = article_get("https://www.sehatq.com/forum/" + article_name)
#    with open(article_name+".json", "w") as f:
#        json.dump(article, f)
    print_site("https://www.sehatq.com/forum/kandungan")
    #article_get("http://localhost:9999")
