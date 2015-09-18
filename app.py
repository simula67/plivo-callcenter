#!/usr/bin/python2

from flask import Flask, render_template, request, make_response, url_for
import plivo, plivoxml
import psycopg2
from conf import *

app = Flask(__name__)
app.debug = True
p = plivo.RestAPI(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN)

# TODO: Use SQLAlchemy
try:
    conn = psycopg2.connect("dbname='{}' user='postgres' host='{}' password='{}'".format(DB_NAME, DB_HOST, DB_PASSWD))
except:
    print "I am unable to connect to the database"


@app.route("/forward", methods=['POST', 'GET'])
def forward():
    return generate_forward_response()


@app.route("/agent", methods=["GET", "POST"])
def agent():
    return render_template("agent_page.html")


@app.route("/answer", methods=['POST', 'GET'])
def answer():
    if request.method == "GET":
        return "You reached call center answer url"

    callUuid = request.form['CallUUID']
    cursor = execute_query("SELECT * from ongoing_calls")
    rows = cursor.fetchall()
    if (len(rows) == 0):
        response = generate_forward_response()
        active = 'true'
    else:
        # Put it in queue
        plivo_response = plivo.XML.Response()
        plivo_response.addSpeak("Our agent is busy. Please hold on")
        plivo_response.addPlay('https://s3.amazonaws.com/plivocloud/music.mp3', loop=1)
        response = make_response(render_template('response_template.xml', response=plivo_response))
        response.headers['content-type'] = 'text/xml'
        active = 'false'
    execute_query("INSERT INTO ongoing_calls (from_number, active, calluuid) VALUES('{}', '{}', '{}');".format(
        request.form['From'], active, callUuid))
    return response


@app.route("/hangup", methods=['POST', 'GET'])
def hangup():
    if request.method == "GET":
        return "You have reached the call center hangup url"

    active_calls_from_number_cursor = execute_query(
        "select * from ongoing_calls where from_number='{}' AND active=true;".format(request.form['From']))
    rows = active_calls_from_number_cursor.fetchall()
    active_calls_from_number_cursor.close()
    if (len(rows) != 0):
        # hung up call is the active one, transfer the first incoming call to agent
        transfer_call_cur = execute_query("SELECT calluuid FROM ongoing_calls WHERE active=false ORDER BY id")
        uuid_row = transfer_call_cur.fetchone()
        if not uuid_row is None:
            uuid = uuid_row[0]
            params = {
                'call_uuid': uuid,
                'aleg_url': APP_URL + url_for("forward")
            }
            p.transfer_call(params)
            # Mark the call active
            execute_query("UPDATE ongoing_calls SET active=true WHERE calluuid = '{}'".format(uuid))

    # Delete the call from the database, it was hung up
    execute_query("DELETE FROM ongoing_calls WHERE from_number ='{}'".format(request.form['From']))
    return ""

def execute_query(query):
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    return cursor

def generate_forward_response():
    return """<Response>
                    <Dial callerId="{}">
                        <User>sip:{}@phone.plivo.com</User>
                    </Dial>
               </Response>""".format(request.form['From'], SIP_USERNAME)

app.run(host="0.0.0.0")
