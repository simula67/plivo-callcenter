Plivo Call Center Application
=============================

This application is used to create a generic call center application using the Plivo platform.
Agents can receive calls by going to /agent URL. When clients call the number assosciated with the Plivo Application,
calls are forwarded to the agent. If there are more than one caller, they are put on hold until the call currently being
handled is hung up.


How to run ?
============

1. Set the APP_URL, DB_HOST and DB_NAME in conf.py
2. Install dependencies
3. Create the tables necessary by running the following command(s)

    create table ongoing_calls ( id SERIAL PRIMARY KEY, calluuid VARCHAR(36), from_number VARCHAR(15), active boolean );

4. Set credentials like authentication token etc in environment variables
5. Run app.py

