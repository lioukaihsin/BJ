import random
import urllib
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


class Game(db.Model):
  card           = db.ListProperty(int)
  playerHandCard = db.ListProperty(int)
  bankerHandCard = db.ListProperty(int)
  bankerPK       = db.BooleanProperty(default=False)
  gameName       = db.StringProperty()
  chip           = db.IntegerProperty(default=100)
  wantNewGame    = db.BooleanProperty(default=True)
  wantMoreCard   = db.BooleanProperty(default=False)


class MainPage(webapp.RequestHandler):
  def get(self):
    if self.request.get('repeat') == 'True':
      self.response.out.write("The name has been used, please use else name.</br>")
    self.response.out.write("Please enter the name of the game:")
    self.response.out.write("""
      <html>
      <body>
      <form action="/crgn" method="post">
      <input type="text" name="gameName" cols="10">
      <input type="submit" value="Go">
      </form>
      </body>
      </html>
      """)


class checkRepeatedGameName(webapp.RequestHandler):
  def post(self):
    gameName = self.request.get('gameName')
    result = Game.all().filter('gameName',gameName)
    if result.count() > 0:
      self.redirect('/?' + urllib.urlencode({'repeat': True}))
    else:
      self.redirect('/newGame?' + urllib.urlencode({'gameName': gameName}))


class newGame(webapp.RequestHandler):
  def get(self):
    game = Game()
    game.gameName = self.request.get('gameName')
    for i in range(52): game.card.append(i)
    game.put()
    self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))


class bj(webapp.RequestHandler):
  def get(self):
    key = self.request.get('key')
    game = Game.get(key)

    if game.chip > 0 and game.wantMoreCard == True:
      self.response.out.write("Name of the game: " + str(game.gameName))
      self.response.out.write("</br>Now your chips remain $" + str(game.chip))
      self.response.out.write("</br>Your hand cards:")
      self.response.out.write(show(game.playerHandCard))
      (playerBomb, playerPoint) = cal(game.playerHandCard)
      self.response.out.write("</br>total points: " + str(playerPoint))
      if game.bankerPK == True:
        self.response.out.write("</br>Banker's cards are:")
        self.response.out.write(show(game.bankerHandCard))
        (bankerBomb, bankerPoint) = cal(game.bankerHandCard)
        self.response.out.write("</br>Banker's total points: " + str(bankerPoint))
        if bankerBomb or bankerPoint < playerPoint:
          self.response.out.write("</br>You win.")
          game.chip += 10
        else:
          self.response.out.write("</br>You lose.")
          game.chip -= 10
        # reset for a new game
        game.bankerPK = False
        game.wantMoreCard = False
        game.card = []
        for i in range(52): game.card.append(i)
        game.playerHandCard = []
        game.bankerHandCard = []
        game.put()
        self.response.out.write("</br>Want to play again?[y/n]")
        self.response.out.write("""
          <form action="/cardDrawing" method="post">
          """)
        self.response.out.write('<input type="hidden" name="key" value="'+key+'">')
        self.response.out.write("""
          <input type="submit" name="wantNewGame" value="y">
          <input type="submit" name="wantNewGame" value="n">
          </form>
          """)
      else:
        if playerBomb == True:
          self.response.out.write("</br>You bomb!!!")
          game.chip -= 10
          # reset for a new game
          game.wantMoreCard = False
          game.card = []
          for i in range(52): game.card.append(i)
          game.playerHandCard = []
          game.put()
          self.response.out.write("</br>Want to play again?[y/n]")
          self.response.out.write("""
            <form action="/cardDrawing" method="post">
            """)
          self.response.out.write('<input type="hidden" name="key" value="'+key+'">')
          self.response.out.write("""
            <input type="submit" name="wantNewGame" value="y">
            <input type="submit" name="wantNewGame" value="n">
            </form>
            """)
        else:
          self.response.out.write("</br></br>Do you want one more card?")
          self.response.out.write("""
            <form action="/cardDrawing" method="post">
            """)
          self.response.out.write('<input type="hidden" name="key" value="'+key+'">')
          self.response.out.write("""
            <input type="submit" name="wantMoreCard" value="y">
            <input type="submit" name="wantMoreCard" value="n">
            </form>""")
    elif game.chip > 0 and game.wantNewGame == True:
      self.response.out.write("Name of the game: " + str(game.gameName))
      self.response.out.write("</br>Now your chips remain $" + str(game.chip))
      self.response.out.write("</br>Game start?[y/n]")
      self.response.out.write("""
        <form action="/cardDrawing" method="post">
        """)
      self.response.out.write('<input type="hidden" name="key" value="'+key+'">')
      self.response.out.write("""
        <input type="submit" name="wantNewGame" value="y">
        <input type="submit" name="wantNewGame" value="n">
        </form>
        """)
    else:
      self.response.out.write("byebye")
    

class cardDrawing(webapp.RequestHandler):
  def post(self):
    key = self.request.get('key')
    game = Game.get(key)

    if self.request.get('wantNewGame') == 'n':
      game.wantNewGame = False
      game.put()
      self.redirect('/bj?' + urllib.urlencode({'key': game.key()}))
    elif self.request.get('wantMoreCard') == 'n':
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
                                ('/newGame', newGame),
                                ('/cardDrawing', cardDrawing),
                                ('/crgn', checkRepeatedGameName)],
                                debug=True)

def main():
  run_wsgi_app(myApp)

if __name__ == "__main__":
  main()
