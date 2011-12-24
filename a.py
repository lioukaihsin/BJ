import random
import urllib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class game(db.Model):
  gameName = db.StringProperty()
  player = db.StringProperty()
  handCard = db.ListProperty(int)
  chip = db.IntegerProperty(default=-1)
  choice = db.BooleanProperty(default=True)


def gameNameKey(gameName=None):
  return db.Key.from_path('bj', gameName or 'default_gameName')


class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write("Do you want to play blackjack?")
    self.response.out.write("""
      <html>
      <body>
      <form action="/newGame" method="post">
      <input type="text" name="gameName" cols="10">
      <input type="submit" value="yes">
      </form>
      </body>
      </html>
      """)

class newGame(webapp.RequestHandler):
  def post(self):
    gamename = self.request.get('gameName')
    aGame = game(parent=gameNameKey(gamename))
    aGame.chip = 100
    aGame.gameName = gamename
    aGame.choice = True
    aGame.put()
    self.redirect('/bj?' + urllib.urlencode({'gameName': gamename}))


class bj(webapp.RequestHandler):
  def get(self):
    gamename = self.request.get('gameName')
    aGame = game(parent=gameNameKey(gamename))

    self.response.out.write("Name of the game: " + str(aGame.gameName))
    
    self.response.out.write("</br>Now your chips remain $" + str(aGame.chip))
    self.response.out.write("</br>Want to play again?[y/n]")

#    aGame = db.GqlQuery("SELECT * FROM game", gameNameKey(gameName))
    

    if aGame.chip > 0 and aGame.choice == 'y':
      self.response.out.write("</br>Now your chips remain $" + str(aGame.chip))
      self.response.out.write("</br>Want to play again?[y/n]")
      self.response.out.write("""
        <form action="/test" method="post">
        <input type="submit" name="choice1" value="y">
        <input type="submit" name="choice1" value="n">
        </form>
        """)
    

  def gaming():    
    
    # Create the original card set
    card = []
    for i in range(52):
      card.append(i)
    
    playerCard = []
    oneMoreCard = 'y'
    while oneMoreCard is 'y':
      thisCard = card.pop(card.index(random.choice(card)))
      playerCard.append(thisCard)
      (bomb, point) = cal(playerCard)
      show(playerCard)
      print "total points: " + str(point)
      if bomb:
        print "You lose."
        chip[0] -= 10
        return
      print "Do you want to have one more card?[y/n]"
      oneMoreCard = raw_input()
    
    bankerHandCard = []
    bankerPoint = 0
    while bankerPoint < 18:
      thisCard = card.pop(card.index(random.choice(card)))
      bankerHandCard.append(thisCard)
      (bomb, bankerPoint) = cal(bankerHandCard)
    print "Banker's cards are:",
    show(bankerHandCard)
    print "Banker's total points: " + str(bankerPoint)
    if bomb or bankerPoint < point:
      print "You win."
      chip[0] += 10
    else:
      print "You lose."
      chip[0] -= 10
  
    
  #  for i in range(52):
  #    thisCard = newCardSet.pop(newCardSet.index(random.choice(newCardSet)))
  #    print chr(3+thisCard/13)+str(thisCard%13+1)
  
  
class judge(webapp.RequestHandler):  
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
  
  
  def show(handCard):
    for i in range(len(handCard)): 
      if   handCard[i] / 13 == 0: print """
      <img src="http://www.writerscafe.org/uploads/stories/03225200-1233894394.jpg"></img>
      """ +str(i%13) ,
      elif handCard[i] / 13 == 1: print """
          <img src="http://heartoftheschool.edublogs.org/files/2010/09/beating_heart.gif"></img>
          """ +str(i%13),
      elif handCard[i] / 13 == 2: print """
          <img src="http://www.wordans.us/wordansfiles/images/2011/4/27/77598/77598_340.jpg?1303937078"></img>
          """ +str(i%13),
      elif handCard[i] / 13 == 3: print """
          <img src="http://www.writerscafe.org/uploads/stories/03225200-1233894394.jpg"></img>
          """ +str(i%13) ,
    print
  


myApp = webapp.WSGIApplication([('/', MainPage),
                                ('/bj', bj),
                                ('/newGame', newGame)],
                                debug=True)

def main():
  run_wsgi_app(myApp)

if __name__ == "__main__":
  main()
