import json
from os import path
from datetime import datetime 

from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener

from sqlalchemy import DateTime
from sqlalchemy.orm.exc import NoResultFound

from data_analysis.database import session, Tweet, Hashtag, User

from data_analysis._util import WorkerThread
from queue import Queue


consumer_key = 'mpyQQqLooq'
consumer_secret = 'CK1bmR7tZinYuaxwCc'
access_token = '3702780913-tS80TesD27'
access_token_secret = 'O5FB5S4Bm1NnfEVJCN'


auth = OAuthHandler(consumer_key,
                    consumer_secret)

auth.set_access_token(access_token, access_token_secret)


def save_tweets():
    directory = _get_dir_absolute_path()
    filepath = path.join(directory, 'tweets.json')

    listener = DatabaseListener(number_tweets_to_save=1000, filepath=filepath)
    stream = Stream(auth, listener)
    languages = ('en',)
    try:
        stream.sample(languages=languages)
    except KeyboardInterrupt:
        # listener.file.close()
        pass


class DatabaseListener(StreamListener):
    def __init__(self, number_tweets_to_save, filepath=None):
        self._final_count = number_tweets_to_save
        self._current_count = 0
        # self._queue = Queue()
        # self._thread = WorkerThread(self._queue)
        if filepath is None:
            filepath = 'tweets.txt'
        self.file = open(filepath, 'w')

    def on_data(self, raw_data):
        data = json.loads(raw_data)
        json.dump(raw_data, self.file)
        self.file.write("\n")
        if 'in_reply_to_status_id' in data:
            return self.on_status(data)

    def on_status(self, data):
        # NOTE: This method is definied in this file
        result = save_to_database(data)
        self._current_count += 1
        # print(self._current_count)
        # self._queue.put((save_to_database, (data,), {}))
        print('Status count: {}'.format(self._current_count))
        if self._current_count >= self._final_count:
            return False


_TIME_FORMAT ='%a %b %d  %H:%M:%S +0000 %Y' 

def create_user_helper(user_data):
    # alias to shorten calls
    u = user_data
    user = User(uid=u['id_str'],
                name=u['name'],
                screen_name=u['screen_name'],
                created_at=datetime.strptime(u['created_at'],
                                             _TIME_FORMAT),

                description=u.get('description'),
                followers_count=u['followers_count'],
                statuses_count=u['statuses_count'],
                favourites_count=u['favourites_count'],
                friends_count=u['friends_count'],
                listed_count=u['listed_count'],
                geo_enabled=u['geo_enabled'],
                lang=u.get('lang'))

    return user


def create_tweet_helper(tweet_data, user):
    # alias to shorten calls
    t = tweet_data
    retweet = True if t['text'][:3] == 'RT ' else False
    coordinates = t['coordinates']
    if coordinates is not None:
        coordinates = json.dumps(t['coordinates'])

    tweet = Tweet(tid=t['id_str'],
                  tweet=t['text'],
                  user=user,
                  coordinates=coordinates,
                  created_at=datetime.strptime(t['created_at'],
                                               _TIME_FORMAT),

                  favorite_count=t['favorite_count'],
                  in_reply_to_screen_name=t.get('in_reply_to_screen_name'),
                  in_reply_to_status_id=t.get('in_reply_to_status_id'),
                  in_reply_to_user_id=t.get('in_reply_to_user_id'),
                  lang=t.get('lang'),
                  quoted_status_id=t.get('quoted_status_id'),
                  retweet_count=t['retweet_count'],
                  source=t['source'],
                  is_retweet=retweet)

    return tweet


def save_to_database(data):
    try:
        session.query(Tweet).filter_by(tid=data['id']).one()
        return False
    except NoResultFound:
        pass

    try:
        user = session.query(User).filter_by(uid=str(data['user']['id'])).one()
    except NoResultFound:
        user = create_user_helper(data['user'])
        session.add(user)

    hashtag_results = []
    hashtags = data['entities']['hashtags']
    for hashtag in hashtags:
        hashtag = hashtag['text'].lower()
        try:
            hashtag_obj = session.query(Hashtag).filter_by(text=hashtag).one()
        except NoResultFound:
            hashtag_obj = Hashtag(text=hashtag)
            session.add(hashtag_obj)
            session.commit()

        hashtag_results.append(hashtag_obj)

    tweet = create_tweet_helper(data, user)

    for hashtag in hashtag_results:
        tweet.hashtags.append(hashtag)

    session.add(tweet)
    session.commit()
    return True


def _get_dir_absolute_path():
    """
    helper method to get the absolute path of the file directory
    """
    directory = path.abspath(path.dirname(__file__))
    return directory


if __name__ == '__main__':
    save_tweets()
