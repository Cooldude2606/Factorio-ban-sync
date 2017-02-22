import os, configparser, importlib, time, datetime
scriptDir = os.path.dirname(os.path.realpath('__file__'))

masterconfig = configparser.ConfigParser()
masterconfig.read('masterconfig.ini')

restart = importlib.import_module(masterconfig['Scripts']['restart'])

while True:
    now = datetime.datetime.now()
    date = '{:%Y-%m-%d}'.format(datetime.datetime(now.year, now.month, now.day))
    print('DATE:',date)
    player = input('PLAYER: ')
    server = input('SERVER: ')
    fromserver = input('FROM SERVER: ')
    print(restart.generateCode(date,player,server,fromserver))
    time.sleep(5)
