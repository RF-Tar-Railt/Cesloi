from cesloi.mini import cesloi

bot = cesloi("a", 123, "b")


@bot.register("GroupMessage")
async def test(app: bot.client, ev: bot.GroupMessage):
    await app.send_group_message(ev.sender.group, "Hello,World")

bot.run()
