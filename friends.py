"""
A simple example script to get all posts on a user's timeline and sort them according to date.
The first few functions are to allow easy acquisition of the access token, they contain a web server 
and a TokenHandler class to accept the token from Facebook.

using_posts(1) for old posts, using_posts(2) for somewhat old and using_posts(3) for new posts
The second argument in using_posts controls filtering the posts by author, using any value 
except 'me' will output posts from all users that appear in the timeline.
The third argument controls dating posts from the earliest comment instead of the created_time
of the post.

posts_in_range will get posts from between 2 dates, the first argument is the start date and
the second argument is the end date. Date format is 'yyyy-mm-dd'. Third argument is the same as
second argument in using_posts

comments_from_post gives you comments from a post based on the post ID which can be filtered
for certain attributes.

comment_counter takes array of post ids and counts number of comments in each.

comment_hist produces histogram of comments per post, can be used to get histograms
of using_posts outputs by using same arguments.
"""
import facebook
import requests
import BaseHTTPServer
import urllib2
from webbrowser import open_new
import numpy as np
import dateparser as dp
import datetime as dt
import matplotlib.pyplot as plt

# REDIRECT_URL = 'http://localhost:8080/'
# I've modified my HOSTS file to redirect this domain to localhost:8080
REDIRECT_URL = 'http://this.is.a.real.domain/'
PORT = 8080

def get_access_token_from_url(url):
    """
    Parse the access token from Facebook's response
    Args:
        uri: the facebook graph api oauth URI containing valid client_id,
             redirect_uri, client_secret, and auth_code arguements
    Returns:
        a string containing the access key 
    """
	
    token = requests.get(url).json()
    
    return token['access_token']

class HTTPServerHandler(BaseHTTPServer.BaseHTTPRequestHandler,object):

    """
    HTTP Server callbacks to handle Facebook OAuth redirects
    """
    def __init__(self, request, address, server, a_id, a_secret):
        self.app_id = a_id
        self.app_secret = a_secret
        super(HTTPServerHandler, self).__init__(request, address, server)

    def do_GET(self):
        GRAPH_API_AUTH_URI = ('https://graph.facebook.com/v2.6/oauth/' 
            + 'access_token?client_id=' + self.app_id + '&redirect_uri=' 
            + REDIRECT_URL + '&client_secret=' + self.app_secret + '&code=')
        # GRAPH_API_AUTH_URI
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        if 'code' in self.path:
            self.auth_code = self.path.split('=')[1]
            self.wfile.write(bytes('<html><h1>You may now close this window.'
                              + '</h1></html>'))
            self.server.access_token = get_access_token_from_url(
                    GRAPH_API_AUTH_URI + self.auth_code)

    # Disable logging from the HTTP Server
    def log_message(self, format, *args):
        return

class TokenHandler:
    """
    Functions used to handle Facebook oAuth
    """
    def __init__(self, a_id, a_secret):
        self._id = a_id
        self._secret = a_secret

    def get_access_token(self):
        """
         Fetches the access key using an HTTP server to handle oAuth
         requests
            Args:
                appId:      The Facebook assigned App ID
                appSecret:  The Facebook assigned App Secret
        """

        ACCESS_URI = ('https://www.facebook.com/dialog/' 
            + 'oauth?client_id=' +self._id + '&redirect_uri='
            + REDIRECT_URL + "&scope=public_profile,user_friends,user_posts")

        open_new(ACCESS_URI)
        httpServer = BaseHTTPServer.HTTPServer(
                ('127.0.0.1', 8080),
                lambda request, address, server: HTTPServerHandler(
                    request, address, server, self._id, self._secret))
        httpServer.handle_request()
        return httpServer.access_token 

def some_action(friend):
    """ Here you might want to do something with each post. E.g. grab the
    post's message (post['message']) or the post's picture (post['picture']).
    In this implementation we just print the post's created time.
    """
    print(friend['first_name']) 

# these parameters come from the facebook app
# the app secret should be stored elsewhere on a final build
app_id = '**input your app ID here**'
app_secret = '**input your app secret here**'

# start with the access token so that we can access the user's data
auth = TokenHandler(app_id,app_secret)
access_token = auth.get_access_token()
    
# get the name and id of the user
graph = facebook.GraphAPI(access_token)
name_id = graph.get_object('me')
my_name = name_id['name']
my_id = name_id['id']

# these are commands from the Graph API explorer
# facebook limits output of post queries to 100 results
likes_limit = '1000'
photos_likes = '?fields=photos.limit(100){likes.limit(' + likes_limit + ').order(reverse_chronological)}'
feed_from = '?fields=feed.limit(100){from,created_time,comments{user_likes.limit(' + likes_limit + '),from,created_time},type}'
posts_from = '?fields=posts.limit(100){from,created_time,comments{user_likes.limit(' + likes_limit + '),from,created_time},type}'

feed_from_dates = '?fields=feed.limit(100){from,created_time,comments{user_likes.limit(' + likes_limit + '),from,created_time},type}'
posts_from_dates = '?fields=posts.limit(100){from,created_time,comments{user_likes.limit(' + likes_limit + '),from,created_time},type}'

posts_reactions = '?fields=feed{reactions}'
user_liked_comments = '?fields=posts{comments{user_likes.limit(' + likes_limit + '),from}}'

# graph API syntax, breakdown of the GET request:
# 'https://graph.facebook.com/v2.6/'  + my_id                   + ?fields=photos                             + '&access_token=' + access_token
# access graph and specify version    + id of user/post/comment + query for certain connections/attributes   + specify access token

def posts_in_range(since, until, whose_posts = 'me'):
    # input the since and until dates in the form 'yyyy-mm-dd'
    if whose_posts=='me':
        # whose_posts variable set to return only user's own posts by default
        posts = requests.get('https://graph.facebook.com/v2.6/' + my_id + \
        '?fields=posts.limit(100).since(' + since + ').until(' + until + \
        '){from,created_time,comments{user_likes.limit(' + likes_limit + \
        '),from,created_time},type}' + '&access_token=' + access_token).json()
        
        # specify 'posts' for user's own posts
        f_or_p = 'posts'
        
    else:
        # alternatively it can return posts from the entire feed
        # including those made by other users. Change the value
        # of whose_posts to any value other than 'me' to do this
        posts = requests.get('https://graph.facebook.com/v2.6/' + my_id + \
        '?fields=feed.limit(100).since(' + since + ').until(' + until + \
        '){from,created_time,comments{user_likes.limit(' + likes_limit + \
        '),from,created_time},type}' + '&access_token=' + access_token).json()
        
        # specify 'feed' to return all posts in the timeline
        f_or_p = 'feed'
        
    posts_out = np.array(['ID', 'Date','Type'])
        # this while loop will keep paginating results
    while True:
        
        # except statement will catch the KeyError when there are no more pages
        try:
        
        # get each post, created date and id and sort them according to age
            for post in posts[f_or_p]['data']:
                posts_out = np.vstack((posts_out,np.array([post['id'], post['created_time'], post['type']])))

            # Attempt to make a request to the next page of data, if it exists.
            posts = requests.get(posts[f_or_p]['paging']['next']).json()

        except KeyError:

        # When there are no more pages (['paging']['next']), break from the
        # loop and end the script.
            break
    return posts_out
    
def using_posts(input = 1, whose_posts = 'me', comment_or_created = 'created'):
    
    # get the first page of posts
    
    if whose_posts=='me':
        # whose_posts variable set to return only user's own posts by default
        posts = requests.get('https://graph.facebook.com/v2.6/' + my_id + posts_from + '&access_token=' + access_token).json()
        
        # specify 'posts' for user's own posts
        f_or_p = 'posts'
        
    else:
        # alternatively it can return posts from the entire feed
        # including those made by other users. Change the value
        # of whose_posts to any value other than 'me' to do this
        posts = requests.get('https://graph.facebook.com/v2.6/' + my_id + feed_from + '&access_token=' + access_token).json()
        
        # specify 'feed' to return all posts in the timeline
        f_or_p = 'feed'

    # initialize results arrays
    output_old = np.array(['ID', 'Date','Type'])
    output_med = np.array(['ID', 'Date','Type'])
    output_new = np.array(['ID', 'Date','Type'])
    
    # this while loop will keep paginating results
    while True:
        
        # except statement will catch the KeyError when there are no more pages
        try:
        
        # get each post, created date and id and sort them according to age
            for post in posts[f_or_p]['data']:
                # choose the sorting method, it will either use
                # the created_time of the post or the most recent
                # user-liked comment
                if comment_or_created == 'created':
                    # using the post created_time
                    checkdate = dp.parse(post['created_time'])
                else:
                    try:
                        # using the first liked comment, facebook automatically outputs
                        # comments in chronological order so this is also the most recent
                        # comment
                        liked = post['comments']['data'][0]['user_likes']
                        
                        # initialize as the date of the first comment
                        checkdate = dp.parse(post['comments']['data'][0]['created_time'])
                        n = 0
                        
                        # if the first comment is liked this loop is not entered, if the loop
                        # is entered then it breaks at the first user-liked comment
                        while not liked:
                            
                            n += 1
                            
                            # check next comment to see if it is liked
                            liked = post['comments']['data'][n]['user_likes']
                            checkdate = dp.parse(post['comments']['data'][n]['created_time'])
                            
                    # when there are no more comments then an IndexError is thrown
                    except IndexError:
                    
                        # if there are no liked comments use date of most recent comment
                        checkdate = dp.parse(post['comments']['data'][0]['created_time'])
                        
                    # if there are no comments on the post then a KeyError is thrown
                    except KeyError:
                    
                        # if there are no comments then use the created_time of the post
                        checkdate = dp.parse(post['created_time'])

                # old posts
                if checkdate < dp.parse('2 years ago'):
                    output_old = np.vstack((output_old,np.array([post['id'], post['created_time'], post['type']])))
                
                # somewhat old
                elif checkdate < dp.parse('1 year ago'):
                    output_med = np.vstack((output_old, np.array([post['id'], post['created_time'], post['type']])))
                    
                # recent
                else:
                    output_new = np.vstack((output_old, np.array([post['id'], post['created_time'], post['type']])))

            # Attempt to make a request to the next page of data, if it exists.
            posts = requests.get(posts[f_or_p]['paging']['next']).json()

        except KeyError:

        # When there are no more pages (['paging']['next']), break from the
        # loop and end the script.
            break
    if input == 1:
        return output_old
    elif input == 2:
        return output_med
    elif input == 3:
        return output_new
    else:
        print("input either 1, 2 or 3")

def comments_from_post(id, filter_user_liked = False, date_cutoff = dt.timedelta(weeks = 300)):
    """
    The only required variable is the Post ID (id), the rest are filters for the comments with 
    various default values.
    
    filter_user_liked : False means no filter, True means it will only return comments that the
    user has liked
    
    date_cutoff: datetime.timedelta variable that is by default to 300 weeks, it is the allowed 
    time between the creation of the post and the comment. I.e. the maximum allowed time 
    difference between the post created_time and the comment created_time. Only comments made
    within this time difference are returned.
    """
    # get comments from the graph
    comments = graph.get_connections(id, 'comments?fields=user_likes,message,created_time')
    
    # get the created_time of the post
    post_date = graph.get_connections(id, '?fields=created_time')
    
    # initalize output
    comments_out = [None]
    
    # if date cutoff is of a string type parse it before use
    if type(date_cutoff) == type('string'):
        date_cutoff = dt.datetime.today - dp.parse(date_cutoff)
    
    while True:
        try:
            for comment in comments['data']:
                # filter by likes if required
                if filter_user_liked and (not comment['user_likes']):
                    continue
                
                # filter by date if requried
                if (dp.parse(comment['created_time']) - dp.parse(post_date['created_time'])) < date_cutoff:
                    comments_out.append(comment['message'])
            # access next page of comments if possible        
            comments = requests.get(comments['paging']['next'])
        except KeyError:
            # else break
            break
    return comments_out
    
def comment_counter(ids):
    # takes array of post ids and counts number of comments in each
    summary = [None]
    for inp in ids:
        # this is a try statement because if the post was not made by the current user
        # they will often not have permission to access the comments data
        try:
            sum = requests.get('https://graph.facebook.com/v2.6/' + inp + '?fields=comments.summary(true)' + '&access_token=' + access_token ).json()
            summary.append(sum['comments']['summary']['total_count'])
        except Exception:
            # if they dont have permission just skip the post
            continue
    return summary

def comment_hist(inpt = 1, from_who = 'me', com_or_created = 'created', show = True):
    # this function takes the same arguments as using_posts
    # and can be used to make histograms of the comments of that data
    # if only a count of the total number of comments is required then 
    # the graph output can be suppressed by setting the last argument to false
    posts = using_posts(inpt, from_who, com_or_created)
    c = comment_counter(posts[ 1: , 0])

    while True:
        # extract None values from array
        try:
            c.remove(None)
        except Exception:
            break
    
    if show:
        plt.hist(c,bins = 7)
        plt.xlabel('Number of Comments')
        plt.ylabel('Frequency')
        plt.show()
        
    return np.sum(c)