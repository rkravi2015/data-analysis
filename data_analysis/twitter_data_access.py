import json
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream, API

consumer_key = 'mpyQQqLooqGfVaFnVT2vWrNwn'
consumer_secret = 'CK1bmR7tZinYuaxwCcYGuDpsfAVf6cAywLESv0BkCbYsJLk9OY'
access_token = '3702780913-tS80TesD27dYUaunh87TcaYRewcHeSHjlYudqHJ'
access_token_secret = 'O5FB5S4Bm1NnfEVJCN2ttCrUJBhgCs8Ygw31FgeOSh0vz'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)


class PrintListener(StreamListener):
    def on_status(self, status):
        if not status.text[:3] == 'RT ':
            print(status.text)
            print(status.author.screen_name, status.created_at, status.source,'\n')

    def on_error(self, status_code):
        print("Error code: {}".format(status_code))
        return true #keep stream alive
    def on_timeout(self):
        print('Listener timed out!')
        return true #keep stream alive

def print_to_terminal():
    listener = PrintListener()
    stream = Stream(auth, listener)
    languages = ('en',)
    stream.sample(languages=languages)
def pull_down_tweets(screen_name):
    print("started...")
    print(screen_name)
    api = API(auth)
    tweets = api.user_timeline(screen_name=screen_name, count=200)
    for tweet in tweets:
        print(json.dumps(tweet._json, indent=4))

if __name__ == "__main__":
    #print_to_terminal()
    pull_down_tweets(auth.get_username)
