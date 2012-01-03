import wsgiref.handlers
import os

from a import UserPrefs
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext.webapp import template


class a1dteu(webapp.RequestHandler):
  def get(self):
    users = UserPrefs.all()
    for user in users:
      user.money += 10
      user.put()


myApp = webapp.WSGIApplication([('/a1dteu', a1dteu)],
                                debug=True)

def main():
  run_wsgi_app(myApp)

if __name__ == "__main__":
  main()
