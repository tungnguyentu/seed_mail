import sys
import time
from datetime import datetime
import uuid

import asyncio
import threading

from src.libs.logger import logger
from src.libs.arguments import args
from src.libs.client import imap, smtp
from src.configuration.smtpconfig import SmtpConfig
from src.configuration.imapconfig import ImapConfig
from concurrent.futures import ThreadPoolExecutor
import imaplib
from datetime import datetime

imaplib._MAXLINE = 900000000000000000

sys.tracebacklimit = 0


def send_new_mail(date, numb):
    logger.info("Main thread name: {}"
                .format(threading.current_thread().name))
    rcpt_to = SmtpConfig.rcpt_to.split(",")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    smtp.send_mail(SmtpConfig.user, rcpt_to, SmtpConfig.payload.format(current_time, numb, now))


def imap_add_message_to_sent():
    logger.info("Main thread name: {}"
                .format(threading.current_thread().name))
    client = imap.new_imap_client()
    imap.login(client)
    imap.send_message(client, ImapConfig.payload)


def imap_new_message():
    logger.info("Main thread name: {}"
                .format(threading.current_thread().name))
    client = imap.new_imap_client()
    imap.login(client)
    imap.new_message(client)


def imap_delete_message(folder: str):
    logger.info("Main thread name: {}"
                .format(threading.current_thread().name))
    client = imaplib.IMAP4(ImapConfig.host, ImapConfig.port)
    client.starttls()
    client.login(ImapConfig.user,ImapConfig.password)
    imap.delete(client, folder)


def get_arg(send, add, new, delete):
    mapping_func = {
        send: send_new_mail,
        add: imap_add_message_to_sent,
        new: imap_new_message
    }
    delete_mail = {
        delete: imap_delete_message
    }
    number_of_message = max(mapping_func.keys())
    func = mapping_func.get(number_of_message)
    folder = None
    if delete:
        folder = delete
        func = delete_mail.get(delete)
    return number_of_message, func, folder


async def main(number_of_message: int, func, folder=None):
    loop = asyncio.get_running_loop()
    if folder:
        loop.run_in_executor(ThreadPoolExecutor(max_workers=1), func, folder)

    executor = None
    if number_of_message > 0:
        executor = ThreadPoolExecutor(max_workers=50)
    
    for i in range(number_of_message):
        loop.run_in_executor(executor, func, time.time(), i)


if __name__ == '__main__':
    number_of_message, func, folder = get_arg(**args.__dict__)
    s = time.perf_counter()
    asyncio.run(main(number_of_message, func, folder))
    elapsed = time.perf_counter() - s
    logger.info(f"{__file__} EXECUTED IN {elapsed:0.5f} SECONDS.")
