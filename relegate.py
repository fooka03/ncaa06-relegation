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
    result['TEAM'] = input("Please enter the path to your TEAM csv file: ")
    result['CONF'] = input("Please enter the path to your CONF csv file: ")
    result['DIVI'] = input("Please enter the path to your DIVI csv file: ")
    result['TSWP'] = input("Please enter the path to your TSWP csv file: ")
    return result

def loadInputs(csvPaths):
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
    cur.execute(f"CREATE TABLE TEAM({','.join(teamDict['headers'])})")
    cur.execute(f"CREATE TABLE CONF({','.join(confDict['headers'])})")
    cur.execute(f"CREATE TABLE DIVI({','.join(diviDict['headers'])})")
    cur.execute(f"CREATE TABLE TSWP({','.join(tswpDict['headers'])})")

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
        powerConfIds[idTup[0]] = cur.execute(f"SELECT tgid, cgid, dgid, tscs_ FROM team WHERE cgid='{idTup[0]}' ORDER BY CAST(tscs_ AS INTEGER) DESC LIMIT {numRelegate};").fetchall()
    con.close()
    return powerConfIds

def findPromotions(numPromote):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Find group conference ids
    groupConfIdRes = cur.execute("SELECT cgid FROM conf WHERE cprs IN ('2', '1');").fetchall()
    groupConfIds = []
    for id in groupConfIdRes:
        groupConfIds.append(id[0])
    joinStr = "', '"
    groupConfIdString = f"'{joinStr.join(groupConfIds)}'"
    teamRes = cur.execute(f"SELECT tgid, cgid, dgid, tscs_ FROM team WHERE cgid IN ({groupConfIdString}) ORDER BY CAST(tscw_ AS INTEGER) DESC LIMIT {numPromote};").fetchall()

    con.close()
    return teamRes

def swapTeams(relegateTeam, promoteTeam):
    global MAX_SWOR
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    MAX_SWOR = MAX_SWOR + 1
    relegateTeamInfo = cur.execute(f"SELECT team.tdna, conf.cnam, divi.dnam FROM team JOIN conf ON team.cgid=conf.cgid LEFT JOIN divi ON team.dgid=divi.dgid WHERE team.tgid='{relegateTeam[0]}';").fetchone()
    promoteTeamInfo = cur.execute(f"SELECT team.tdna, conf.cnam, divi.dnam FROM team JOIN conf ON team.cgid=conf.cgid LEFT JOIN divi ON team.dgid=divi.dgid WHERE team.tgid='{promoteTeam[0]}';").fetchone()
    print(f"Relegating {relegateTeamInfo[0]} to {promoteTeamInfo[1]} conference and division {promoteTeamInfo[2]}")
    print(f"Promoting {promoteTeamInfo[0]} to {relegateTeamInfo[1]} conference and division {relegateTeamInfo[2]}")
    print("")
    cur.execute(f"INSERT INTO tswp (tgid, tidr, swor) VALUES('{relegateTeam[0]}', '{promoteTeam[0]}', '{MAX_SWOR}')")
    cur.execute(f"UPDATE team SET cgid = '{relegateTeam[1]}', dgid = '{relegateTeam[2]}' WHERE tgid = '{promoteTeam[0]}';")
    cur.execute(f"UPDATE team SET cgid = '{promoteTeam[1]}', dgid = '{promoteTeam[2]}' WHERE tgid = '{relegateTeam[0]}';")
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
    random.shuffle(groupConfIds)
    for conf in powerConfIds:
        for team in powerConfIds[conf]:
            swapTeams(team, groupConfIds.pop())

def saveCSV(csvPaths):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    teamData = cur.execute("SELECT cgid, dgid FROM team;").fetchall()
    teamHeaders = ['CGID', 'DGID']
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
