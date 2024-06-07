import os
import requests
import csv
from textblob import TextBlob
from time import sleep
import subprocess

if os.environ.get("API_KEY"):
    API_KEY = os.environ.get("API_KEY")
else:
    raise Exception("API KEY not set")
    
params = {
    'q': 'Donald Trump',
    'apiKey': API_KEY,
    'language':'en',
    'sources': 'bbc-news,cnn,fox-news,nbc-news,the-guardian-uk,the-new-york-times,the-washington-post,usa-today,independent,daily-mail'
}
url = "https://newsapi.org/v2/everything"

def fetch_data(page=1):
    params["page"] = page
    response = requests.get(url, params=params).json()
    return response

def get_sentiment(score):
    if score > 0:
        return 1.0
    else:
        return 0

create_hdfs_bigdata_folder = """
hadoop fs -mkdir -p /bigdata
"""

subprocess.run(create_hdfs_bigdata_folder, shell=True, check=True)

response = fetch_data()
totalResults = response["totalResults"]
if totalResults > 100:
    pages = totalResults//100
else:
    pages = 1
if pages > 10:
    pages = 10


page = 1
rounds = 0  
while True:
    file_name = f"news_feed_{page}_{rounds}.csv"
    hdfs_path = f"/bigdata/{file_name}"
    with open(file_name, 'w', newline='', encoding='utf-8') as local_file:
        csv_writer = csv.writer(local_file)
        csv_writer.writerow(['title', 'source', 'content', 'sentiment'])

        try:
            articles = fetch_data(page=page)["articles"]
        except KeyError:
            print("At last page of article")
            page = 1
            rounds +=1
            sleep(60)
            continue

        for data in articles:

            date = data['publishedAt']
            title = data['title']
            source_name = data['source']['name']
            content = data['content']

            title_blob = TextBlob(title)
            cleaned_title = " ".join(title_blob.words)
            print('Title:',cleaned_title)
            print("*"*50)

            content_blob = TextBlob(content)
            cleaned_content = " ".join(content_blob.words)
            content_sentiment_score = content_blob.sentiment.polarity

            sentiment = get_sentiment(content_sentiment_score)

            csv_writer.writerow([cleaned_title, source_name, cleaned_content, sentiment])


    hdfs_move_script = f"""
    hadoop fs -copyFromLocal {file_name} {hdfs_path}
    """

    subprocess.run(hdfs_move_script, shell=True, check=True)
    page +=1
    sleep(10)



    