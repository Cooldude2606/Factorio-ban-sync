import configparser, os, re, json
scriptDir = os.path.dirname(os.path.realpath('__file__'))
print(scriptDir)

masterconfig = configparser.ConfigParser()
masterconfig.read('masterconfig.ini')

relitiveScriptDir = os.path.join(scriptDir, os.path.normpath(masterconfig['Scripts']['log'][:-9]))
print(relitiveScriptDir)

config = configparser.ConfigParser()
config.read(os.path.join(relitiveScriptDir,'localconfig.ini'))

logPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['log']))
chatlogPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['chatlog']))
rawlogPath = os.path.join(relitiveScriptDir, os.path.normpath(config['Paths']['rawlog']))
print(logPath)
print(chatlogPath)
print(rawlogPath)

def rawLog(line):
    print('Writing to raw log')
    if not os.path.isfile(rawlogPath):
        file = json.dumps({},indent=2)
        file = json.loads(file)
    else:
        file = json.loads(open(rawlogPath, 'r').read())
    if not line['type'] in file:
        file[line['type']] = []
    file[line['type']].append(line)
    with open(rawlogPath,'w') as log:
        log.write(json.dumps(file,indent=2))

def removeFromStr(substring,string):
    if substring in string:
        if string.find(substring)-1 <0:
            return string[string.find(substring)+len(substring)+1:]
        else:
            return string[:string.find(substring)-1] + string[string.find(substring)+len(substring)+1:]
    else:
        return string

def decodeType(line):
    if re.search('\(shout\)',line):
        type = 'shout'
    elif re.search('\[(\D+?)\]',line):
        type = re.search('\[(\D+?)\]',line).group(0)[1:-1]
    else:
        type = 'system'
    return type

def decodeLine(line, server):
    log = {}
    log['server'] = server
    log['type'] = decodeType(line)
    line = removeFromStr(log['type'],line)
    log['type'] = log['type'].lower()
    if log['type'] == 'system':
        pass
    elif log['type'] == 'shout':
        print(line)
        if '<server>' in line:
            log['byplayertag'] = 'owner'
            log['byplayer'] = '<server>'
        else:
            log['byplayertag'] = tag=re.search('\[(.+?)\]',line).group(0)[1:-1]
            line = removeFromStr(log['byplayertag'],line)
            log['byplayer'] = re.search('(.+) :',line).group(0)[:-3]
            line = removeFromStr(log['byplayer'],line)
        log['message'] = re.search(': (.+)$',line).group(0)[2:]
    else:
        log['date'] = re.search('\d{4}-\d{2}-\d{2}',line).group(0)
        line = removeFromStr(log['date'],line)
        log['time'] = re.search('\d{2}:\d{2}:\d{2}',line).group(0)
        line = removeFromStr(log['time'],line)
        if log['type'] == 'chat':
            if '<server>' in line:
                log['byplayertag'] = 'owner'
                log['byplayer'] = '<server>'
            else:
                log['byplayertag'] = tag=re.search('\[(.+?)\]',line).group(0)[1:-1]
                line = removeFromStr(log['byplayertag'],line)
                log['byplayer'] = re.search('(.+?) :',line).group(0)[1:-3]
                line = removeFromStr(log['byplayer'],line)
            log['message'] = re.search(': (.+)$',line).group(0)[2:]
        elif log['type'] == 'ban':
            log['player'] = re.search('(.+?) ',line).group(0)[1:-1]
            line = removeFromStr(log['player'],line)
            if '<server>' in line:
                log['byplayertag'] = 'owner'
                log['byplayer'] = '<server>'
            else:
                log['byplayertag'] = tag=re.search('\[(.+?)\]',line).group(0)[1:-1]
                line = removeFromStr(log['byplayertag'],line)
                log['byplayer'] = re.search('by (.+?)\.',line).group(0)[3:-2]
                line = removeFromStr(log['byplayer'],line)
            log['reason'] = re.search('Reason: (.+?)\.',line).group(0)[8:-1]
        elif log['type'] ==  'unban' or log['type'] ==  'promote' or log['type'] ==  'demote':
            log['player'] = re.search('(.+?) ',line).group(0)[1:-1]
            line = removeFromStr(log['player'],line)
            if '<server>' in line:
                log['byplayertag'] = 'owner'
                log['byplayer'] = '<server>'
            else:
                log['byplayertag'] = tag=re.search('\[(.+?)\]',line).group(0)[1:-1]
                line = removeFromStr(log['byplayertag'],line)
                log['byplayer'] = re.search('by (.+?)\.',line).group(0)[3:-2]
        else:
            print('%s not decoded' %(log['type']))
            print(log)
            print(line)
    return log

def log(line):
    if line['type'] == 'ban':
        lineToAdd = '%s [%s] %s was baned by %s\n' %(line['date'],masterconfig['Server Names'][line['server']],line['player'],line['byplayer'])
    elif line['type'] == 'shout':
        lineToAdd = '[%s] %s %s: %s\n' %(masterconfig['Server Names'][line['server']],line['byplayer'],line['byplayertag'],line['message'])
    else:
        if line['type'][-1].lower() == 'e':
            lineToAdd = '%s [%s] %s was %s by %s\n' %(line['date'],masterconfig['Server Names'][line['server']],line['player'],(line['type']+'d').lower(),line['byplayer'])
        else:
            lineToAdd = '%s [%s] %s was %s by %s\n' %(line['date'],masterconfig['Server Names'][line['server']],line['player'],(line['type']+'ed').lower(),line['byplayer'])
    with open(logPath, 'a') as log:
        log.write(lineToAdd)

def logChat(line):
    if line['type'] == 'chat':
        lineToAdd = '%s %s %s %s %s: %s\n' %(line['date'],line['time'],masterconfig['Server Names'][line['server']],line['byplayer'],line['byplayertag'],line['message'])
    else:
        lineToAdd = '%s %s %s: %s\n' %(masterconfig['Server Names'][line['server']],line['byplayer'],line['byplayertag'],line['message'])
    with open(chatlogPath, 'a') as log:
        log.write(lineToAdd)

def getNewLines(server):
    log = open(os.path.join(scriptDir, os.path.normpath(masterconfig['Paths'][server]), os.path.normpath(masterconfig['Paths']['log'])),'r').readlines()
    if int(config['Log Progress'][server]) <= log.index(log[-1])+1:
        toReturn = log[int(config['Log Progress'][server]):]
    else:
        toReturn = log[0:]
    config['Log Progress'][server] = str(log.index(log[-1])+1)
    print('Got %s new lines' %(len(toReturn)))
    return toReturn

def readLogs():
    for server in config['Read From']:
        if config['Read From'][server] == 'true':
            print('Reading from',server)
            makeLogOf = ['ban','unban','promote','demote']
            for line in getNewLines(server):
                print(line[:-1])
                line = decodeLine(line,server)
                if line['type'] == 'chat' or line['type'] == 'shout':
                    logChat(line)
                elif line['type'] in makeLogOf and line['byplayer'] != '<server>':
                    log(line)
                if line['type'] == 'shout':
                    log(line)
                if line['type'] != 'system':
                    rawLog(line)
    print('Saveing config')
    with open(os.path.join(relitiveScriptDir,'localconfig.ini'), 'w') as configfile:
        config.write(configfile)
