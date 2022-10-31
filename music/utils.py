INVALID_URL_ERROR_MESSAGE = "Invalid URL"


async def _send_error_msg(ctx):
    ctx.channel.send(INVALID_URL_ERROR_MESSAGE)


async def _send_big_message(ctx, response):
    message = response
    for i in range(len(message) // 2000):
        await ctx.channel.send(message[:2000])
        message = message[2000:]
    await ctx.channel.send(message)
