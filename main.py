import tweepy
import time
import csv
import sys
import os
from dotenv import dotenv_values
from discord_webhook import DiscordWebhook, DiscordEmbed

config = dotenv_values(".env")

# For Twitter: Add the relevant keys, tokens and secrets from your Twitter app made here: https://apps.twitter.com/

client = tweepy.Client(bearer_token=config["bearer_token"],wait_on_rate_limit=True)

# Variables - configure the bits below to get your script working. 

style = "1da1f2"   # Colour for the message - default is Twitter Bird blue

# Discord incoming webhook URL

webhook = DiscordWebhook(url=config["discord_webhook"], username="Twitter Follow Alert")

# Database

pathDatabase = os.path.dirname(os.path.realpath(__file__)) + "/database.csv"

# Init
database = dict()
author = dict()
content = dict()
csvHeading = ["idTweeter","lastFollowing"]
newFollowings = False

# Read CSV file to know get the following list and then update it.

try:
    fileDatabase = open(pathDatabase, 'r+')
    if (os.path.getsize(pathDatabase) == 0):
        print("Please fill the database before launching the program.")
        fileDatabase.close()
        sys.exit()
    else:
        reader = csv.DictReader(fileDatabase, delimiter=',')
        for data in reader:
            database[data['idTweeter']] = data['lastFollowing'].split(';')
        fileDatabase.close()
        print("Database successfuly read")
except OSError:
    print ("Could not open/read file: " + pathDatabase)
    print ("Creating the file...")
    try:
        fileDatabase = open(pathDatabase, 'w')
        print("database.csv has been successfuly created !")
        print("Please fill the database before launching the program.")
        fileDatabase.close()
        sys.exit()
    except OSError:
        print("File couldn't be created. The program will be stopped.")
        sys.exit()


def followers():
    
    while True:
        # We are going to loop the database, and thus comparing the database with the data of the API.
        for key, value in database.items():
            popValuesFromDB = 0
            print("Checking in progress for", key)
            # We get the last followings of the user.

            lastFollowings = client.get_users_following(id=key, max_results=10, user_fields=['description','profile_image_url'])
            
            # We loop through the 10 last followings of the user.
            for i in range(0,10):
                if (str(lastFollowings[0][i].id) not in value):

                    personWhoFollows = client.get_user(id=key, user_fields=['profile_image_url'])
                    print(f"@{personWhoFollows[0].username} !")

                    # We update the database values : we insert the new followings.
                    database[key].insert(0,str(lastFollowings[0][i].id))
                    # We need to delete the older values when we're done looping.
                    popValuesFromDB += 1

                    # Prepare values for Discord notification
                    author['name'] = "@" + personWhoFollows[0].username 
                    author['URL'] = "https://twitter.com/" + personWhoFollows[0].username
                    author['IconURL'] = personWhoFollows[0].profile_image_url

                    content['title'] = "@" + lastFollowings[0][i].username
                    content['description'] = lastFollowings[0][i].description
                    content['url'] = "https://twitter.com/" + lastFollowings[0][i].username

                    # # Send Discord notification
                    ## webhook.set_content(author['name'] + ' followed ' + content['title'] + ' !')

                    webhook.remove_embeds()
                    
                    embed = DiscordEmbed(title=content['title'], description=content['description'], color=style, url=content['url'])
                    embed.set_author(name=author['name'] + " followed", url=author['URL'], icon_url=author['IconURL'])
                    embed.set_image(url=lastFollowings[0][i].profile_image_url)
                    embed.set_timestamp()
                    
                    webhook.add_embed(embed)
                    webhook.execute()
                    
                    time.sleep(1)

            if (popValuesFromDB != 0):
                for i in range (0, popValuesFromDB):
                    database[key].pop()
                # We write down on the CSV file the newest database
                print("Database rewriting in progress...")
                with open(pathDatabase, 'w') as fileDatabase:
                    writer = csv.writer(fileDatabase, delimiter=',')
                    writer.writerow(csvHeading)
                    for idTweeter, lastFollowing in database.items():
                        writer.writerow([idTweeter, ';'.join(lastFollowing)])
                print("Finished rewriting!") 
            
            print("Completed check!")

            time.sleep(1)    
    
followers()    