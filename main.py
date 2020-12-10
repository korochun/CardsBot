from random import shuffle
from typing import List, Dict, Optional

from discord import Member, Game
from discord.ext.commands import Bot, Context

cards = [suit + str(number // 6 + 1) for number, suit in enumerate("RWLSND" * 12)]


def card_index(card):
    return "DNSLWR".index(card[0]) * 12 + int(card[1:])


class GameObj:
    def __init__(self, players: List[int]):
        self.playernum = len(players)
        self.players = players
        self.hands = {player: [] for player in players}
        self.table = None
        self.deck = cards.copy()
        self.pos = 0
        self.turn = 0
        shuffle(self.players)
        shuffle(self.deck)

    async def deal(self, ctx: Context, player: int, cards: int):
        if cards > 72 - self.pos:
            cards = 72 - self.pos
        self.hands[player] += self.deck[self.pos:self.pos + cards]
        self.pos += cards
        await self.send_hand(ctx, player)

    async def send_hand(self, ctx: Context, player: int):
        member = ctx.guild.get_member(player)
        if member is None:
            member = await ctx.guild.fetch_member(player)
        await member.send("Your hand: " + ", ".join(sorted(self.hands[player], key=card_index)))


bot = Bot(",")
games: Dict[int, GameObj] = {}


@bot.event
async def on_ready():
    await bot.change_presence(activity=Game("Deltanian cards"))


# @bot.event
# async def on_message(message: Message):
#     card = message.content.split()[0].upper()
#     if message.channel.id in games and len(card) in (2, 3) and card[0][0] in ("D", "R", "L", "S", "W", "N") and card[0][1:].isnumeric():
#         game = games[message.channel.id]
#         if game["players"][game["turn"]] != message.author.id:
#             await message.channel.send("It's not your turn!")
#         else:
#             hand = game["hands"][message.author.id]
#             if card in hand:
#                 hand.remove(card)
#                 game["table"].append(card)
#                 game["turn"] = (game["turn"] + 1) % game["nplayers"]
#                 await message.channel.send(card + " was played")
#             else:
#                 await message.channel.send("You don't have that card!")
#     else:
#         await bot.process_commands(message)


def game(func):
    async def wrapper(ctx: Context, *args, **kwargs):
        if ctx.channel.id in games:
            await func(ctx, games[ctx.channel.id], *args, **kwargs)
        else:
            await ctx.send("No game in current channel")
    return wrapper


@bot.command()
async def start(ctx: Context, *players: Member):
    players = [player.id for player in players]
    game = GameObj(players)
    games[ctx.channel.id] = game
    await ctx.send("Turn order: " + ", ".join(f"<@{player}>" for player in game.players))
    for player in players:
        await game.deal(ctx, player, 9)


@bot.command(name="hand")
@game
async def hand(ctx: Context, game: GameObj):
    await game.send_hand(ctx, ctx.author.id)
    await ctx.send("Sent you your hand")


@bot.command(name="undo")
@game
async def undo(ctx: Context, game: GameObj):
    if game.table is None:
        await ctx.send("Nothing to undo")
    else:
        game.turn = (game.turn - 1) % game.playernum
        game.hands[game.players[game.turn]].append(game.table)
        game.table = None
        await ctx.send("Your card was put back into your hand")


@bot.command(name="draw")
@game
async def draw(ctx: Context, game: GameObj):
    if game.players[game.turn] == ctx.author.id:
        await ctx.send(f"{ctx.author.mention} drew 4 cards")
        game.table = None
        game.turn = (game.turn + 1) % game.playernum
        for player in game.players:
            await game.deal(ctx, player, 4 if player == ctx.author.id else 1)
    else:
        await ctx.send("It's not your turn!")


@bot.command(name="play", aliases=["p"])
@game
async def play(ctx: Context, game: GameObj, card: str):
    if game.players[game.turn] != ctx.author.id:
        await ctx.send("It's not your turn!")
    else:
        hand = game.hands[ctx.author.id]
        card = card.upper()
        if card in hand:
            hand.remove(card)
            game.table = card
            await ctx.send(card + " was played")
            if len(hand) == 0:
                await ctx.send(ctx.author.mention + " won!")
                games.pop(ctx.channel.id)
            else:
                game.turn = (game.turn + 1) % game.playernum
        else:
            await ctx.send("You don't have that card!")


@bot.command(name="leave")
@game
async def leave(ctx: Context, game: GameObj, player: Optional[Member]):
    if player is None:
        game.players.remove(ctx.author.id)
        game.hands.pop(ctx.author.id)
        await ctx.send(ctx.author.mention + " left the game")
    else:
        game.players[game.players.index(ctx.author.id)] = player.id
        game.hands[player.id] = game.hands.pop(ctx.author.id)
        await ctx.send(ctx.author.mention + " left the game for " + player.mention)


if __name__ == "__main__":
    bot.run("Nzg1NzQzODkwMzA4NzkyMzIx.X88TBQ.QIgS5uGjEQJPOI28febmk0MvOFM")
