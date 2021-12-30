# Discord Bot for Heroku
This bot has a wide functionality, and pretty easy to deploy
## Configuration
All configurations can be done with using config.py file
### This bot was written for users of Russian servers, and send all data in russian. Although the code and database structure was written if possible in English 

### Available  features:
1. Basic admin commands: ban, kick, mute, unmute
2. Deleting messages using the ?clear command 
3. Getting a random picture using Google engine 
4. Possibility of search queries in Google 
* To be able use point 3 and 4 you have to get google api tokens and put the to config.txt file, or keep them as system variables 
5. Sending voice messages
6. Creating poll messeage of two types, what will send results at the end of the vote time.
7. Extensive opportunities to calculate the statistics of messages. This bot can keep message and symbols stats. 
Track stats for different periods of time: day, week and all time together. As well it will handle maximum stats for users and server overall.
8. By the end of the: day, week, month bot will automatically send message stats
* Unfortunately, all databases were created in manual mode and the migration not available. You can create them by viewing description of data clasess: utils/data
9. Feature to save and get users quotes.
10. You can save events from your life time in database and then get them. As well you can group your memories by different periods of time.
11. Prohibition on use CAPS LOCK mode by admin desire.
12. Available translation to different languages with google translate api

### Thanks:
Some parts of code been copy pasted (or used as starting point) and then updated to be used inside my bot, here is the references: <br />
Point 3, 4, 12 -> https://github.com/appu1232/Discord-Selfbot<br />
Point 6 -> https://github.com/stayingqold/Poll-Bot
PS I hope it's legal and i won't go to jail ^_^
