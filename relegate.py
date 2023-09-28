import csv
import os
import random
import sqlite3
import tempfile

TSWP_MAX = 446
IND_CONF_NAME = 'Independent'
DB_PATH = os.path.join(tempfile.gettempdir(), "relegate.db")
MAX_SWOR = -1

filePaths = {}

def readCSV(csvPath):
    result = dict(headers=[], data=[])
    with open(csvPath, 'r', newline='') as csvFile:
        reader = csv.DictReader(csvFile)
        result['headers'] = reader.fieldnames
        for idx, k in enumerate(result['headers']):
            if k.islower():
                result['headers'][idx] = f"{k}_"
        for row in reader:
            result['data'].append(row)
    return result

def writeCSV(csvHeaders, csvTuples, csvPath):
    with open(csvPath, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(csvHeaders)
        writer.writerows(csvTuples)


def getFilePaths():
    result = {}
    result['COCH'] = input("Please enter the path to your COCH csv file: ")
    result['TEAM'] = input("Please enter the path to your TEAM csv file: ")
    result['CONF'] = input("Please enter the path to your CONF csv file: ")
    result['DIVI'] = input("Please enter the path to your DIVI csv file: ")
    result['TSWP'] = input("Please enter the path to your TSWP csv file: ")
    return result

def loadInputs(csvPaths):
    cochDict = readCSV(csvPaths['COCH'])
    teamDict = readCSV(csvPaths['TEAM'])
    confDict = readCSV(csvPaths['CONF'])
    diviDict = readCSV(csvPaths['DIVI'])
    tswpDict = readCSV(csvPaths['TSWP'])

    try:
        os.remove(DB_PATH)
    except OSError:
        pass

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(f"CREATE TABLE COCH({','.join(cochDict['headers'])})")
    cur.execute(f"CREATE TABLE TEAM({','.join(teamDict['headers'])})")
    cur.execute(f"CREATE TABLE CONF({','.join(confDict['headers'])})")
    cur.execute(f"CREATE TABLE DIVI({','.join(diviDict['headers'])})")
    cur.execute(f"CREATE TABLE TSWP({','.join(tswpDict['headers'])})")

    cur.executemany(f"INSERT INTO COCH VALUES(:{', :'.join(cochDict['headers'])})", cochDict['data'])
    cur.executemany(f"INSERT INTO TEAM VALUES(:{', :'.join(teamDict['headers'])})", teamDict['data'])
    cur.executemany(f"INSERT INTO CONF VALUES(:{', :'.join(confDict['headers'])})", confDict['data'])
    cur.executemany(f"INSERT INTO DIVI VALUES(:{', :'.join(diviDict['headers'])})", diviDict['data'])
    cur.executemany(f"INSERT INTO TSWP VALUES(:{', :'.join(tswpDict['headers'])})", tswpDict['data'])

    con.commit()
    MAX_SWOR = cur.execute("SELECT MAX(swor) FROM TSWP;").fetchone()[0]
    con.close()

def findRelegates(numRelegate):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Find power conference IDs
    powerConfIdRes = cur.execute(f"SELECT cgid FROM conf WHERE cprs='3' AND NOT cnam='{IND_CONF_NAME}';").fetchall()
    powerConfIds = {}
    for idTup in powerConfIdRes:
        powerConfIds[idTup[0]] = {'wins': {'total': -1, 'index': -1}, 'teams': []}
        coachQuery = cur.execute(f"SELECT coch.cswi, coch.tgid, team.cgid, team.dgid FROM coch JOIN team ON coch.tgid=team.tgid WHERE coch.ptid='511' AND team.cgid='{idTup[0]}' ORDER BY coch.cswi;")
        coachRes = coachQuery.fetchall()
        for coach in coachRes:
            if len(powerConfIds[idTup[0]]['teams']) == numRelegate:
                if powerConfIds[idTup[0]]['wins']['total'] > int(coach[0]):
                    powerConfIds[idTup[0]]['teams'][powerConfIds[idTup[0]]['wins']['index']] = coach
                    powerConfIds[idTup[0]]['wins']['total'] = int(coach[0])
                    for idx, team in enumerate(powerConfIds[idTup[0]]['teams']):
                        if int(team[0]) > powerConfIds[idTup[0]]['wins']['total']:
                            powerConfIds[idTup[0]]['wins'] = {'total': int(team[0]), 'index': idx}
            else:
                powerConfIds[idTup[0]]['teams'].append(coach)
                if len(powerConfIds[idTup[0]]['teams']) == numRelegate:
                    for idx, team in enumerate(powerConfIds[idTup[0]]['teams']):
                        if int(team[0]) > powerConfIds[idTup[0]]['wins']['total']:
                            powerConfIds[idTup[0]]['wins'] = {'total': int(team[0]), 'index': idx}
    con.close()
    return powerConfIds

def findPromotions(numPromote):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Find group conference ids
    groupConfIdRes = cur.execute("SELECT cgid FROM conf WHERE cprs='2' OR cprs='1';").fetchall()
    groupConfIds = {'wins': {'total': -1, 'index': -1}, 'teams': []}
    for idTup in groupConfIdRes:
        coachQuery = cur.execute(f"SELECT coch.cswi, coch.tgid, team.cgid, team.dgid FROM coch JOIN team ON coch.tgid=team.tgid WHERE coch.ptid='511' AND team.cgid='{idTup[0]}' ORDER BY coch.cswi DESC;")
        coachRes = coachQuery.fetchall()
        for coach in coachRes:
            if len(groupConfIds['teams']) == numPromote:
                if groupConfIds['wins']['total'] < int(coach[0]):
                    groupConfIds['teams'][groupConfIds['wins']['index']] = coach
                    groupConfIds['wins']['total'] = int(coach[0])
                    for idx, team in enumerate(groupConfIds['teams']):
                        if int(team[0]) < groupConfIds['wins']['total']:
                            groupConfIds['wins']['total'] = int(team[0])
                            groupConfIds['wins']['index'] = idx
            else:
                groupConfIds['teams'].append(coach)
                if len(groupConfIds['teams']) == numPromote:
                    groupConfIds['wins'] = {'total': int(coach[0]), 'index': numPromote - 1}
                    for idx, team in enumerate(groupConfIds['teams']):
                        if int(team[0]) < groupConfIds['wins']['total']:
                            groupConfIds['wins']['total'] = int(team[0])
                            groupConfIds['wins']['index'] = idx
    con.close()
    return groupConfIds

def swapTeams(relegateTeam, promoteTeam):
    global MAX_SWOR
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    MAX_SWOR = MAX_SWOR + 1
    relegateTeamInfo = cur.execute(f"SELECT team.tdna, conf.cnam, divi.dnam FROM team JOIN conf ON team.cgid=conf.cgid LEFT JOIN divi ON team.dgid=divi.dgid WHERE team.tgid='{relegateTeam[1]}';").fetchone()
    promoteTeamInfo = cur.execute(f"SELECT team.tdna, conf.cnam, divi.dnam FROM team JOIN conf ON team.cgid=conf.cgid LEFT JOIN divi ON team.dgid=divi.dgid WHERE team.tgid='{promoteTeam[1]}';").fetchone()
    print(f"Relegating {relegateTeamInfo[0]} to {promoteTeamInfo[1]} conference and division {promoteTeamInfo[2]}")
    print(f"Promoting {promoteTeamInfo[0]} to {relegateTeamInfo[1]} conference and division {relegateTeamInfo[2]}")
    cur.execute(f"INSERT INTO tswp (tgid, tidr, swor) VALUES('{relegateTeam[1]}', '{promoteTeam[1]}', '{MAX_SWOR}')")
    cur.execute(f"UPDATE team SET cgid = '{relegateTeam[2]}', dgid = '{relegateTeam[3]}' WHERE tgid = '{promoteTeam[1]}';")
    cur.execute(f"UPDATE team SET cgid = '{promoteTeam[2]}', dgid = '{promoteTeam[3]}' WHERE tgid = '{relegateTeam[1]}';")
    con.commit()
    con.close()

def relegate():
    global MAX_SWOR
    global TSWP_MAX
    numRelegate = int(input("How many teams per power conference should be relegated? "))
    powerConfIds = findRelegates(numRelegate)
    numPromote = numRelegate * len(powerConfIds.keys())
    if MAX_SWOR + numPromote + 1 > TSWP_MAX:
        print("WARNING! You've reached the max number of team swaps in this save.  Cancelling promotion.")
        exit(1)
    groupConfIds = findPromotions(numPromote)
    random.shuffle(groupConfIds['teams'])
    for conf in powerConfIds:
        for team in powerConfIds[conf]['teams']:
            swapTeams(team, groupConfIds['teams'].pop())

def saveCSV(csvPaths):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    teamCol = cur.execute('PRAGMA table_info(team);').fetchall()
    teamData = cur.execute("SELECT * FROM team;").fetchall()
    teamHeaders = []
    for teamHead in teamCol:
        if teamHead[1].endswith('_'):
            teamHeaders.append(teamHead[1][:-1])
        else:
            teamHeaders.append(teamHead[1])
    writeCSV(teamHeaders, teamData, f"{csvPaths['TEAM']}.new.csv")

    tswpCol = cur.execute('PRAGMA table_info(tswp);').fetchall()
    tswpData = cur.execute("SELECT * FROM tswp;").fetchall()
    tswpHeaders = []
    for tswpHead in tswpCol:
        tswpHeaders.append(tswpHead[1])
    writeCSV(tswpHeaders, tswpData, f"{csvPaths['TSWP']}.new.csv")

if __name__ == "__main__":
    csvPaths = getFilePaths()
    loadInputs(csvPaths)
    relegate()
    saveCSV(csvPaths)
