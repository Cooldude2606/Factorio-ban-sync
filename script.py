import os, configparser, importlib, time
scriptDir = os.path.dirname(os.path.realpath('__file__'))

masterconfig = configparser.ConfigParser()
masterconfig.read('masterconfig.ini')

log = importlib.import_module(masterconfig['Scripts']['log'])
sync = importlib.import_module(masterconfig['Scripts']['sync'])
restart = importlib.import_module(masterconfig['Scripts']['restart'])

for i in range(0,int(masterconfig['Other']['looptime'])):
    log.readLogs()
    sync.syncStratUpChecks()
    sync.syncAllServers()
    restart.autoRestart()
    time.sleep(float(masterconfig['Other']['sleeptime']))  
    
while masterconfig['Other']['looptime'] == '0':
    log.readLogs()
    sync.syncStratUpChecks()
    sync.syncAllServers()
    restart.autoRestart()
    time.sleep(float(masterconfig['Other']['sleeptime']))
