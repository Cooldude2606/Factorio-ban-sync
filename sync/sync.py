import configparser, os, re, ast, subprocess, json
scriptDir = os.path.dirname(os.path.realpath('__file__'))

masterconfig = configparser.ConfigParser()
masterconfig.read('masterconfig.ini')

relitiveScriptDir = os.path.join(scriptDir, os.path.normpath(masterconfig['Scripts']['sync'][:-5]))

config = configparser.ConfigParser()
config.read(os.path.join(relitiveScriptDir,'localConfig.ini'))
rawlogPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['rawlog']))
syncPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['sync']))

def sync(command):
    for server in config['Sync']:
        if config['Sync'][server] == 'true':
            if command['type'] == 'BAN':
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player'], command['reason'], '- '+command['byplayer']])
            else:
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player']])

def addToSync(report):
    file = json.loads(open(syncPath, 'r').read())
    if report['type'] == 'ban':
        file['bans'].append(report)
    elif report['type'] == 'promote':
        file['admins'].append(report)
    with open(syncPath,'w') as sync:
        sync.write(json.dumps(file,sort_keys=True,indent=2))

def removeFromSync(player, type):
    file = json.loads(open(syncPath, 'r').read())
    if report['type'] == 'ban':
        file['bans'].remove(report)
    elif report['type'] == 'promote':
        file['admins'].remove(report)
    with open(syncPath,'w') as sync:
        sync.write(json.dumps(file,sort_keys=True,indent=2))

def readBans():
    server = config['Other']['defaultserver']
    file = json.loads(open(os.path.join(scriptDir,os.path.normpath(masterconfig['Paths'][server]),os.path.normpath(masterconfig['Paths']['bans'])),'r').read())
    for report in file['bans']:
        log = {}
        log['server'] = server
        log['type'] = 'ban'
        log['player'] = report['username']
        if 'reason' in report:
            if re.search(' - ?(.+?)"',report['reason']):
                log['byplayer'] = re.search(' - ?(.+?)"',report['reason']).group(0)[3:-1]
                log['reason'] = report['reason'][:-(len(log['byplayer'])+4)]
            else:
                log['byplayer'] = '<Non_Given>'
                log['reason'] = report['reason']
        else:
            log['reason'] = 'Non Given'
            log['byplayer'] = '<Non_Given>'
        addToSync(log)
        sync(log)

def readAdmins():
    server = config['Other']['defaultserver']
    file = json.load(open(os.path.join(scriptDir,os.path.normpath(masterconfig['Paths'][server]),os.path.normpath(masterconfig['Paths']['admins'])),'r').read())
    for admin in file['admins']:
        log = {}
        log['server'] = server
        log['type'] = 'promote'
        log['player'] = admin
        addToSync(log)
        sync(log)

def syncStratUpChecks():
    if config['Other']['firstTimeSetUp'] == 'true':
        config['Other']['firstTimeSetUp'] = 'false'
        syncFile = open(syncPath, 'w')
        syncFile.write(json.dumps({'bans': [],'admins': []},sort_keys=True,indent=2))
        syncFile.close()
        readBans()
        readAdmins()
    elif config['Other']['newserver'].lower() != 'n/a':
        server = config['Other']['newserver']
        config['Other']['newserver'] = 'N/A'
        for line in open(syncPath,'r'):
            line = line[:-1]
            line = ast.literal_eval(re.search('{(.+?)}',line).group(0))
            if line['type'] == 'BAN':
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player'], line['reason'], '- '+line['byplayer']])
            else:
                subprocess.call(['service', masterconfig['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player']]) 

def getNewLines(section):
    file = json.loads(open(os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['rawlog'])),'r').read())
    log = file[section]
    if int(config['Log Progress'][section]) <= log.index(log[-1])+1:
        toReturn = log[int(config['Log Progress'][section]):]
    else:
        toReturn = log[0:]
    config['Log Progress'][section] = str(log.index(log[-1])+1)
    return toReturn

def syncAllServers():
    toSync = ['ban','unban','promote','demote']
    for section in toSync:
        newlines = getNewLines(section)
        for server in masterconfig['Server Names']:
            for report in newlines:
                if report['type'] == 'BAN':
                    removeFromSync(line['player'],'UNBAN')
                    addToSync(line)
                    sync(line)
                elif report['type'] == 'UNBAN':
                    removeFromSync(line['player'],'BAN')
                    addToSync(line)
                    sync(line)
                elif report['type'] == 'PROMOTE':
                    removeFromSync(line['player'],'DEMOTE')
                    addToSync(line)
                    sync(line)
                elif report['type'] == 'DEMOTE':
                    removeFromSync(line['player'],'PROMOTE')
                    addToSync(line)
                    sync(line)
    with open(os.path.join(relitiveScriptDir,'localConfig.ini'), 'w') as configfile:
        config.write(configfile)
