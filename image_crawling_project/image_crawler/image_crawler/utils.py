from http.cookies import SimpleCookie
import os
from datetime import datetime
import requests
from .settings import USER_AGENT_LIST
import random

class UtilsProcess:
   

    # Random User Agent:
    def random_user_agent(self):
        return random.choice(USER_AGENT_LIST)   


    # Parse Cookie For Request
    def cookie_parser(self, cookie_string):

        cookie = SimpleCookie()
        cookie.load(cookie_string)

        cookies = {}
        for key,morsel in cookie.items():
            cookies[key] = morsel.value
        
        print(cookies)
        return cookies
    
    
    
    

utils = UtilsProcess()

