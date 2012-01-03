import random
import urllib
import wsgiref.handlers
import os

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext.webapp import template


class MainPage(webapp.RequestHandler):
  def get(self):
    template_value = {
                      }
    path = os.path.join(os.path.dirname(__file__), 'index.htm')
    self.response.out.write(template.render(path, template_value))


class guide(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    template_value = {
                      'logout_orl': users.create_logout_url("/createGame"),
                      'login_url': users.create_login_url("/createGame"),
                      'user': user,
                      'userNickName': user.nickname()
                      }
    path = os.path.join(os.path.dirname(__file__), 'guide.htm')
    self.response.out.write(template.render(path, template_value))


class welcome(webapp.RequestHandler):
  def get(self):
    template_value = {
                      }
    path = os.path.join(os.path.dirname(__file__), 'welcome.htm')
    self.response.out.write(template.render(path, template_value))


myApp = webapp.WSGIApplication([('/', MainPage),
                                ('/guide', guide),
                                ('/welcome', welcome)],
                                debug=True)

def main():
  run_wsgi_app(myApp)

if __name__ == "__main__":
  main()
