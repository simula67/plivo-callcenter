Plivo Call Center Application
=============================

This application is used to create a generic call center application using the Plivo platform.
Agents can receive calls by going to /agent URL. When clients call the number assosciated with the Plivo Application,
calls are forwarded to the agent. If there are more than one caller, they are put on hold until the call currently being
handled is hung up.

Demo
====

https://plivocallcenter.herokuapp.com/admin

https://plivocallcenter.herokuapp.com/agent

Call center number : +1 8552110703

How to run ?
============

Run the application
-------------------

1. Install dependencies
2. Create the tables necessary by running the following command(s)
```
create table calls ( id SERIAL PRIMARY KEY, calluuid VARCHAR(36), agent_sipusername VARCHAR(40) );
create table agents ( id SERIAL PRIMARY KEY, sipusername VARCHAR(40), busy boolean );   
create table call_stats ( id SERIAL PRIMARY KEY, duration INTEGER );
```
3. Set credentials like authentication token, database password and configuration values in environment variables
4. Run app.py

Configure Plivo Application
----------------------------
1. Create an application in Plivo
2. Set the answer URL and hangup URL to that of "/answer" and "/hangup" of the hosted application created in the above subsection 
3. Buy a number from Plivo and assign it to the Plivo application created above


After this you can buy sip endpoints from Plivo and insert it into the call center application from the admin page.
Calls made to the number bought from Plivo will get forwarded to the agents.
Please note that when usernames are inserted into the database, calls are made to sip://username@phone.plivo.com.

Some screenshots
================

Admin page

![Admin page](http://i.imgur.com/NHxpRMu.png)

Agent page

![Agent page](http://i.imgur.com/pILGs8Y.png)


