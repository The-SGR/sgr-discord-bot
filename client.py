from discord.interactions import Interaction # type: ignore # type: ignore
import disnake # type: ignore
from disnake.ext import commands # type: ignore
from asyncio import sleep
from conf import settings
from typing import Optional
import datetime
import sqlite3
import base64

bot_version = "2.1.04102024"

#Databases (Options)
db1 = sqlite3.connect('whitelist.db')
cr1 = db1.cursor()

cr1.execute('''CREATE TABLE IF NOT EXISTS ids (
    id INT       
)''')
db1.commit()

warn = sqlite3.connect('warns.db')
cr2 = warn.cursor()

cr2.execute('''CREATE TABLE IF NOT EXISTS warns (
    id INT,
    name TEXT,
    warn INT
)''')

warn.commit()
print('[!] Databases are ready.')

prfx = '!'

intents = disnake.Intents().all()
bot = commands.Bot(sync_commands_debug=True, command_prefix=prfx, intents=disnake.Intents.all())

bot.remove_command('help')
err403 = disnake.Embed(title='<:CANCEL:1289669671305482281> Ошибка 403', description='Доступ запрещён', color=0xff0000)

########
#Events#
########

@bot.event
async def on_ready():
  print("[!] Bot is ready to work.")
  print(f"[!] Bot version: {bot_version}")
  await bot.change_presence(status = disnake.Status.idle, activity = disnake.Activity(name = f'the.sgr', type = disnake.ActivityType.listening))

  for guild in bot.guilds:
    for member in guild.members:
        if cr2.execute(f"SELECT id FROM warns WHERE id = {member.id}").fetchone is None:
            cr2.execute(f"INSERT INTO warns VALUES (?, ?, ?)", [{member.id}, "{member}", 0])
            warn.commit()
        else:
            pass

@bot.event
async def on_member_join(member):
    if cr2.execute(f"SELECT id FROM warns WHERE id = {member.id}").fetchone is None:
        cr2.execute(f"INSERT INTO warns VALUES (?, ?, ?)", [{member.id}, "{member}", 0])
        warn.commit()
    else:
        pass


@bot.event
async def on_command_error(ctx, error):
    pass

#################
#Unique Commands#
#################

#Warns (Databases too)
@bot.slash_command(guild_ids=[1285607338539225110])
@commands.has_permissions(mute_members=True)
async def warn(ctx, *, member: disnake.Member, reason: str, action:str=commands.Param(choices=['add', 'remove'])):
    """
    Gives a warn to the user. {{ WARN }}
    """
    if action == 'add':
        cr2.execute("UPDATE warn SET warn = warn + {} WHERE id = {}".format(1, member.id))
        reason=reason + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
        await ctx.send(f'участнику {member.mention} выдано предупреждение. Причина: {reason}')
        await member.send(f'вы получили предупреждение на сервере {ctx.guild}. Причина: {reason}')
        warn.commit()
    else:
        cr2.execute("UPDATE warn SET warn = warn - {} WHERE id = {}".format(1, member.id))
        reason=reason + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
        await ctx.send(f'с участника {member.mention} снято предупреждение. Причина: {reason}')
        await member.send (f'с вас снято предупреждние на сервере {ctx.guild}.\nМодератор: {ctx.author.mention}.')
        warn.commit()

@bot.slash_command(guild_ids=[1285607338539225110])
async def warns(ctx, *, member: disnake.Member = None):
    """
    Sends information about your (or not your) warns. {{ WARNS }}
    """
    if member is None:
        result = cr2.execute("SELECT warn FROM warnsdb WHERE id = ?", (ctx.author.id,)).fetchone()
        if result is None:
            await ctx.send('You have no warns.')
        else:
            await ctx.send(f'You have {result[0]} warns.')
    else:
        result = cr2.execute("SELECT warn FROM warnsdb WHERE id = ?", (member.id,)).fetchone()
        if result is None:
            await ctx.send(f'{member.mention} has no warns.')
        else:
            await ctx.send(f'{member.mention} has {result[0]} warns.')

#Databases
@bot.slash_command(guild_ids=[1285607338539225110], description='only sgr can use this command.')
async def add_whitelist(ctx, id: str):
    if ctx.author.id == 1037358401946128476:
        user_id = id
        try:
            id = int(id)
            cr1.execute('INSERT OR IGNORE INTO ids (id) VALUES (?)', [user_id])
            db1.commit()
            await ctx.send(f'**Пользователь** <@{id}> **добавлен в белый список!**')
        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
    else:
        await ctx.send(embed=err403)

@bot.slash_command(guild_ids=[1285607338539225110], description='only sgr can use this command.')
async def whitelist_list(ctx):
    if ctx.author.id == 1037358401946128476:
        cr1.execute('SELECT * FROM ids')
        users = cr1.fetchall()
        user_ids = ', '.join(str(user[0]) for user in users)
        await ctx.send(f'**Список пользователей в белом списке**: {user_ids}')
    else:
        await ctx.send(embed=err403)

@bot.slash_command(guild_ids=[1285607338539225110], description='only sgr can use this command.')
async def remove_user(ctx, id: str):
    if ctx.author.id == 1037358401946128476:
        id = int(id)
        cr1.execute('DELETE FROM ids WHERE id = ?', (id,))
        db1.commit()
    
        if cr1.rowcount > 0:
            await ctx.send(f'**Пользователь с ID** *{id} (<@{id}>)* **был удален из белого списка.**')
        else:
            await ctx.send(f'**Пользователь не найден в базе данных.**')
    else:
        await ctx.send(embed=err403)

#AI
@bot.slash_command(guild_ids=[1285607338539225110]) #TODO: Make this works
async def ai(ctx, question: str):
    ctx.send("In development since 16.09.2024 0:56 MSK!")

################
#Other Commands#
################

#eval
@bot.command()
async def eval(ctx, *, code):
    user_id = ctx.author.id
    cr1.execute('SELECT * FROM ids WHERE id = ?', (user_id,))
    success = cr1.fetchone()

    if success is not None:
       try:
           exec(code)
           await ctx.send(f'**✅ Команда выполнена!**\n*Отправитель: {ctx.author}.*')
       except Exception as e:
           await ctx.send(f'**Ошибка:**\n```{e}```')
           print(f"Ошибка eval: {e}, отправитель: {ctx.author}")
    else:
        await ctx.send(embed=err403)

#base64
@bot.slash_command() #TODO: Translate choices
async def b64(ctx, type: str = commands.Param(choices=["encode", "decode"]), *, value: str):
    """
    Encode/Decode your text in base64 {{ BASE64 }}

    Parameters
    ----------
    type: encode or decode? {{ TYPECODE }}
    value: value {{ CODEVALUE }}
    """
    if type == "encode":
        if value is None:
            try:
                value=None
            except Exception as e:
                await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
                print(f"Ошибка: {e}, отправитель: {ctx.author}")
        else:
            value=base64.b64encode(value.encode('utf-8')).decode('utf-8')
            emb=disnake.Embed(title="Зашифрованный текст", description=f"{value}", color=0x0297fa)
            await ctx.send(embed=emb)
    elif type == "decode":
        if value is None:
            try:
                value=None
            except Exception as e:
                await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
                print(f"Ошибка: {e}, отправитель: {ctx.author}")
        else:
            value=base64.b64decode(value.encode('utf-8')).decode('utf-8')
            emb=disnake.Embed(title="Дешифрованный текст", description=f"{value}", color=0x0297fa)
            await ctx.send(embed=emb)

#binary
@bot.slash_command() #TODO: Translate choices
async def binary(ctx, type: str = commands.Param(choices=["encode", "decode"]), *, value: str):
    """
    Encode/Decode your text in binary code {{ BINARY }}

    Parameters
    ----------
    type: encode or decode? {{ TYPECODE }}
    value: value {{ CODEVALUE }}
    """
    if type == "encode":
        if value is None:
            try:
                value=None
            except Exception as e:
                await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
                print(f"Ошибка: {e}, отправитель: {ctx.author}")
        else:
            value=' '.join(format(ord(char), '08b') for char in value)
            emb=disnake.Embed(title="Зашифрованный текст", description=f"{value}", color=0x0297fa)
            await ctx.send(embed=emb)
    elif type == "decode":
        if value is None:
            try:
                value=None
            except Exception as e:
                await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
                print(f"Ошибка: {e}, отправитель: {ctx.author}")
        else:
            value=''.join(chr(int(binary, 2)) for binary in value.split())
            emb=disnake.Embed(title="Дешифрованный текст", description=f"{value}", color=0x0297fa)
            await ctx.send(embed=emb)

#bot server list
@bot.slash_command(guild_ids=[1285607338539225110])
async def bot_server_list(ctx):
    user_id = ctx.author.id
    cr1.execute('SELECT * FROM ids WHERE id = ?', (user_id,))
    success = cr1.fetchone()

    if success is not None:
        server_dict = {}
        total_members = 0
        for guild in bot.guilds:
            server_dict[guild.name] = guild.member_count
            total_members += guild.member_count
        server_list = [f"- {name} ({members} members)" for name, members in server_dict.items()]
        total_servers = len(server_dict)
        embed = disnake.Embed(
            title=f"Server List ({total_servers} servers, {total_members} members):",
            description="\n".join(server_list),
            color=0x0097fa
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(embed=err403)

#say
@bot.slash_command()
async def say(ctx, *, message: str):
    """
    Bot says your message {{ SAY }}
    Parameters
    ----------
    message: enter the message {{ MSG }}
    """
    await ctx.send("**Отправлено!**", ephemeral=True, delete_after=10)
    this_channel = ctx.channel.id 
    channel = bot.get_channel(int(this_channel))
    await channel.send(message)
    print(f'{ctx.author} воспользовался командой say. Введённое сообщение:\n{message}')

#help (useless)
@bot.slash_command()
async def help(ctx):
    """
    Help with commands {{ HELP }}
    """
    author = ctx.author
    help = disnake.Embed(title='Помощь', color=0x0297fa, description='''
    *Все слэш-команды будут показаны при вводе "/".*\n
    !eval - прописать собственный код в бота [ОГРАНИЧЕНО].
    
    *Ниже отправил сервер бота для поддержки и так далее.*
    ''')
    help.set_author(name=ctx.author, icon_url=author.avatar)
    help.set_footer(text=f'Made for people. By SGR. Bot version: {bot_version}')
    await ctx.send(embed=help)
    await ctx.send('https://discord.gg/ttrNWzcTZM')

#about (useless too)
@bot.slash_command()
async def about(ctx):
    """
    Sends information about this bot {{ INFO }}
    """
    embed = disnake.Embed(title="Информация о боте", description=f'''
    Бот, созданный для людей.
    Имеет весёлые команды, команды администрирования и другие штуки.

    Версия бота: {bot_version}    
    ''', color=0x0297fa)
    author = ctx.author
    embed.set_author(name=ctx.author, icon_url=author.avatar)
    embed.set_footer(text='Made for people. By SGR.')
    
    await ctx.send(embed=embed)

#server
@bot.slash_command() #TODO: Make this works
async def server(ctx):
    """
    Sends information about this server. {{ SERVER }}
    """
    # guild = ctx.guild
    # total_members = guild.member_count
    # online_members = sum(1 for member in guild.members if member.status != disnake.Status.offline)

    # emb = disnake.Embed(title=f'{guild.name} - Информация')
    # emb.add_field(name='Участники', value=f"Всего участников: {total_members}\nОнлайн: {online_members}")
    await ctx.send("WIP", ephemeral=True)

#avatar
@bot.slash_command()
async def avatar(ctx, *, member: disnake.Member = None):
    """
    Sends member avatar {{ USERAVATAR }}

    Parameters
    ----------
    member: Member {{ MEMBER }}
    """
    if member is None:
        try:
            member = ctx.author
            embed = disnake.Embed(title=f"Аватар {ctx.author}", color=0x0297fa)
            embed.set_image(url=member.avatar)

        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
    else:
        embed = disnake.Embed(title=f"Аватар {member.name}", color=0x0297fa)
        embed.set_image(url=member.avatar)
    
    await ctx.send(embed=embed)

################
#Administration#
################

#kick
@bot.slash_command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: disnake.Member, *, reason: str = None):
    """
    Kicks member from server {{ KICKMEMBER }}

    Parameters
    ----------
    member: member {{ MEMBER }}
    reason: reason {{ KICKREASON }}
    """
    if reason is None:
        try:
            reason="Причина не указана." + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
    else:
        reason=reason + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
    if member is None:
        try:
            ctx.send(err1)
        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
    else:
        if member.top_role.position > ctx.author.top_role.position and member != ctx.guild.owner:
            await ctx.send(embed=err403)
        else:
            emb_kick = disnake.Embed(
                title='<:BAN:1289672537650892973> Кик',
                description=f"{member.mention} ({member.id}) был кикнут с {ctx.guild}\nПричина: {reason}",
                timestamp=datetime.datetime.now(),
                color=0xff0000
            )
            await member.kick(reason=reason)
            await ctx.send(embed=emb_kick)
            print(f"{ctx.author} кикнул {member.id}")

err1 = disnake.Embed(title='Ошибка!', description='Вы не указали пользователя.', color=0xff0000)

#ban
@bot.slash_command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: disnake.Member, *, reason: str = None):
    """
    Bans member from server {{ BANMEMBER }}

    Parameters
    ----------
    member: member {{ MEMBER }}
    reason: reason {{ BANREASON }}
    """
    if reason is None:
        try:
            reason="Причина не указана." + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
    else:
        reason=reason + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
    if member is None:
        try:
            ctx.send(err1)
        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
    elif not member:
        try:
            member = int(member)
            user = await bot.fetch_user(member)
            if member.top_role.position > ctx.author.top_role.position and member != ctx.guild.owner:
                await ctx.send(embed=err403)
            else:
                emb_ban = disnake.Embed(
                    title='<:BAN:1289672537650892973> Бан',
                    description=f"<@{user.id}> ({user.id}) был забанен на {ctx.guild}\nПричина: {reason}",
                    timestamp=datetime.datetime.now(),
                    color=0xff0000
                )
                await member.ban(reason=reason)
                await ctx.send(embed=emb_ban)
                print(f"{ctx.author} забанил {member.id}")
        except:
            pass
    else:
        if member.top_role.position > ctx.author.top_role.position and member != ctx.guild.owner:
            await ctx.send(embed=err403)
        else:
            emb_ban = disnake.Embed(
                title='<:BAN:1289672537650892973> Бан',
                description=f"{member.mention} ({member.id}) был забанен на {ctx.guild}\nПричина: {reason}",
                timestamp=datetime.datetime.now(),
                color=0xff0000
            )
            await member.ban(reason=reason)
            await ctx.send(embed=emb_ban)
            print(f"{ctx.author} забанил {member.id}")

err1 = disnake.Embed(title='Ошибка!', description='Вы не указали пользователя.', color=0xff0000)

#unban
@bot.slash_command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, member: str):
    """
    Unbans member from server {{ UNBANMEMBER }}

    Parameters
    ----------
    member: id {{ MEMBER }}
    """
    if not member:
        await ctx.send(err1)
    else:
        try:
            member = int(member)
            user = await bot.fetch_user(member)
        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
        
        emb_unban = disnake.Embed(
            title='<:YES1:1289673871707869285> Разбан',
            description=f"<@{user.id}> ({user.id}) был разбанен на {ctx.guild}\nМодератор: {ctx.author} ({ctx.author.id})",
            timestamp=datetime.datetime.now(),
            color=0x0fff50
        )
        await ctx.guild.unban(user)
        await ctx.send(embed=emb_unban)
        print(f"{ctx.author} разбанил {member.id}")

#mute
@bot.slash_command() #TODO: Float-Int conversion
@commands.has_permissions(mute_members=True)
async def mute(ctx, member: disnake.Member, *, time: str, reason: str = None):
    """
    Mutes member for a while. {{ MUTE }}

    Parameters
    ----------
    member: Member {{ MEMBER }}
    time: Time {{ MUTETIME }}
    reason: Reason {{ MUTEREASON }}
    """
    if reason is None:
        try:
            reason="Причина не указана." + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
        except Exception as e:
            await ctx.send('Произошла ошибка. Дополнительная информация выведена в консоль.')
            print(f"Ошибка: {e}, отправитель: {ctx.author}")
    else:
        reason=reason + (f"\n Модератор: {ctx.author} ({ctx.author.id})")
    time = datetime.datetime.now() + datetime.timedelta(minutes=float(time))
    await member.timeout(reason=None, until=time)
    emb_mute = disnake.Embed(
        title='<:MUTE:1289673681110565070> Мьют',
        description=f"{member.mention} ({member.id}) был замьючен до {time}\nПричина: {reason}",
        timestamp=datetime.datetime.now(),
        color=0xff0000
    )
    await ctx.send(embed=emb_mute)
    print(f'{member} был замьючен до {time} по причине {reason}.')

#unmute
@bot.slash_command()
@commands.has_permissions(mute_members=True)
async def unmute(ctx, member: disnake.Member):
    """
    Unmutes member. {{ UNMUTE }}

    Parameters
    ----------
    member: Member {{ MEMBER }}
    """
    author = ctx.author
    emb_unmute = disnake.Embed(
        title='<:SOUND:1289711648424333322> Размьют',
        description=f"{member.mention} ({member.id}) был размьючен!\nМодератор: {ctx.author} ({ctx.author.id})",
        timestamp=datetime.datetime.now(),
        color=0x0fff50
    )
    await member.timeout(reason=None, until=None)
    await ctx.send(embed=emb_unmute)
    print(f'{member} **был размьючен.\nМодератор:** {author}.')

#clear
@bot.slash_command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """
    Clears some messages. {{ CLEAR }}

    Parameters
    ----------
    amount: Amount {{ AMOUNT }}
    member: Member {{ MEMBER }}
    """
    emb_clear = disnake.Embed(
        title='<:CLEAR:1289712793116872714> Чистка сообщений',
        description=f"Очищено {amount} сообщений\nМодератор: {ctx.author} ({ctx.author.id})",
        timestamp=datetime.datetime.now(),
        color=0xff0000
    ) 
    # if member == None:
    await ctx.channel.purge(limit=amount)
    await ctx.send(embed=emb_clear, delete_after=10)
    print(f'Была воспроизведена очистка {amount} сообщений.\nМодератор:{ctx.author}.')
    # else:
    #     await ctx.purge(limit=amount, check=is_member)
    #     await ctx.send(f'**Очищено {amount} сообщений участника {member.mention}!**\n**Модератор: {ctx.author.mention}**', delete_after=10)
    #     print(f'Была воспроизведена очистка {amount} сообщений участника {member}.\nМодератор:{ctx.author}.')

########
#Errors#
########

@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=err403)
        print(f'Ошибка 403. Отправитель: {ctx.author}')

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=err403)
        print(f'Ошибка 403. Отправитель: {ctx.author}')

@kick.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=err403)
        print(f'Ошибка 403. Отправитель: {ctx.author}')

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=err403)
        print(f'Ошибка 403. Отправитель: {ctx.author}')

@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=err403)
        print(f'Ошибка 403. Отправитель: {ctx.author}')

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=err403)
        print(f'Ошибка 403. Отправитель: {ctx.author}')

bot.i18n.load("locale/ru.json")
bot.run(settings['token'])