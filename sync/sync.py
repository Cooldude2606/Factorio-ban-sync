import configparser, os, re, ast, subprocess
scriptDir = os.path.dirname(os.path.realpath('__file__'))

config = configparser.ConfigParser()
config.read('syncConfig.ini')

syncPath = os.path.join(scriptDir, os.path.normpath(config['Paths']['MasterBans']))
filterlogPath = os.path.join(scriptDir, os.path.normpath(config['Paths']['filterLog']))

#converts a line form a log into a useable list  
def decodeLog(line, server):
    log = {}
    log['server'] = server
    log['type'] = re.search('\[(\D+?)\]',line)
    if log['type'] == None:
        log['type'] = 'other'
        log['filler'] = line
        return log
    if re.search('\(shout\)',line):
        log['type'] = 'Shout'
        log['player'] = re.search('(.+?) ',line).group(0)
        return log
    else:
        log['type'] = log['type'].group(0)[1:-1]
        line = line[:line.find(log['type'])-1] + line[line.find(log['type'])+len(log['type'])+2:]
        log['date'] = re.search('\d{4}-\d{2}-\d{2}',line).group(0)
        line = line[len(log['date'])+1:]
        log['time'] = re.search('\d{2}:\d{2}:\d{2}',line).group(0)
        line = line[len(log['time'])+1:]
    if log['type'] == 'CHAT':
        log['player'] = re.search('(.+?):',line).group(0)[:-1]
        line = line[len(log['player'])+2:]
        log['filler'] = line
        return log
    elif log['type'] == 'BAN':
        log['player'] = re.search('(.+?) ',line).group(0)[:-1]
        line = line[len(log['player'])+1:]
        tag=re.search('\[(.+?)\]',line)
        if tag:
            tag=len(tag.group(0))+2
        else:
            tag=1
        log['byPlayer'] = re.search('by (.+?)\.',line).group(0)[3:-(tag)]
        line = line[:line.find(log['byPlayer'])-1] + line[line.find(log['byPlayer'])+len(log['byPlayer'])+1:]
        log['reason'] = re.search('Reason: (.+?)\.',line).group(0)[8:-1]
        line = line[:-(len(log['reason'])+10)]
        log['filler'] = line
        return log
    elif log['type'] ==  'COLOR':
        log['player'] = re.search('(.+?) ',line).group(0)[:-3]
        line = line[len(log['player'])+1:]
        log['color'] = re.search('now (.+?)$',line).group(0)[4:]
        line = line[:-(len(log['color']))]
        log['filler'] = line
        return log
    else:
        log['player'] = re.search('(.+?) ',line).group(0)[:-1]
        line = line[len(log['player'])+1:]
        tag=re.search('\[(.+?)\]',line)
        if tag:
            tag=len(tag.group(0))+2
        else:
            tag=1
        log['byPlayer'] = re.search('by (.+?)\.',line).group(0)[3:-(tag)]
        line = line[:line.find(log['byPlayer'])-1] + line[line.find(log['byPlayer'])+len(log['byPlayer'])+1:]
        log['filler'] = line
        return log
    
#gets all new lines from a log
def getNewLines(server):
    log = open(os.path.join(scriptDir, os.path.normpath(config['Paths'][server]), os.path.normpath(config['Paths']['log'])),'r').readlines()
    if int(config['Log Progress'][server]) <= log.index(log[-1])+1:
        toReturn = log[int(config['Log Progress'][server]):]
    else:
        toReturn = log[0:]
    config['Log Progress'][server] = str(log.index(log[-1])+1)
    return toReturn

#adds a line to the log
def log(line):
    if line['type'] == 'ban':
        lineToAdd = '%s [%s] %s was baned by %s' %(line['date'],config['Server Names'][line['server']],line['player'],line['byPlayer'])
    else:
        if line['type'][-1].lower() == 'e':
            lineToAdd = '%s [%s] %s was %s by %s\n' %(line['date'],config['Server Names'][line['server']],line['player'],(line['type']+'d').lower(),line['byPlayer'])
        else:
            lineToAdd = '%s [%s] %s was %s by %s\n' %(line['date'],config['Server Names'][line['server']],line['player'],(line['type']+'ed').lower(),line['byPlayer'])
    with open(filterlogPath, 'a') as log:
        log.write(lineToAdd)

#adds a player to the ban list
def addToSync(report):
    with open(syncPath, 'a+') as sync:
        sync.write(str(report)+'\n')

#removes a player from the ban list
def removeFromSync(player, type):
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

#reads the first ban list and saves to ban list (only used on first use)
def readBans():
    server = config['Other']['defaultserver']
    log = {}
    for line in open(os.path.join(scriptDir,os.path.normpath(config['Paths'][server]),os.path.normpath(config['Paths']['bans'])),'r').readlines():
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

#reads the first ban list and saves to ban list (only used on first use)
def readAdmins():
    server = config['Other']['defaultserver']
    for line in open(os.path.join(scriptDir,os.path.normpath(config['Paths'][server]),os.path.normpath(config['Paths']['admins'])),'r'):
        line = line[:-1]
        if re.search('"admins": (.+?)]',line):
            admins = ast.literal_eval(re.search('\[(.+?)\]',line).group(0))
    for player in admins:
        log = {}
        log['server'] = server
        log['type'] = 'PROMOTE'
        log['player'] = player
        addToSync(log)
        sync(log)

#runs a command on every server but the one it came from
def sync(command):
    for server in config['Server Names']:
        if server != command['server']:
            if command['type'] == 'BAN':
                subprocess.call(['service', config['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player'], command['reason'], command['byPlayer']])
            else:
                subprocess.call(['service', config['Map Names'][server], 'cmd', '/'+command['type'].lower(), command['player']])
        
#Startup on first run    
if config['Other']['firstTimeSetUp'] == 'true':
    config['Other']['firstTimeSetUp'] = 'false'
    banlist = open(syncPath, 'w')
    filterlog = open(filterlogPath, 'w')
    for server in config['Server Names']:
        config['Log Progress'][server] = '0'
    readBans()
    readAdmins()

#resycn one server due it being new
if config['Other']['newserver'].lower() != 'n/a':
    server = config['Other']['newserver']
    config['Other']['newserver'] = 'N/A'
    for line in open(syncPath,'r'):
        line = line[:-1]
        line = ast.literal_eval(re.search('{(.+?)}',line).group(0))
        if line['type'] == 'BAN':
            subprocess.call(['service', config['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player'], line['reason'], line['byPlayer']])
        else:
            subprocess.call(['service', config['Map Names'][server], 'cmd', '/'+line['type'].lower(), line['player']]) 

i = 1
if i == int(config['Other']['looptime']):
    i = i-1
while i != int(config['Other']['looptime']):
    i = i+1
    #Main Loop for script
    for server in config['Server Names']:
        makeLogOf = ['BAN','UNBAN','PROMOTE','DEMOTE']
        for line in getNewLines(server):
            line=line[:-1]
            line = decodeLog(line, server)
            if line['type'] in makeLogOf and line['byPlayer'] != '<server>':
                log(line)
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

    #Saves any config changes
    with open('syncConfig.ini', 'w') as configfile:
        config.write(configfile)
