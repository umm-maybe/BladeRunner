import logging
from detoxify import Detoxify
import discord
import praw
from simpletransformers.classification import ClassificationModel

model = ClassificationModel(
    "bert", "baykenney/bert-base-gpt2detector-topk40", num_labels=2, use_cuda=False
)

detox = Detoxify('unbiased-small', device='cpu')

reddit = praw.Reddit(
    client_id="CLIENT_ID",
    client_secret="CLIENT_SECRET",
    password="PASSWORD",
    user_agent="Comment Extraction (by u/USERNAME)",
    username="USERNAME",
)

TOKEN = 'OTk5NTE3NjU5NTA5MDQzMjgw.GWN0x4.Nth7_QHk-9CkaGlkL2H29TyUbnADfN0-2grOK8' #Put your Discord token Here!
DEDICATED_CHANNEL_NAME = 'mods' #Put the name of the channel in your server where you want the bot to chat!
SUB = 'subsimgpt2interactive' #Put the name of the subreddit you wish to report on

#Set help message
help = """Commands:
```
!set                ~ Set the subreddit you wish to query
!top                ~ Get statistics on top users by metric:
 posts                most posts
 comments             most comments
!tox                ~ Run Detoxify report on a user or a subreddit
 username             returns toxicity, severe_toxicity, obscene, threat, insult, identity_attack, sexual_explicit
!v-k                ~ Tests how bot-like a user is (a.k.a. a "Voight-Kampff" test)
 username
```
"""



client = discord.Client()

@client.event
async def on_message(message):
    if str(message.channel) == DEDICATED_CHANNEL_NAME:
        if message.content == '!help':
            await message.channel.send(help)
            return
        elif message.content.startswith('!set'):
            global SUB=message.content.split()[1:]
            msgTxt = f"Subreddit set to {SUB}"
            await message.channel.send(msgTxt)
            return
        elif message.content.startswith('!top'):
            command = message.content.split()[1:]
            if command == "posts":
                tally = {}
                n = 0
                for submission in reddit.subreddit(SUB).new(limit=1000):
                    auth = submission.author
                    if tally and auth in tally.keys():
                        tally[auth] += 1
                    else:
                        tally[auth] = 1
                    n = n + 1
                msgTxt = f"Post share by user, {SUB}"
                sorted_tally = sorted(tally, key=tally.get)
                for auth in sorted_tally.keys():
                    shr = round(sorted_tally[auth]/10,2)
                    msgTxt = msgTxt + "\n{}: {}%".format(auth, shr)
                await message.channel.send(msgTxt)
                return
            elif command == "comments":
                tally = {}
                for comment in reddit.subreddit("test").comments(limit=1000):
                    auth = comment.author
                    if tally and auth in tally.keys():
                        tally[auth] += 1
                    else:
                        tally[auth] = 1
                msgTxt = f"Total comments by user, {SUB}"
                sorted_tally = sorted(tally, key=tally.get)
                for auth in sorted_tally.keys():
                    shr = round(sorted_tally[auth]/10,2)
                    msgTxt += "\n{}: {}%".format(auth, shr])
                await message.channel.send(msgTxt)
                return
            else:
                msgTxt = f"!top command {command} not found"
                await message.channel.send(msgTxt)
                return
        elif message.content.startswith('!tox'):
            user = message.content.split()[1:]
            n = 0
            tally = {'toxicity': 0, 'severe_toxicity': 0, 'obscene': 0, 'identity_attack': 0, 'insult': 0, 'threat': 0, 'sexual_explicit': 0}
            for comment in reddit.redditor(user).comments.new(limit=1000):
                try:
			        results = detox.predict(comment.body)
		        except:
			        logging.exception("Exception when trying to run detoxify prediction on {}".format(comment.body))
                if tally.keys() != results.keys():
        			logging.warning(f"Detoxify result keys and tally keys do not match.")
        			continue
        		for key in tally.keys():
        			tally[key] += results[key]
                n += 1
            msgTxt = f"Detoxify report for user {user}"
            for key in tally.keys():
                msgTxt += "\n{}: {}".format(key, round(results[key]/n,2))
            await message.channel.send(msgTxt)
            return
        elif message.content.startswith('!v-k'):
            user = message.content.split()[1:]
            n_chars = 0
            tally = 0
            for comment in reddit.redditor(user).comments.new(limit=1000):
                try:
			        predictions, raw_outputs = model.predict([comment.body])
		        except:
			        logging.exception(f"Exception when trying to run Voight-Kampff test on {comment.body}")
                tally += predictions[0]*len(comment.body)
                n_chars += len(comment.body)
            for submission in reddit.redditor(user).submissions.new(limit=100):
                post_text = submission.title + "\n" + submission.selftext
                try:
			        predictions, raw_outputs = model.predict([post_text])
		        except:
			        logging.exception(f"Exception when trying to run Voight-Kampff test on {post_text}")
                tally += predictions[0]*len(post_text)
                n_chars += len(post_text)
            msgTxt += "There is a {} probability that {} is a GPT-2 bot.".format(round(tally/n_chars,2), user)
            await message.channel.send(msgTxt)
            return
    else:
        return

client.run(TOKEN)
