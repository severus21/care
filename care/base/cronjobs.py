'''
Created on Aug 25, 2014

@author: Bart Romgens
'''

from care.settings import BASE_DIR
from care.userprofile.models import UserProfile, NotificationInterval
from care.groupaccount.models import GroupAccount, GroupSetting
from care.transaction.models import Transaction, TransactionRecurring

from care.base import emailserver

from django_cron import CronJobBase, Schedule

import shutil
import os
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


def send_transaction_histories(inteval_name):
    interval = NotificationInterval.objects.get(name=inteval_name)
    userprofiles = UserProfile.objects.all().filter(historyEmailInterval=interval)
    for userprofile in userprofiles:
        logger.info(userprofile.displayname)
        userprofile.send_transaction_history()


def send_low_balance_reminders(inteval_name):
    interval = NotificationInterval.objects.get(name=inteval_name)
    settings = GroupSetting.objects.all().filter(notification_lower_limit_interval=interval)
    groups = GroupAccount.objects.all().filter(settings=settings)
    for group in groups:
        userprofiles = UserProfile.objects.filter(group_accounts=group)
        for userprofile in userprofiles:
            balance = UserProfile.get_balance(group.id, userprofile.id)
            if balance < group.settings.notification_lower_limit:
                assert group in userprofile.group_accounts.all()
                emailserver.send_low_balance_reminder(userprofile.user, group)
                    

class DailyBackup(CronJobBase):
    RUN_EVERY_MINS = 1*24*60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'care.daily_backup'    # a unique code

    def do(self):
        logger.info('backup database')
        now = datetime.now()
        nowStr = now.strftime('%Y%m%d')
        directory = './backup/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        shutil.copy(os.path.join(BASE_DIR, 'care.sqlite'), directory + nowStr + 'care.sqlite')


class DailyEmails(CronJobBase):
    RUN_EVERY_MINS = 1*24*60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'care.daily_emails'    # a unique code

    def do(self):
        send_transaction_histories("Daily")
        send_low_balance_reminders("Daily")


class WeeklyEmails(CronJobBase):
    RUN_EVERY_MINS = 7*24*60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'care.weekly_emails'    # a unique code                    
            
    def do(self):
        send_transaction_histories("Weekly")
        send_low_balance_reminders("Weekly")


class MonthlyEmails(CronJobBase):
    RUN_EVERY_MINS = 30*24*60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'care.monthly_emails'    # a unique code

    def do(self):
        send_transaction_histories("Monthly")
        send_low_balance_reminders("Monthly")


class TestEmails(CronJobBase):
    RUN_EVERY_MINS = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'care.test2_emails'

    def do(self):
        logger.debug('testing email cronjob')
        send_low_balance_reminders("Weekly")
        send_transaction_histories("Monthly")


class CreateRecurrentShareOccurrence(CronJobBase):
    RUN_EVERY_MINS = 2 * 60  # 2 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'care.create_recurrent_share_occurrence'

    def do(self):
        allRecurringShares = TransactionRecurring.objects.filter(
            date__lte=datetime.now(),
            last_occurrence__lt=datetime.now())
        for rShare in allRecurringShares:
            if rShare.next_due <= datetime.now():
                rShare.create_occurrence()
