import discord
from discord.ext import commands
from discord.utils import get
import asyncio
from utils import load_token, team_schedule, gen_leaderboard, nfl_map, split_cprint, cprint_df, full_name


class Requests(commands.Cog):

    @commands.command(name="schedule")
    async def schedule(self, message, *args):
        name = " ".join(args)
        await message.channel.send(f"**Schedule for {full_name(name)}**")
        if len(args) > 0:
            schedule = cprint_df(team_schedule(name))
            for chunk in split_cprint(schedule):
                await message.channel.send(chunk)
        else:
            await message.channel.send("**You idjot, plz include a team to query.")
    
    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx, *args):
        max_chunk_size = 1850
        teams = " ".join(args).split("/")
        await ctx.send(f"**Leaderboard**")
        if (len(teams) > 0) and (teams[0] != ''):
            result = cprint_df(gen_leaderboard(name_map=nfl_map, teams=teams))
        else:
            result = cprint_df(gen_leaderboard(name_map=nfl_map, teams=nfl_map.keys()))

        if len(result) < max_chunk_size:
            await ctx.send(result)
        else:
            for chunk in split_cprint(result, max_chunk_size):
                await ctx.send(chunk)


if __name__ == "__main__":
    '''local resource loads'''
    # load bot token
    token = load_token()

    '''bot instantiation'''
    # creates discord bot object (with member intents enabled to grab members)
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(intents=intents, command_prefix='!', case_insensitive=True)
    #add command cogs to bot
    bot.add_cog(Requests())
    #run the bot
    bot.run(token)