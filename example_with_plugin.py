from arclet.cesloi.bot_client import Cesloi
from arclet.cesloi.communicate_with_mah import BotSession


bot = Cesloi(bot_session=BotSession(host="http://localhost:9080", account=2582049752, verify_key="INITKEYWylsVdbr"), debug=False)
bot.install_plugins("test_plugins")
bot.reload_plugins()
bot.start()
