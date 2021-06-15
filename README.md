# StockTickerAnalysis
Analyze how often stock tickers are mentioned on stock-related discussion reddit subreddits using PRAW api and analyze sentiment of those comments using vaderSentiment

Previously a reddit bot but now back-end for a web app.

# Raw Output
![sample](https://i.imgur.com/yyFuiwo.png)

An example of the program running. Note that it sometimes takes an hour+ for the program to run, this is due to the PRAW api and a limitation with the reddit API of loading more and more comments results in more constraint/lag and some discussion threads range between 15,000 comments and sometimes upto 100,000 comments in a single thread depending on what's occuring in the stock market (usually higher volatility means higher comment voluume).
