import requests
import discord
from discord.ext import tasks, commands
import pprint
import sqlite3
from datetime import datetime

APIkey = ""

server = ""
statsChannel = ""
statsChannelSlug = ""
statsChannelMessage = ""

slug = ""

collectionName = ""
collectionPicture = ""
collectionChain = ""
collectionDescription = ""
collectionURL = ""

totalSales = 0
totalSupply = 0
totalVolume = 0.0
sevenDayAvgPrice = 0.0
floorPrice = 0.0
owners = 0

#setting up sql tables on a database
con = sqlite3.connect("osbot.db")
cur = con.cursor()

#Creating the different tables for the bot.

#Table for keeping track of the osChannel stats for specific servers.
#cur.execute("CREATE TABLE server(serverID, channelID, messageID, slug)")
#Table for keeping track of abbreviations for collections.
#cur.execute("CREATE TABLE sluga(name, slug)")

#database functions
#Functions for inserting rows in the table
def createChannelOnServer(serverID, channelID, messageID, slug):
    cur.execute("INSERT INTO server VALUES (?, ?, ?, ?)", (serverID, channelID, messageID, slug))
    con.commit()

def createSlugAbreviation(name, slug):
    cur.execute("INSERT INTO sluga VALUES (?, ?)", (name, slug))
    con.commit()

#Functions for returning values from specific rows
def returnServerTableValues(identifier):
    res = cur.execute('SELECT * FROM server WHERE serverID=?', identifier)
    return res.fetchone()

def returnSlugTableValues(identifier):
    res = cur.execute('SELECT * FROM server WHERE serverID=?', identifier)
    return res.fetchone()

def returnAllServerTableValues():
    res = cur.execute('SELECT * FROM server')
    return res.fetchall()

#Gets the stats from the slug name and an OS key
def getStats(slug, key):
    url = "https://api.opensea.io/api/v1/collection/" + slug
    headers = {
        "accept": "application/json",
        "X-API-KEY": key
    }

    response = requests.get(url, headers=headers)

    if(response.ok==True):
        dic = response.json()
        return dic
    else:
        print("error")

#Function that updates the stat variables based on the returned stats
def updateStatVariables(stats):
        
        global collectionDescription
        global collectionPicture
        global collectionName
        global collectionChain
        global collectionURL
        global totalSales
        global totalSupply
        global totalVolume
        global sevenDayAvgPrice
        global floorPrice
        global owners

        collectionDescription = str(stats['collection']['description'])
        collectionPicture = str(stats['collection']['image_url'])
        collectionName = str(stats['collection']['name'])
        collectionChain = str(stats['collection']['primary_asset_contracts'][0]['chain_identifier'])
        collectionURL = "https://opensea.io/collection/" + str(stats['collection']['slug'])
        totalSales = str(stats['collection']['stats']['total_sales'])
        totalSupply = str(int(stats['collection']['stats']['count']))
        totalVolume = str(round(stats['collection']['stats']['total_volume'], 4)) + " ETH"
        sevenDayAvgPrice = str(stats['collection']['stats']['seven_day_average_price'])
        floorPrice = str(stats['collection']['stats']['floor_price'])
        owners = str(stats['collection']['stats']['num_owners'])


intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        global statsChannel
        global server
        global statsChannelSlug
        global statsChannelMessage
        self.update.start()

        

    
    #updates the stats
    @tasks.loop(minutes=1)
    async def update(self):
        
        #gets data from the db which tells it which messages it needs to update and runs a for loop on all of them.
        db = returnAllServerTableValues()
        for x in db:
            statsChannel = x[1]
            statsChannelMessage = x[2]
            statsChannelSlug = x[3]
            
            #updates the stat variables
            updateStatVariables(getStats(statsChannelSlug, APIkey))

            embed = discord.Embed(title=collectionName,
                    url=collectionURL,
                    description=collectionDescription,
                    colour=0x00b0f4)

            embed.add_field(name="Total Supply:",
                            value="```\n" + totalSupply + "\n```",
                            inline=True)
            embed.add_field(name="Owners:",
                            value="```\n" + owners + "\n```",
                            inline=True)
            embed.add_field(name="Chain:",
                            value="```\n" + collectionChain + "\n```",
                            inline=True)
            embed.add_field(name="Floor Price",
                            value="```\n" + floorPrice + "\n```",
                            inline=True)
            embed.add_field(name="7D Average Price:",
                            value="```\n" + sevenDayAvgPrice + "\n```",
                            inline=True)
            embed.add_field(name="Total Volume:",
                            value="```\n" + totalVolume + "\n```",
                            inline=True)
            
            embed.set_image(url=collectionPicture)
            
            #finds the message and updates the embed
            c = await client.fetch_channel(statsChannel)
            m = await c.fetch_message(statsChannelMessage)
            await m.edit(embed=embed)


    async def on_message(self, message):
        #returns if message is sent by self
        if message.author == client.user:
            return
        
        #checks for the prefix sent by the user
        if (message.content[:1] == ";"):

            #checks for the commands setup which sets the channel and slug(the nft collection) 
            #and sends the embeds in that channel 

            if(message.content[:4]==";os "):
            
                #gets the stats from the slug name
                slug = message.content[4:]

                updateStatVariables(getStats(slug, APIkey))

                #Creates an embed with all the data and sends it to the channel
                embed = discord.Embed(title=collectionName,
                    url=collectionURL,
                    description=collectionDescription,
                    colour=0x00b0f4)

                embed.add_field(name="Total Supply:",
                                value="```\n" + totalSupply + "\n```",
                                inline=True)
                embed.add_field(name="Owners:",
                                value="```\n" + owners + "\n```",
                                inline=True)
                embed.add_field(name="Chain:",
                                value="```\n" + collectionChain + "\n```",
                                inline=True)
                embed.add_field(name="Floor Price",
                                value="```\n" + floorPrice + "\n```",
                                inline=True)
                embed.add_field(name="7D Average Price:",
                                value="```\n" + sevenDayAvgPrice + "\n```",
                                inline=True)
                embed.add_field(name="Total Volume:",
                                value="```\n" + totalVolume + "\n```",
                                inline=True)

                await message.channel.send(embed=embed)
            
            #command for finding just the floor value of a sllug
            if message.content[:9]==";osfloor ":
                slug = message.content[9:]
                stats = getStats(slug,APIkey)

                floorPrice = str(stats['collection']['stats']['floor_price'])
                collectionPicture = str(stats['collection']['image_url'])
                collectionName = str(stats['collection']['name'])
                collectionChain = str(stats['collection']['primary_asset_contracts'][0]['chain_identifier'])
                collectionURL = "https://opensea.io/collection/" + str(stats['collection']['slug'])

                embed = discord.Embed(title="Current floor price:",
                        description="**" + floorPrice + " " + collectionChain + "**",
                        colour=0x00b0f4,
                        timestamp=datetime.now())

                embed.set_author(name=collectionName,
                        url=collectionURL,
                        icon_url=collectionPicture)

                await message.channel.send(embed=embed)


            #command to setup a updating message that keeps you updated on a slug
            if(message.content[:8]==";osetup "):

                slug = message.content[8:]
                updateStatVariables(getStats(slug, APIkey))

                #Creates an embed with all the data and sends it to the channel
                embed = discord.Embed(title=collectionName,
                    url=collectionURL,
                    description=collectionDescription,
                    colour=0x00b0f4)

                embed.add_field(name="Total Supply:",
                                value="```\n" + totalSupply + "\n```",
                                inline=True)
                embed.add_field(name="Owners:",
                                value="```\n" + owners + "\n```",
                                inline=True)
                embed.add_field(name="Chain:",
                                value="```\n" + collectionChain + "\n```",
                                inline=True)
                embed.add_field(name="Floor Price",
                                value="```\n" + floorPrice + "\n```",
                                inline=True)
                embed.add_field(name="7D Average Price:",
                                value="```\n" + sevenDayAvgPrice + "\n```",
                                inline=True)
                embed.add_field(name="Total Volume:",
                                value="```\n" + totalVolume + "\n```",
                                inline=True)

                embed.set_image(url=collectionPicture)

                sentMessage = await message.channel.send(embed=embed)

                #enters the data into the database
                server = message.guild.id
                statsChannel = message.channel.id
                statsChannelSlug = slug
                statsChannelMessage = sentMessage.id

                createChannelOnServer(str(server), str(statsChannel), str(statsChannelMessage), str(statsChannelSlug))
    
client = MyClient(intents=intents)
client.run('')



