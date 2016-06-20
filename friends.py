"""
A simple example script to get all posts on a user's timeline and sort them according to date.
The first few functions are to allow easy acquisition of the access token, then we do the real
work in the using_posts function.

using_posts(1) for old posts, using_posts(2) for somewhat old and using_posts(3) for new posts

"""
import facebook
import requests
import BaseHTTPServer
import urllib2
from webbrowser import open_new
import numpy as np
import dateparser as dp
import datetime as dt

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
app_id = '*Enter your own APP ID*'
app_secret = '*Enter your own APP SECRET*'

# these are commands from the Graph API explorer
photos_likes = '?fields=photos.limit(100){likes.limit(20).order(reverse_chronological)}'
feed_from = '?fields=feed.limit(100){from,created_time}'
posts_from = '?fields=posts.limit(100){from,created_time}'
posts_reactions = '?fields=feed{reactions}'
user_liked_comments = '?fields=posts{comments{user_likes,from}}'

def using_posts(input=1, whose_posts='me'):

    # start with the access token so that we can access the user's data
    auth = TokenHandler(app_id,app_secret)
    access_token = auth.get_access_token()
    
    # get the name and id of the user
    graph = facebook.GraphAPI(access_token)
    name_id = graph.get_object('me')
    my_name = name_id['name']
    my_id = name_id['id']
    
    # get the first page of posts
    
    if whose_posts=='me':
        # whose_posts returns only user's own posts by default
        posts = requests.get('https://graph.facebook.com/v2.6/' + my_id + posts_from + '&access_token=' + access_token).json()
        
    else:
        # alternatively it can return posts from the entire feed
        # including those made by other users. Change the value
        # of whose_posts to any value other than 'me' to do this
        posts = requests.get('https://graph.facebook.com/v2.6/' + my_id + feed_from + '&access_token=' + access_token).json()

    # initialize results arrays
    from_me_old = np.array([None,None])
    from_me_med = np.array([None,None])
    from_me_new = np.array([None,None])
			
	# comment_names = posts['posts']['data'][1]['comments']['data'][0]['from']['id']
    # comment_dates = posts['posts']['data']['comments']['data']['created_time']
    # post_dates = posts['posts']['data']['created_time']
    # print(comment_names)
    
    # this while loop will keep paginating results
    while True:
        try:
        # get each post, created date and id and sort them according to age
            for post in posts['feed']['data']:

                # old posts
                if da.parse(post['created_time']) < dp.parse('2 years ago'):
                    from_me_old = np.vstack((from_me_old,np.array([post['id'], post['created_time']])))
                
                # somewhat old
                elif da.parse(post['created_time']) < dp.parse('1 year ago'):
                    from_me_med = np.vstack((from_me_old,np.array([post['id'], post['created_time']])))
                    
                # recent
                else:
                    from_me_new = np.vstack((from_me_old,np.array([post['id'], post['created_time']])))
            # Attempt to make a request to the next page of data, if it exists.
            posts = requests.get(posts['feed']['paging']['next']).json()
        except KeyError:
        # When there are no more pages (['paging']['next']), break from the
        # loop and end the script.
            break
    if input == 1:
        return from_me_old
    elif input == 2:
        return from_me_med
    elif input == 3:
        return from_me_new
    else:
        print("input either 1, 2 or 3")
        
def using_comments():
    # start with the access token so that we can access the user's data
    auth = TokenHandler(app_id,app_secret)
    access_token = auth.get_access_token()
    
    # get the name and id of the user
    graph = facebook.GraphAPI(access_token)
    name_id = graph.get_object('me')
    my_name = name_id['name']
    my_id = name_id['id']
    
    # get the first page of comments
    posts = requests.get('https://graph.facebook.com/v2.6/' + my_id + user_liked_comments + '&access_token=' + access_token).json()
