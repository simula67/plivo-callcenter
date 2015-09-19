#!/usr/bin/python2

from flask import Flask, render_template, request, make_response, url_for, redirect
import plivo
import psycopg2
from conf import *

"""

How does this work ?

We have two tables :

calls
+-----------+-----------+-------------------+
|           |           |                   |
| call_id   | calluuid  |agent_sipusername  |
|           |           |                   |
|           |           |                   |
+-----------+-----------+-------------------+

agents
+-----------+-------------+-------+
|           |             |       |
|           |             |       |
|agent_id   |sipusername  | busy  |
|           |             |       |
|           |             |       |
+-----------+-------------+-------+


agents table is prepopulated by admin

when new calls come in, we check if there is at least one agent free
if yes:
    pick a free agent and forward the call to agent
    insert new row into calls table with sipusername set to assigned agent
    mark the assigned agent in agents table as busy
else:
    insert new row into calls table with null agent_sipusername
    put the caller in wait mode

when a call is hung up, we check if the call was assigned to an agent ( non-null agent_sipusername field )
if yes:
    mark the agent in agents table as free
    transfer the oldest call to answer_url --> this will execute the new call algorithm above
delete the hung up call from the database

"""


app = Flask(__name__)
app.debug = True
p = plivo.RestAPI(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN)

# TODO: Use SQLAlchemy
try:
    conn = psycopg2.connect("dbname='{}' user='postgres' host='{}' password='{}'".format(DB_NAME, DB_HOST, DB_PASSWD))
except:
    print "I am unable to connect to the database"

@app.route("/answer", methods=['POST', 'GET'])
def answer():
    if request.method == "GET":
        return "You reached call center answer url"

    call_uuid = request.form['CallUUID']
    cursor = execute_query("SELECT * from agents WHERE busy='false'")
    if cursor.rowcount > 0:
        free_agent_sip_username = get_free_agent()
        mark_agent_busy(free_agent_sip_username)
        response = generate_forward_response(free_agent_sip_username)
    else:
        # Put it in queue
        free_agent_sip_username= None
        response = generate_queue_response()
    if free_agent_sip_username is None:
        execute_query("INSERT INTO calls (calluuid, agent_sipusername) VALUES('{}', {});".format(call_uuid, "NULL"))
    else:
        execute_query("INSERT INTO calls (calluuid, agent_sipusername) VALUES('{}', '{}');".format(call_uuid, free_agent_sip_username))
    return response

@app.route("/hangup", methods=['POST', 'GET'])
def hangup():
    if request.method == "GET":
        return "You have reached the call center hangup url"
    call_uuid = request.form['CallUUID']
    call_duration = request.form['Duration']
    # First, lets store some stats
    execute_query("INSERT INTO call_stats (duration) VALUES ({})".format(call_duration))
    # Now on with business
    cursor = execute_query("SELECT agent_sipusername FROM calls WHERE calluuid='{}' AND agent_sipusername IS NOT NULL".format(call_uuid))
    if cursor.rowcount > 0:
        # Hung up call was being handled by an agent. Mark him/her free
        agent_sipusername = cursor.fetchone()[0]
        execute_query("UPDATE agents SET busy='false' WHERE sipusername = '{}'".format(agent_sipusername))
        transfer_calluuid_cursor = execute_query("SELECT calluuid FROM calls WHERE calluuid not like '{}' AND agent_sipusername IS NULL ORDER BY id".format(call_uuid))
        if transfer_calluuid_cursor.rowcount > 0:
            # There is atleast one call that is in queue
            transfer_calluuid = transfer_calluuid_cursor.fetchone()[0]
            params = {
                'call_uuid': transfer_calluuid,
                'aleg_url': APP_URL + url_for("answer")
            }
            p.transfer_call(params)
            # Transferred call will get new uuid, So delete current one
            execute_query("DELETE FROM calls WHERE calluuid ='{}'".format(transfer_calluuid))
    # Delete the original call from the database, It was hung up
    execute_query("DELETE FROM calls WHERE calluuid ='{}'".format(call_uuid))
    return ""

@app.route("/queuelen", methods=["GET","POST"])
def queuelen():
    cursor = execute_query("SELECT count(*) FROM calls")
    return str(cursor.fetchone()[0])

@app.route("/agent", methods=["GET", "POST"])
def agent():
    return render_template("agent_page.html")

@app.route("/admin", methods=['POST', 'GET'])
def admin():
    if request.method == "GET":
        average_duration = execute_query("SELECT avg(DURATION) FROM call_stats;").fetchone()[0]
        available_sip_rows = execute_query("SELECT sipusername FROM agents").fetchall()
        available_sips = [i[0] for i in available_sip_rows]
        return render_template("admin_page.html", average_duration=average_duration, sips=available_sips)
    elif request.method == "POST":
        execute_query("INSERT INTO agents (sipusername, busy) VALUES ('{}', 'false')".format(request.form['sipusername']))
        return redirect(url_for('admin'))

def generate_forward_response(sip_username):
    plivo_response = plivo.XML.Response()
    plivo_response.addDial(callerId=request.form['From']).addUser("sip:" + sip_username + "@phone.plivo.com")
    response = make_response(render_template('response_template.xml', response=plivo_response))
    response.headers['content-type'] = 'text/xml'
    return response

def generate_queue_response():
    plivo_response = plivo.XML.Response()
    plivo_response.addSpeak("Our agents are busy. Please hold on")
    plivo_response.addPlay('https://s3.amazonaws.com/plivocloud/music.mp3', loop=1)
    response = make_response(render_template('response_template.xml', response=plivo_response))
    response.headers['content-type'] = 'text/xml'
    return response

def execute_query(query):
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    return cursor

def get_free_agent():
    cursor = execute_query("SELECT sipusername FROM agents where busy='false'")
    return cursor.fetchone()[0]

def mark_agent_busy(free_agent_sip_username):
    execute_query("UPDATE agents SET busy='true' WHERE sipusername='{}'".format(free_agent_sip_username))

app.run(host="0.0.0.0")
