import random
import urllib
import wsgiref.handlers
import os

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext.webapp import template

class UserPrefs(db.Model):
  user = db.UserProperty()
  money = db.IntegerProperty()

class Game(db.Model):
  card           = db.ListProperty(int)
  playerHandCard = db.ListProperty(int)
  bankerHandCard = db.ListProperty(int)
  bankerPK       = db.BooleanProperty(default=False)
  gameName       = db.StringProperty()
  chip           = db.IntegerProperty(default=100)
  firstGame      = db.BooleanProperty(default=True)
  gameOver       = db.BooleanProperty(default=False)
  wantNewGame    = db.BooleanProperty(default=False)
  wantMoreCard   = db.BooleanProperty(default=False)


class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    template_value = {
                      'repeat':self.request.get('repeat'),
                      'logout_url': users.create_logout_url("/"),
                      'login_url': users.create_login_url("/"),
                      'crgn_url': "/bj/crgn",
                      'user': user,
                      'userNickName': user.nickname(),
                      }
    path = os.path.join(os.path.dirname(__file__), 'index.htm')
    self.response.out.write(template.render(path, template_value))


class checkRepeatedGameName(webapp.RequestHandler):
  def post(self):
    gameName = self.request.get('gameName')
    result = Game.all().filter('gameName',gameName)
    if result.count() > 0:
      self.redirect('/?' + urllib.urlencode({'repeat': True}))
    else:
      self.redirect('/bj/newGame?' + urllib.urlencode({'gameName': gameName}))


class newGame(webapp.RequestHandler):
  def get(self):
    game = Game()
    game.gameName = self.request.get('gameName')
    for i in range(52): game.card.append(i)
    user = users.get_current_user()
    userprefs = UserPrefs.all().filter('user', user).get()
    if userprefs:
      game.chip = userprefs.money
    else:
      userprefs = UserPrefs()
      userprefs.user = user
      userprefs.money = 100
      userprefs.put()
    game.put()
    self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))


class bj(webapp.RequestHandler):
  def get(self):
    key = self.request.get('key')
    game = db.get(key)
    
    userprefs = UserPrefs.all().filter('user', users.get_current_user()).get()
    game.chip = userprefs.money
    
    enoughChip = game.chip > 0
    playerWin = False
    (playerBomb, playerPoint) = cal(game.playerHandCard)
    (bankerBomb, bankerPoint) = cal(game.bankerHandCard)
    if playerBomb:
      game.chip -= 10
      game.gameOver = True
    if game.bankerPK:
      if bankerBomb or bankerPoint < playerPoint:
        playerWin = True
        game.chip += 10
      else:
        game.chip -= 10
      game.gameOver = True
    game.put()
    userprefs.money = game.chip
    userprefs.put()
    template_value = {
                      'gameName': game.gameName,
                      'key': key,
                      'cardDrawing_url': "/bj/cardDrawing",
                      'bj_url': "/bj",
                      'chip': game.chip,
                      'enoughChip': enoughChip,
                      'bankerPK': game.bankerPK,
                      'wantMoreCard': game.wantMoreCard,
                      'wantNewGame': game.wantNewGame,
                      'firstGame': game.firstGame,
                      'gameOver': game.gameOver,
                      'playerHandCard': show(game.playerHandCard),
                      'playerBomb': playerBomb,
                      'playerPoint': playerPoint,
                      'bankerHandCard': show(game.bankerHandCard),
                      'bankerBomb': bankerBomb,
                      'bankerPoint': bankerPoint,
                      'playerWin': playerWin,
                      }
    path = os.path.join(os.path.dirname(__file__), 'bj.htm')
    self.response.out.write(template.render(path, template_value))
    if game.gameOver:
      # reset for a new game
      game.gameOver = False
      game.bankerPK = False
      game.wantMoreCard = False
      game.card = []
      for i in range(52): game.card.append(i)
      game.playerHandCard = []
      game.bankerHandCard = []
      game.put()
    

class cardDrawing(webapp.RequestHandler):
  def post(self):
    key = self.request.get('key')
    game = db.get(key)
    
    if game.firstGame:
      game.firstGame = False
      game.put()
    if self.request.get('wantNewGame') == 'n':
      game.wantNewGame = False
      game.put()
      self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))
    elif self.request.get('wantMoreCard') == 'nn':
      game.bankerPK = True
      card = game.card
      bankerPoint = 0
      while bankerPoint < 18:
        thisCard = card.pop(card.index(random.choice(card)))
        game.bankerHandCard.append(thisCard)
        (temp, bankerPoint) = cal(game.bankerHandCard)
      game.put()
      self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))
    else:
      card = game.card
      thisCard = card.pop(card.index(random.choice(card)))
      game.playerHandCard.append(thisCard)
      game.wantMoreCard = True
      game.put()
      self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))


# to show one's hand card
#return handcard_string
def show(handCard):
  output = ''
  for i in range(len(handCard)): 
    if   handCard[i] / 13 == 0: output += " s "
    elif handCard[i] / 13 == 1: output += " h "
    elif handCard[i] / 13 == 2: output += " d "
    elif handCard[i] / 13 == 3: output += " c "
    output += str(handCard[i] % 13 + 1)
  return output

  
# to calculate the pts of handcard and whether it bombs or not
# return (bomb_or_not,point)
def cal(handCard):
  handCardCopy = handCard[:]
  point = 0
  while len(handCardCopy) > 0:
    temp = handCardCopy.pop()%13+1
    if temp < 11:
      point += temp
    else:
      point += 10
      
    if point > 21:
      return (True, point)
  return (False, point)
  
  
myApp = webapp.WSGIApplication([('/', MainPage),
                                ('/bj', bj),
                                ('/bj/newGame', newGame),
                                ('/bj/cardDrawing', cardDrawing),
                                ('/bj/crgn', checkRepeatedGameName)],
                                debug=True)

def main():
  run_wsgi_app(myApp)

if __name__ == "__main__":
  main()
