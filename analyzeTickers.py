import re
import sys
import praw
import operator
import datetime
import yfinance as yf

# to add the path for Python to search for files to use edited version of vaderSentiment
sys.path.insert(0, 'vaderSentiment/vaderSentiment')
from vaderSentiment import SentimentIntensityAnalyzer

blacklist_words = [
      "YOLO", "TOS", "CEO", "CFO", "CTO", "DD", "BTFD", "BTD", "WSB", "OK", "RH",
      "KYS", "FD", "TYS", "US", "USA", "IT", "ATH", "RIP", "BMW", "GDP",
      "OTM", "ATM", "ITM", "IMO", "LOL", "DOJ", "BE", "PR", "PC", "ICE",
      "TYS", "ISIS", "PRAY", "PT", "FBI", "SEC", "GOD", "NOT", "POS", "COD",
      "AYYMD", "FOMO", "TL;DR", "EDIT", "STILL", "LGMA", "WTF", "RAW", "PM",
      "LMAO", "LMFAO", "ROFL", "EZ", "RED", "BEZOS", "TICK", "IS", "DOW"
      "AM", "PM", "LPT", "GOAT", "FL", "CA", "IL", "PDFUA", "MACD", "HQ",
      "OP", "DJIA", "PS", "AH", "TL", "DR", "JAN", "FEB", "JUL", "AUG",
      "SEP", "SEPT", "OCT", "NOV", "DEC", "FDA", "IV", "ER", "IPO", "RISE"
      "IPA", "URL", "BUT", "SSN", "USD", "CPU", "AT", "GG", "ELON", "TO", "THE", "MOON",
      "MEME"
   ]

def extract_ticker(body, start_index):
   """
   Given a starting index and text, this will extract the ticker, return None if it is incorrectly formatted.
   """

   count  = 0
   ticker = ""

   for char in body[start_index:]:
      # if it should return
      if not char.isalpha():
         # if there aren't any letters following the $
         if (count == 0):
            return None

         return ticker.upper()
      else:
         ticker += char
         count += 1

   return ticker.upper()

def parse_section(ticker_dict, body):
   if '$' in body:
      index = body.find('$') + 1
      word = extract_ticker(body, index)
      
      if word and word not in blacklist_words:
         try:
            price = yf.Ticker(word)
            if word in ticker_dict:
               ticker_dict[word].count += 1
               ticker_dict[word].bodies.append(body)
            else:
               ticker_dict[word] = Ticker(word)
               ticker_dict[word].count = 1
               ticker_dict[word].bodies.append(body)
         except:
            pass
   
   # checks for non-$ formatted comments, splits every body into list of words
   word_list = re.sub("[^\w]", " ",  body).split()
   #print(word_list)
   for word in word_list:
      # initial screening of words
      if word.isupper() and len(word) != 1 and (word.upper() not in blacklist_words) and len(word) <= 5 and word.isalpha():
         # sends request to IEX API to determine whether the current word is a valid ticker
         # if it isn't, it'll return an error and therefore continue on to the next word
         price = yf.Ticker(word)

         print(word)
         #print(word + "fail")
         #continue
      
         # add/adjust value of dictionary
         if word in ticker_dict:
            ticker_dict[word].count += 1
            ticker_dict[word].bodies.append(body)
         else:
            ticker_dict[word] = Ticker(word)
            ticker_dict[word].count = 1
            ticker_dict[word].bodies.append(body)

   return ticker_dict

def get_url(key, value, total_count):
   # determine whether to use plural or singular
   mention = ("mentions", "mention") [value == 1]
   if int(value / total_count * 100) == 0:
         perc_mentions = "<1"
   else:
         perc_mentions = int(value / total_count * 100)
   
def final_post(subreddit, text):
   # finding the daily discussino thread to post
   title = str(get_date()) + " | Today's Top 25 Tickers"
   print("\nPosting...")
   print(title)
   subreddit.submit(title, selftext=text)

def get_date():
   now = datetime.datetime.now()
   return now.strftime("%b %d, %Y")

def setup(sub):
   if sub == "":
      sub = "wallstreetbets"

   # create a reddit instance
   reddit = praw.Reddit(user_agent = "Analyzing tickers 1.0 by /u/tickerAnalysis", site_name= "tickerAnalysis")  

   # create an instance of the subreddit
   subreddit = reddit.subreddit(sub)

   return subreddit

def retrieve_comments(submission):
   submissionList = []

   submission.comments.replace_more(limit = 200000)
   for comment in submission.comments.list():
      #print(comment.body)
      submissionList.append(comment.body)

   return submissionList


def run(mode, sub, num_submissions):
   ticker_dict = {}
   text = ""
   
   subreddit = setup(sub)
   hot_posts = subreddit.new(limit= num_submissions)

   
   for count, post in enumerate(hot_posts):
      # if we have not already viewed this post thread
      if not post.clicked:
         # parse the post's title's text
         ticker_dict = parse_section(ticker_dict, post.title)

         comments = retrieve_comments(post)

         for comment in comments:
            ticker_dict = parse_section(ticker_dict, comment)
         
         # update the progress count
         sys.stdout.write("\rProgress: {0} / {1} posts".format(count + 1, num_submissions))
         sys.stdout.flush()

   text = "Amount of Mentions + Their Sentiment Analysis: "
   text += "\n {:20s} | {:20s} | {:20s} | {:20s} | {:20s} \n".format("Ticker", "Mentions", "Bullish (%)", "Neutral (%)", "Bearish (%)")

   total_mentions = 0
   ticker_list = []
   for key in ticker_dict:
      # print(key, ticker_dict[key].count)
      total_mentions += ticker_dict[key].count
      ticker_list.append(ticker_dict[key])

   ticker_list = sorted(ticker_list, key = operator.attrgetter("count"), reverse=True)

   for ticker in ticker_list:
      Ticker.analyze_sentiment(ticker)

   # will break as soon as it hits a ticker with fewer than 5 mentions
   for count, ticker in enumerate(ticker_list):
      if count == 25:
         break
      

      # setting up formatting for table
      text += "\n {:20s} | {:20d} | {:20d} | {:20d} | {:20d}".format(ticker.ticker, ticker.count, ticker.bullish, ticker.bearish, ticker.neutral)

   # post to the subreddit if it is in bot mode (i.e. not testing)
   if mode:
      final_post(subreddit, text)
   else:
      print("\nTest Mode\n\n*************************************************\n")
      print(text)

class Ticker:
   def __init__(self, ticker):
      self.ticker = ticker
      self.count = 0
      self.bodies = []
      self.pos_count = 0
      self.neg_count = 0
      self.bullish = 0
      self.bearish = 0
      self.neutral = 0
      self.sentiment = 0 # 0 is neutral

   def analyze_sentiment(self):
      analyzer = SentimentIntensityAnalyzer()
      neutral_count = 0
      for text in self.bodies:
         sentiment = analyzer.polarity_scores(text)
         if (sentiment["compound"] > .005) or (sentiment["pos"] > abs(sentiment["neg"])):
            self.pos_count += 1
         elif (sentiment["compound"] < -.005) or (abs(sentiment["neg"]) > sentiment["pos"]):
            self.neg_count += 1
         else:
            neutral_count += 1

      self.bullish = int(self.pos_count / len(self.bodies) * 100)
      self.bearish = int(self.neg_count / len(self.bodies) * 100)
      self.neutral = int(neutral_count / len(self.bodies) * 100)

if __name__ == "__main__":
   mode = 0

   # default is 2, these are the 2 stickied threads in subreddits like /r/wallstreetbets, /r/stocks, /r/investing, etc..
   num_submissions = 3

   sub = "wallstreetbets"

   run(mode, sub, num_submissions)