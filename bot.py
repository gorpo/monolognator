from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
import random
import logging
import os
import re

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

counter = {}
previous_user = None
msg_limit = {}  #random.randint(5, 12)
my_chat_id = 113426151
#logger.info(f'First msg limit: {msg_limit}')

# List of existing gifs to send to chat
gifs = ['hand', 'bla', 'incoming', 'duck', 'typing1', 'tsunami']


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I'm The MonologNator. I'll be back")


def get_limit(bot, update):
    global msg_limit
    if update.message.chat_id not in msg_limit:
        random_limit(bot, update)
    logger.info(f'Limit query on {update.message.chat.title}'
                f' by {update.message.from_user.first_name}.'
                f' Limit: {msg_limit[update.message.chat_id]}')
    bot.send_message(chat_id=update.message.chat_id,
                     text=f"Current monologue limit: {msg_limit[update.message.chat_id]}")
    logger.info('================================================')


def random_limit(bot, update):
    global msg_limit
    msg_limit[update.message.chat_id] = random.randint(5, 12)
    logger.info(f'Random limit of {msg_limit[update.message.chat_id]} set on {update.message.chat.title}')
    return msg_limit[update.message.chat_id]


def set_limit(bot, update):
    logger.debug(update.message.text)
    global msg_limit
    msg = update.message.text
    msg_limit[update.message.chat_id] = int(re.findall('[0-9]+', msg)[0])
    logger.info(f'New Limit set by {update.message.from_user.first_name}: {msg_limit[update.message.chat_id]}')


def send_gif(bot, update):
    bot.send_document(chat_id=update.message.chat_id,
                      document=open('./gifs/' + random.choice(gifs) + '.gif', 'rb'), timeout=100)


def delete_messages(bot, update, user, chat):
    # Delete messages from group
    for m in set(counter[user]['msg_ids']):
        bot.delete_message(chat_id=chat, message_id=m)


def multi_count(bot, update):
    global counter
    global previous_user
    global msg_limit

    user = update.message.from_user.id
    chat = update.message.chat_id

    if chat not in msg_limit:
        random_limit(bot, update)

    #Check if chat is in counter
    if chat not in counter:
        counter[chat] = {}

    # if user not seen before in this chat, create dictionary and set initial count
    if user not in counter[chat]:
        counter[chat][user] = {}
        user_counter = counter[chat][user]
        user_counter['count'] = 1
        user_counter['msg_ids'] = [update.message.message_id]
        user_counter['msgs'] = [update.message.text]
        counter[chat]['latest_by'] = user
    else:
        # if we seen the user before, check if previous msg was by the same user
        # if it was, increase counter and add msgs
        if user == counter[chat]['latest_by']:
            user_counter = counter[chat][user]
            user_counter['count'] += 1
            user_counter['msg_ids'].append(update.message.message_id)
            user_counter['msgs'].append(update.message.text)
        else:
            # If the msg was by a different user, reset counter for previous user and start new counter for new user.
            previous_user = counter[chat]['latest_by']
            logger.info(f"Reseting the counter for {previous_user} on {update.message.chat.title}")
            # remove previous user from dictionary
            counter[chat].pop(previous_user)
            user_counter = counter[chat][user]
            user_counter['count'] = 1
            user_counter['msg_ids'] = [update.message.message_id]
            user_counter['msgs'] = [update.message.text]
            counter[chat]['latest_by'] = user

    logger.info(f'Count for {update.message.from_user.first_name} on {update.message.chat.title}: {user_counter["count"]}')
    logger.info(f'Msg on {update.message.chat.title}'
                f' from {update.message.from_user.first_name}:  {update.message.text}')
    logger.debug(f'limit: {msg_limit[chat]}')
    logger.debug(counter[chat][user]['msg_ids'])
    logger.debug(counter[chat][user]['msgs'])
    user_count = counter[chat][user]['count']
    logger.info('================================================')

    if user_count >= msg_limit[chat]:
        logger.info(f'{user} hit the limit on {update.message.chat.title}')
        # Clear counter for user
        counter[chat][user]['count'] = 0

        # Reset random limit
        limit = random_limit(bot, update)
        bot.send_message(chat_id=my_chat_id,
                         text=f'New msg limit set on {update.message.chat.title}: {limit}')

        # Delete messages from group
        for m in set(counter[chat][user]['msg_ids']):
            bot.delete_message(chat_id=update.message.chat_id, message_id=m)

        # Send funny gif
        bot.send_document(chat_id=update.message.chat_id,
                          document=open('./gifs/' + random.choice(gifs) + '.gif', 'rb'), timeout=100)

        # Send monologue back as a single message
        bot.send_message(chat_id=update.message.chat_id,
                         text='*Monologue by {}*:\n\n`{}`'.format(
                             update.message.from_user.first_name,
                             "\n".join(counter[chat][user]['msgs'])), parse_mode=telegram.ParseMode.MARKDOWN)

        # reset msgs and counters for user
        counter[chat].pop(user)



def count(bot, update):
    global counter
    global previous_user
    global msg_limit

    user = update.message.from_user.id

    # Check if counter exists, if not. start it
    if user not in counter:
        counter[user] = {}
        counter[user]['count'] = 1
        counter[user]['msg_ids'] = list()
        # Add first msg id to counter
        counter[user]['msg_ids'].append(update.message.message_id)
        counter[user]['msgs'] = list()
        # Add first message to counter
        counter[user]['msgs'].append(update.message.text)
    else:
        # if current msg is by the same user as previous msg,
        # increase counter, add msg_id and message to counter
        if user == previous_user:
            counter[user]['count'] += 1
            counter[user]['msg_ids'].append(update.message.message_id)
            counter[user]['msgs'].append(update.message.text)
        else:
            # If it's a new user, reset counter for previous user
            logger.info(f'Reseting the counter for {previous_user}')
            counter[previous_user]['count'] = 1
            counter[previous_user]['msg_ids'] = list()
            counter[previous_user]['msgs'] = list()

    logger.info(f'Count for {user}: {counter[user]["count"]}')
    previous_user = user
    logger.info(f'Msg on {update.message.chat.title}'
                f' from {update.message.from_user.first_name}:  {update.message.text}')
    logger.debug(f'limit: {msg_limit}')
    logger.debug(counter[user]['msg_ids'])
    logger.debug(counter[user]['msgs'])
    user_count = counter[user]['count']
    logger.info('================================================')

    if user_count == msg_limit:
        # Clear counter for user
        counter[user]['count'] = 0

        # Reset random limit
        msg_limit = random.randint(5, 12)
        logger.info(f'New random limit: {msg_limit}')
        bot.send_message(chat_id=my_chat_id, text=f'New msg limit set: {msg_limit}')

        # Delete messages from group
        for m in set(counter[user]['msg_ids']):
            bot.delete_message(chat_id=update.message.chat_id, message_id=m)

        # Send funny gif
        bot.send_document(chat_id=update.message.chat_id,
                          document=open('./gifs/' + random.choice(gifs) + '.gif', 'rb'), timeout=100)

        # Send monologue back as a single message
        bot.send_message(chat_id=update.message.chat_id,
                         text='*Monologue by {}*:\n\n`{}`'.format(
                             update.message.from_user.first_name,
                             "\n".join(counter[user]['msgs'])), parse_mode=telegram.ParseMode.MARKDOWN)

        # reset msgs and counters for user
        counter[user]['msgs'] = list()
        counter[user]['msg_ids'] = list()


def main():

    updater = Updater(os.getenv('telegram_token'))
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('limit', get_limit))
    updater.dispatcher.add_handler(CommandHandler('set_limit', set_limit))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, multi_count))
    updater.start_polling(clean=True)
    logger.info('Starting Monolognator...')
    updater.idle()


if __name__ == '__main__':
    main()