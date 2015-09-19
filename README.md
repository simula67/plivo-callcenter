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

1. Install dependencies
2. Create the tables necessary by running the following command(s)
```
create table calls ( id SERIAL PRIMARY KEY, calluuid VARCHAR(36), agent_sipusername VARCHAR(40) );
create table agents ( id SERIAL PRIMARY KEY, sipusername VARCHAR(40), busy boolean );   
create table call_stats ( id SERIAL PRIMARY KEY, duration INTEGER );
```
3. Set credentials like authentication token, database password and configuration values in environment variables
4. Run app.py

Some screenshots
================

Admin page

![Admin page](http://i.imgur.com/U8HMMaZ.png)

Agent page

![Agent page](http://i.imgur.com/pILGs8Y.png)


