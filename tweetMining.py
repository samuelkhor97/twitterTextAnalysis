import tweepy
import json
import re
import string
from collections import Counter
from tweepy import OAuthHandler
from tweepy import Stream
from nltk.corpus import stopwords
from nltk import bigrams
from collections import defaultdict

consumer_key = 'HJredlx2UD0aO6Yw8RnnRcLSh'
consumer_secret = 'Heb6js60nSIIraqS1lTolxPJcbQbt6yFwean8jTpfjIfabjbme'
access_token = '2403921554-crXxfA7r2o2oBJ6uYxMccZrWgzn3QmLup8SEcBN'
access_secret = 'PGKzzTUpm6j5xxVanD0ae4eOgonebnvvIiZSsrx3lugOw'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)


for status in tweepy.Cursor(api.home_timeline).items(10):
    # Process a single status
    print(status.text)


class StreamListener(tweepy.StreamListener):

    def __init__(self):
        super(StreamListener, self).__init__()
        self.num_tweets = 0
        try:
            with open('tweets.json', 'r') as file:
                for line in file:
                    if line != "\n":
                        self.num_tweets += 1
        except:
            pass

    def on_data(self, data):
        try:
            if self.num_tweets < 8000:
                with open('tweets.json', 'a') as file:
                    file.write(data)
                    self.num_tweets += 1
                    print("tweet num: " + str(self.num_tweets))
                    return True
            else:
                print("Number of tweets being analysed: " +
                      str(self.num_tweets) + '\n')
                return False

        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True

    def on_error(self, status_code):
        if status_code == 420:
            # return False and disconnects the stream
            return False


stream = Stream(auth=auth, listener=StreamListener())
stream.filter(track=['#worldCup2018', '#worldcupfinal', 'fracro', 'worldcup'])


# with open('tweets.json', 'r') as f:
#     # read only first tweet
#     line = f.readline()
#     # load as Python dict.
#     tweet = json.loads(line)
#     # pretty print (from dict to String)
#     print(json.dumps(tweet, indent=4))

# Tokenizing Tweet text
emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""

regex_str = [
    emoticons_str,
    r'<[^>]+>',  # HTML tags
    r'(?:@[\w_]+)',  # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",  # hash-tags
    # URLs
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',

    r'(?:(?:\d+,?)+(?:\.?\d+)?)',  # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])",  # words with - and '
    r'(?:[\w_]+)',  # other words
    r'(?:\S)'  # anything else
]

tokens_re = re.compile(r'(' + '|'.join(regex_str) + ')',
                       re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^' + emoticons_str + '$',
                         re.VERBOSE | re.IGNORECASE)


def tokenize(s):
    return tokens_re.findall(s)


def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(
            token) else token.lower() for token in tokens]
    return tokens

# Stop-words filtering
punctuation = list(string.punctuation)
stop_words = stopwords.words('english') + \
    punctuation + ['rt', 'via', 'RT', 'The', '…', '#WorldCup', 'vs']

# Term frequencies
with open('tweets.json', 'r') as f:
    # command line argument as search term argument
    search_term = input("Enter the search term: ")
    terms_counter = Counter()
    bigram_counter = Counter()
    count_search = Counter()

    line_num = 0
    for line in f:
        if line != '\n':  # Empty line in between tweets when stored as JSON file
            tweet = json.loads(line)
            try:
                # Create a list with all the terms
                all_terms = [term for term in preprocess(
                    tweet['text']) if term not in stop_words and not term.startswith(('#', '@'))]
                bigram_terms = bigrams(all_terms)
                # Update counter for the bigrams
                bigram_counter.update(bigram_terms)
                # Update counter for the terms
                terms_counter.update(all_terms)
                # Update counter for the search term
                if search_term in all_terms:
                    count_search.update(all_terms)

                line_num += 1
            except BaseException as e:
                print("Error format for tweet number %f: %s" %
                      ((line_num + 1), str(e)))

    print(terms_counter.most_common(15))
    print(bigram_counter.most_common(15))
    print("Co-occurence for %s:" % search_term)
    print(count_search.most_common(20))

    france_sup_num = dict(count_search.most_common(20))["France"]
    croatia_sup_num = dict(count_search.most_common(20))["Croatia"]
    total_sup_num = france_sup_num + croatia_sup_num
    france_sup_rate = france_sup_num / total_sup_num * 100
    croatia_sup_rate = croatia_sup_num / total_sup_num * 100

    print("France supporters\' rate: %f %%" % round(france_sup_rate, 2))
    print("Croatia supporters\' rate: %f %%" % round(croatia_sup_rate, 2))
