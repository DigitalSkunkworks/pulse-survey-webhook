#!/usr/bin/env python

# import urllib
import json
import os
from os import environ

from flask import Flask
from flask import request
from flask import make_response
# from flask import g

import sqlite3
import pypyodbc

# Flask app should start in global layout
from SurveyWebProject import app

# app = Flask(__name__)

# Global variables
global_debug = 'Y'
my_dir = os.path.dirname(__file__)

driver = os.environ.get('DRIVER', '')
server = os.environ.get('SERVER', '')
database = os.environ.get('DATABASE', '')
uid = os.environ.get('UID', '')
pwd = os.environ.get('PWD', '')


# Procedure used to output debug messages to the log
def debug(debugmsg):
    if global_debug is 'Y':
        print(debugmsg)


# Creates a connection to the SQLITE database (REMOVED due to new DB)
'''def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    debug('Inside create_connection')

    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return None'''


def ConnectDB():
    conString = ('Driver=' + driver +
                 'Server=' + server +
                 'Database=' + database +
                 'Uid=' + uid +
                 'Pwd=' + pwd)

    azcon = pypyodbc.connect(conString)
    return azcon


def insertDB(unit, area, role, team, department, account, company):
    cnxn = ConnectDB()
    crsr = cnxn.cursor()
    sql = """ INSERT INTO details (unit, area, role, team, department, account, company)
             VALUES (?,?,?,?,?,?,?) """
    crsr.execute(sql, (unit, area, role, team, department, account, company))
    cnxn.commit()
    crsr.close()
    cnxn.close()


def insertOtherDB(area):
    cnxn = ConnectDB()
    crsr = cnxn.cursor()

    if area == "":
        area = 'No value'

    sql = """ INSERT INTO misc (comment) VALUES (?) """
    crsr.execute(sql, (area,))
    cnxn.commit()
    crsr.close()
    cnxn.close()


def updateDB(comments, unit, area, role, team):
    cnxn = ConnectDB()
    crsr = cnxn.cursor()
    sql = """ UPDATE details SET comments = ?
             WHERE unit = ?
             AND area = ?
             AND role = ?
             AND team = ?
             AND date_created = (select max(date_created) from details)   """
    crsr.execute(sql, (comments, unit, area, role, team))
    cnxn.commit()
    crsr.close()
    cnxn.close()

def checkData(area):
    area_list = list()
    area_list.extend(['Digital', 'Workplace', 'VoIP', 'DPS', 'Other', 'PSO', 'PSD', 'TSD'])

    area_count = 0

    for x in area_list:
        if x == area:
            area_count += 1
        else:
            None

    return area_count


# Insert data from survey into sqlite database (REMOVED due to new DB)
"""def insert_survey_details(unit,area,role,team,department,account,company):
    debug('Inside insert_survey_details') #remove debug
    con = create_connection(database)
    cur = con.cursor()
    sql = '''INSERT INTO details (unit, area, role, team, department, account, company)
             VALUES (?,?,?,?,?,?,?) '''
    cur.execute(sql, (unit,area,role,team,department,account,company,))
    con.commit()
    con.close()

#Update record to append comments
def update_survey_details(comments,unit,area,role,team):
    debug('Inside update_survey_details') #remove debug
    con = create_connection(database)
    cur = con.cursor()
    sql = '''UPDATE details SET comments = ?
             WHERE unit = ?
             AND area = ?
             AND role = ?
             AND team = ?
             AND date_created = (select max(date_created) from details)  '''
    cur.execute(sql, (comments,unit,area,role,team,))
    con.commit()
    con.close()"""


def create_list(role, team, department, account, company):
    response_list = list()
    response_list.extend([role, team, department, account, company])
    return response_list


def generate_response(response_list):
    better_count = 0
    same_count = 0
    worse_count = 0
    error_count = 0
    for x in response_list:
        if x == 'Better':
            better_count += 1
        else:
            if x == 'Same':
                same_count += 1
            else:
                if x == 'Worse':
                    worse_count += 1
                else:
                    error_count += 1

    if better_count >= 3:
        speech = "We're pleased that you feel better overall, could you let us know why? (Press enter to submit)"
    else:
        if worse_count >= 3:
            speech = "We've noticed that you feel worse overall, could you let us know why? (Press enter to submit)"
            if error_count > 1:
                speech = 'Sorry, something has gone wrong. Please start again by refreshing this browser. Review the instructions below for further assistance.'
        else:
            speech = 'Please enter any other comments (Press enter to submit)'

            print(speech)

    return speech


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


# Extact parameters from the input JSON and pass to the insert procedure
def makeWebhookResult(req):
    #    if req.get("result").get("action") != "survey.complete":
    #       return {}
    result = req.get("result")
    parameters = result.get("parameters")

    if req.get("result").get("action") == "survey.complete":
        debug('UPDATE DB')
        unit = parameters.get("unit")
        area = parameters.get("area")
        role = parameters.get("role")
        team = parameters.get("team")
        comments = parameters.get("comments")
        updateDB(comments, unit, area, role, team)
        # updateDBDebug()
        speech = "Thanks for taking the pulse survey. Your responses have been recorded. Please close the browser to exit (API)"

    elif req.get("result").get("action") == "survey.initial":
        unit = parameters.get("unit")
        area = parameters.get("area")
        role = parameters.get("role")
        team = parameters.get("team")
        department = parameters.get("department")
        account = parameters.get("account")
        company = parameters.get("company")

        insertDB(unit, area, role, team, department, account, company)
        response_list = create_list(role, team, department, account, company)
        speech = generate_response(response_list)

    elif req.get("result").get("action") == "survey.area":
        area = parameters.get("area")
        error_count = checkData(area)
        if error_count == 0:
            speech = 'Sorry, something has gone wrong. Please start again by refreshing this browser. Review the instructions below for further assistance.'
            insertOtherDB(area)
        else:
            None

    else:
     return {}

    return {
        "speech": speech,
        "displayText": speech,
        # "data": {},
        # "contextOut": [],
        "source": "apiai-pulse-survey"
    }

# Required for Docker  # if __name__ == "__main__":  # app.run(host='0.0.0.0')

'''if __name__ == '__main__':
    HOST = environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)'''
