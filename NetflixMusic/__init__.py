from NetflixMusic.core.bot import Netflix
from NetflixMusic.core.dir import dirr
from NetflixMusic.core.git import git
from NetflixMusic.core.userbot import Userbot
from NetflixMusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Netflix()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
