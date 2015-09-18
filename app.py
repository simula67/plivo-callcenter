#!/usr/bin/python2

from flask import Flask,render_template, request, make_response, url_for
import plivo, plivoxml
import psycopg2
from conf import *

app = Flask(__name__)
app.debug = True
p = plivo.RestAPI(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN)

#TODO: Use SQLAlchemy
try:
    conn = psycopg2.connect("dbname='{}' user='postgres' host='{}' password='{}'".format(DB_NAME, DB_HOST, DB_PASSWD))
except:
    print "I am unable to connect to the database"

@app.route("/forward", methods=['POST', 'GET'])
def forward():
    return """<Response>
                        <Dial callerId="{}">
                            <User>sip:simula67150918103656@phone.plivo.com</User>
                        </Dial>
                    </Response>""".format(request.form['From'])

@app.route("/agent", methods=["GET", "POST"])
def agent():
    return render_template("agent_page.html")

@app.route("/answer", methods=['POST', 'GET'])
def answer():
    if request.method == "GET":
        return "You reached call center answer url"
    callUuid = request.form['CallUUID']
    print callUuid
    cur = conn.cursor()
    cur.execute("SELECT * from ongoing_calls")
    rows = cur.fetchall()
    if(len(rows) == 0):
        response = """<Response>
                        <Dial callerId="{}">
                            <User>sip:simula67150918103656@phone.plivo.com</User>
                        </Dial>
                    </Response>""".format(request.form['From'])
        active = 'true'
    else:
        # Put it in queue
        plivo_response = plivo.XML.Response()
        plivo_response.addSpeak("Our agent is busy. Please hold on")
        plivo_response.addPlay('https://s3.amazonaws.com/plivocloud/music.mp3', loop=1)
        response = make_response(render_template('response_template.xml', response=plivo_response))
        response.headers['content-type'] = 'text/xml'
        active = 'false'
    insert_cursor = conn.cursor()
    insert_new_sql = "INSERT INTO ongoing_calls (from_number, active, calluuid) VALUES('{}', '{}', '{}');".format(request.form['From'], active, callUuid)
    insert_cursor.execute(insert_new_sql)
    conn.commit()
    return response

@app.route("/hangup", methods=['POST', 'GET'])
def hangup():
    if request.method == "GET":
        return "You have reached the call center hangup url"

    is_active_call_sql = "select * from ongoing_calls where from_number='{}' AND active=true;".format(request.form['From'])
    cur = conn.cursor()
    cur.execute(is_active_call_sql)
    rows = cur.fetchall()
    cur.close()
    conn.commit()
    if(len(rows) != 0):
        # hung up call is the active one, transfer the first call to agent
        transfer_call_uuid_sql = "SELECT calluuid FROM ongoing_calls WHERE active=false ORDER BY id"
        transfer_call_cur = conn.cursor()
        transfer_call_cur.execute(transfer_call_uuid_sql)
        uuid_row = transfer_call_cur.fetchone()
        uuid = uuid_row[0]
        params = {
            'call_uuid' : uuid,
            'aleg_url': APP_URL + url_for("forward")
        }
        p.transfer_call(params)
        # Mark the call active
        update_table_sql = "UPDATE ongoing_calls SET active=true WHERE calluuid = {}".format(uuid)
        update_table_cursor = conn.cursor()
        update_table_cursor.execute(update_table_sql)
        conn.commit()

    # Delete the call from the database, it was hung up
    delete_sql = "DELETE FROM ongoing_calls WHERE from_number ='{}'".format(request.form['From'])
    delete_cur = conn.cursor()
    delete_cur.execute(delete_sql)
    conn.commit()
    return ""

app.run(host="0.0.0.0")
