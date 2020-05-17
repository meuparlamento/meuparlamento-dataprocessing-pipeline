from crontab import CronTab


user = "root"

cron = CronTab(user=user)

# setup get last published proposals and update probabilities 
job = cron.new(command='python3 get_last_published_proposals.py; python3 update_probabilities.py')
job.setall("0 0 * * *") #daily at midnight
job.enable()

cron.write()

