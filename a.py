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
  user      = db.UserProperty()
  money     = db.IntegerProperty()
  isPlaying = db.BooleanProperty(default=False)


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
  date = db.DateTimeProperty(auto_now_add=True)
  cardnumber     = db.IntegerProperty(default=-1)
  card_get_5     = db.BooleanProperty(default=False)
  betcoin        = db.IntegerProperty(default=10)
  coinimput        = db.BooleanProperty(default=True)
    

class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    data = Game.all()
    data.order('-date')
    number = data.count()
    show =''
    for p in data:
      show += (" " + (p.gameName))
    show += ("<br> the total play time = " + str(number))
    template_value = {
                      'repeat':self.request.get('repeat'),
                      'logout_url': users.create_logout_url("/"),
                      'login_url': users.create_login_url("/"),
                      'crgn_url': "/bj/crgn",
                      'user': user,
                      'userNickName': user.nickname(),
                      'show':show,
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
      if not userprefs.isPlaying:
        userprefs.isPlaying = True
        userprefs.put()
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
    game.cardnumber = game.cardnumber+1
    
    userprefs = UserPrefs.all().filter('user', users.get_current_user()).get()
    game.chip = userprefs.money
    
    enoughChip = game.chip > 0
    playerWin = False
    (playerBomb, playerPoint) = cal(game.playerHandCard)
    (bankerBomb, bankerPoint) = cal(game.bankerHandCard)
    if playerBomb:
      game.chip -= game.betcoin
      game.gameOver = True
    elif game.cardnumber >= 5:
      game.chip += 2*game.betcoin
      game.gameOver = True
      game.card_get_5 =True
      game.wantMoreCard = False
      
    if game.bankerPK:
      if bankerBomb or bankerPoint < playerPoint :
        playerWin = True
        game.chip += game.betcoin
      else:
        game.chip -= game.betcoin
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
                      'card_get_5':game.card_get_5,
                      'betcoin':game.betcoin,
                      'coinimput':game.coinimput
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
      game.card_get_5 = False
      game.cardnumber = 0
      game.coinimput = True
      game.betcoin = 10
      game.put()
    

class cardDrawing(webapp.RequestHandler):
  def post(self):
    key = self.request.get('key')
    game = db.get(key)
    if self.request.get('addcoin') == '+10':
      game.betcoin += 10
      game.coinimput = True
      game.cardnumber = 0
      game.put()
      self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))
    else :
      game.coinimput = False
      game.put()
    if game.firstGame:
      game.firstGame = False
      game.put()
    if self.request.get('wantNewGame') == 'y':
      game.cardnumber = 0
      game.put()
    if self.request.get('wantNewGame') == 'n':
      game.wantNewGame = False
      user = Users.get_current_user()
      user.isPlaying = False
      user.put()
      game.put()
      self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))
    elif self.request.get('wantMoreCard') == 'nn':
      game.bankerPK = True
      card = game.card
      bankerPoint = 0
      while bankerPoint < playerPoint and (bankerPoint <= 21 or bankerPoint < 17) and bankerCardNum <= 5:
        thisCard = card.pop(card.index(random.choice(card)))
        game.bankerHandCard.append(thisCard)
        (temp, bankerPoint) = cal(game.bankerHandCard)
      game.put()
      self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))
    else:
      if game.coinimput == True:
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
    if   handCard[i] / 13 == 0: output += """<img src="http://www.veryicon.com/icon/png/Object/Las%20Vegas%202/Spade.png" width ="36" height="36"></img>"""
    elif handCard[i] / 13 == 1: output += """ <img src="http://t0.gstatic.com/images?q=tbn:ANd9GcR3tz7Vuqp8r_0EvUT6YxpAAb8xdbsG2BX2zy_hIOYFibts_DLfkp2VyA"width ="36" height="36"></img> """
    elif handCard[i] / 13 == 2: output += """<img src="http://www.wordans.us/wordansfiles/images/2011/4/27/77598/77598_340.jpg?1303937078"width ="36" height="36"></img>"""
    elif handCard[i] / 13 == 3: output += """<img src="http://www.iconpng.com/png/pictograms/club.png"width ="36" height="36"></img>"""
    if (handCard[i] % 13 + 1) ==1:
      output += 'A'
    elif (handCard[i] % 13 + 1) ==11:
      output += 'J'
    elif (handCard[i] % 13 + 1) ==12:
      output += 'Q'
    elif (handCard[i] % 13 + 1) ==13:
      output += 'K'
    else:
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


class onlineUsers(webapp.RequestHandler):
  def get(self):
    userprefs = UserPrefs.all().filter('isPlaying', True)
    playingUsers_list = []
    if userprefs.count() == 1:
      playingUsers = userprefs.get()
      playingUsers_list.append(playingUsers.user.nickname())
    elif userprefs.count > 1:
      playingUsers = userprefs.get()
      for player in playingUsers:
        playingUsers_list.append(player.user.nickname())
    template_value = {
                      'playingUsers_list': playingUsers_list,
                      }
    path = os.path.join(os.path.dirname(__file__), 'onlineUsers.htm')
    self.response.out.write(template.render(path, template_value))
  
  
myApp = webapp.WSGIApplication([('/', MainPage),
                                ('/bj', bj),
                                ('/bj/newGame', newGame),
                                ('/bj/cardDrawing', cardDrawing),
                                ('/bj/crgn', checkRepeatedGameName),
                                ('/bj/onlineUsers', onlineUsers)],
                                debug=True)

def main():
  run_wsgi_app(myApp)

if __name__ == "__main__":
  main()
