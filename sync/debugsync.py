import configparser, os, re, ast, subprocess
scriptDir = os.path.dirname(os.path.realpath('__file__'))

masterconfig = configparser.ConfigParser()
masterconfig.read('masterconfig.ini')

relitiveScriptDir = os.path.join(scriptDir, os.path.normpath(masterconfig['Scripts']['sync'][:-10]))
print(relitiveScriptDir)
config = configparser.ConfigParser()
config.read(os.path.join(relitiveScriptDir,'localConfig.ini'))
rawlogPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['rawlog']))
syncPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['sync']))

def sync(command):
    for server in config['Sync']:
        if config['Sync'][server] == 'true':
            print('SENDING COMMAND FROM %s TO %s'%(masterconfig['Server Names'][command['server']],masterconfig['Server Names'][server]))
            if command['type'] == 'BAN':
                print('service', masterconfig['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player'], command['reason'], '- '+command['byPlayer'])
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player'], command['reason'], '- '+command['byPlayer']])
            else:
                print('service', masterconfig['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player'])
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player']])

def addToSync(report):
    print('ADDED %s TO SYNC' %(report['type']))
    with open(syncPath, 'a+') as sync:
        sync.write(str(report)+'\n')

def removeFromSync(player, type):
    print('REMOVED %s FROM SYNC' %(type))
    lines = open(syncPath, 'r').readlines()
    with open(syncPath, 'w') as sync:
        for line in lines:
            line = line[:-1]
            if re.search('{(.+?)}',line):
                currentReport = ast.literal_eval(re.search('{(.+?)}',line).group(0))
                if currentReport['player'] == player and currentReport['type'] == type:
                    break
                else:
                    sync.write(str(currentReport)+'\n')

def readBans():
    print('START READING BANS')
    server = config['Other']['defaultserver']
    log = {}
    for line in open(os.path.join(scriptDir,os.path.normpath(masterconfig['Paths'][server]),os.path.normpath(masterconfig['Paths']['bans'])),'r').readlines():
        line = line[:-1]
        log['server'] = server
        log['type'] = 'BAN'
        if re.search('"username": "(.*?)"',line):
            log['player'] = re.search('"username": "(.*?)"',line).group(0)[13:-1]
        elif re.search('"reason": "(.+?)"',line):
            if re.search(' - ?(.+?)"',line):
                log['byPlayer'] = re.search(' - ?(.+?)"',line).group(0)[3:-1]
                log['reason'] = re.search('"reason": "(.+?)"',line).group(0)[11:-(len(log['byPlayer'])+4)]
            else:
                log['reason'] = re.search('"reason": "(.+?)"',line).group(0)[11:-1]
        elif re.search('},',line):
            if not 'reason' in log:
                log['reason'] = 'Non Given'
            if not 'byPlayer' in log:
                log['byPlayer'] = '<Non_Given>'
            addToSync(log)
            sync(log)
            log = {}

def readAdmins():
    print('START READING ADMINS')
    server = config['Other']['defaultserver']
    for line in open(os.path.join(scriptDir,os.path.normpath(masterconfig['Paths'][server]),os.path.normpath(masterconfig['Paths']['admins'])),'r'):
        line = line[:-1]
        if re.search('"admins": (.+?)]',line):
            admins = ast.literal_eval(re.search('\[(.+?)\]',line).group(0))
            break
    for player in admins:
        log = {}
        log['server'] = server
        log['type'] = 'PROMOTE'
        log['player'] = player
        addToSync(log)
        sync(log)

def syncStratUpChecks():
    print('STARTING SETUP CHECKS')
    if config['Other']['firstTimeSetUp'] == 'true':
        print('STARTING FIRST TIME SETUP')
        config['Other']['firstTimeSetUp'] = 'false'
        config['Other']['logprogress '] = '0'
        syncFile = open(syncPath, 'w') 
        readBans()
        readAdmins()
    elif config['Other']['newserver'].lower() != 'n/a':
        print('SENDING COMMANDS TO NEW SERVER:',masterconfig['Server Names'][server])
        server = config['Other']['newserver']
        config['Other']['newserver'] = 'N/A'
        for line in open(syncPath,'r'):
            line = line[:-1]
            line = ast.literal_eval(re.search('{(.+?)}',line).group(0))
            if line['type'] == 'BAN':
                print('service', masterconfig['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player'], line['reason'], '- '+line['byPlayer'])
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player'], line['reason'], '- '+line['byPlayer']])
            else:
                print('service', masterconfig['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player'])
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player']]) 

def getNewLines():
    log = open(os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['rawlog'])),'r').readlines()
    if int(config['Other']['logprogress']) <= log.index(log[-1])+1:
        toReturn = log[int(config['Other']['logprogress']):]
    else:
        toReturn = log[0:]
    print('GOT %s NEW LINES' %(len(toReturn)))
    config['Other']['logprogress'] = str(log.index(log[-1])+1)
    return toReturn

    
def syncAllServers():
    lines = getNewLines()
    for server in masterconfig['Server Names']:
        toSync = ['ban','unban','promote','demote']
        for line in lines:
            line = ast.literal_eval(re.search('{(.+?)}',line).group(0))
            print(line)
            if line['type'] in toSync and line['byplayer'] != '<server>':
                if line['type'] == 'BAN':
                    removeFromSync(line['player'],'UNBAN')
                    addToSync(line)
                    sync(line)
                elif line['type'] == 'UNBAN':
                    removeFromSync(line['player'],'BAN')
                    addToSync(line)
                    sync(line)
                elif line['type'] == 'PROMOTE':
                    removeFromSync(line['player'],'DEMOTE')
                    addToSync(line)
                    sync(line)
                elif line['type'] == 'DEMOTE':
                    removeFromSync(line['player'],'PROMOTE')
                    addToSync(line)
                    sync(line)
    print('SAVING CONFIG')
    with open(os.path.join(relitiveScriptDir,'localConfig.ini'), 'w') as configfile:
        config.write(configfile)
