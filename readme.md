## The App

Tech Stack:
    - FastAPI (backend)
    - Streamlit (simple UI)
    - Pandas (data processing)
    - MongoDB (database)

## Database consideration

I considered both SQL and NoSQL databases. I decided to use NoSQL database because of few things:
1. Schema of things that user wants to monitor can vary in time (new API features/ new client desires)
2. NoSQL database has faster read/write
3. Due to nature of task I do not want to join tables but need faster selects.

Because of those reasons I chose NoSQL database. MongoDB was just because I wanted to try out something new.

## My implementation considerations
1. I tried to make the app as simple as possible, there are things as pydantic models, Factory pattern for requests / Database clients, but as a proof of concept I tried to keep things simple (KISS).

2. Due to not having to deal with much data (2500 rows max) I did not see the need to use lazy evaluation data processing libraries such as (polars, PySpark). To increase code efficiency I did not use pandas pre-written drivers for writing to database as converting arrays to dataframe every time would be likely slightly slower. 

3. I also tried not to create excessive not-at-this-moment-needed functionality, because I try not the build things, that people are not going to need (YANGNI). 

4. For better readability I type-hinted, where it was possible. I also added simple class and methods documentation in the code.

## Minimization of API calls
I minimized calls primarily by storing already seen data to database. I also wanted to save API calls using webhooks, but the API
would not let me use them unless I am owner of the repository. This would save me having to update my data periodically.

## Logic
I have built simple FastAPI backend which add data to the database as needed and returns data needed for analysis.
The criteria, which the app adheres to can be described as follows:
1. User sends requests with data parameter
    i. for every repository name app checks if data is already in databaes if it is, it only retrieves new records otherwise, downloads whole data from the API
    (Why to download whole data for new repository? -> I have assumed that the users would also like to be able to see the history and in real case for example agriculture sensors, vendors or ML team would want data for other usage (BI, ML, Data Analysis etc.))
3. The app also checks rate limits as the app could potentially make more requests than permitted. 
    That is why this app checks requests left, stops if needed, and waits until it can start to request data again. (One improvement could be that only getting data from github will stop but user can still get data from database (I have developed it when using Streamlit for UI, but that deviated from task description so changed it back to adhere to more normal REST API))

## Other possible solutions:
1. If we considered not caring about storing the data, production costs and some efficiency could be improved by not using the database at all. Given some simple heuristic for refreshing data we can query maximally 500 data entries per requests, which is simultaneously the max amount from task definition, by simply querying the data and passing it to the UI, we can remove the step of writing and reading the data from database. For repositories, that have not been tracked recently, but have been in past, we could (given we can query maximally 500 events) simply query the data from the API and behave as if they were never considered. Not needing to host Database, we could lower our service costs, maintenance costs and improve development speed somewhere, where its needed more.

## Room for improvement:
- API calls could be done asynchronously and the rate limiting logic use something as Semaphore to first determine the max amount requests it can utilize.
- I have not tested the code, as testing was done mainly by trying out different scenarios. Testing should be implemented.
- There also should be some sort of fault-handling to make sure the app is robust. Although the app will not break if it meets for example type in repository name, 
some logging could improve robustness of application.
- If needed for some reason, the data could be trained on and model for event prediction could be created to further help guide some intuition, what activity can end user expect. Again, that would probably be helpful for instance of predictive maintenance of agriculture tools/machinery as it is warranted to know about high likelihood of failure before the tool is damaged (which decreases the production efficiency)

- I store the raw data from github in database right now, there is possibility, that when data is being stored I could have already created features for monitoring. I did not choose to do that for following reasons:
1. The date features for UI have to be transformed, but in order to use DateTypes in filtering / creating features it would be needed to retype features before using it fot analytics
2. Since the data processing part of the app is quite small (2500 rows max), I would rather compute the features "on the go", because monitoring app features can change quite a lot and that would introduce sparse data in MongoDB. That could lead to messy schema and many not-anymore-used features, that get NaN values and are useless. Computing on the go seems more versatile and lightweight approach. However if the data processing part was quite big I would definitely precompute my features.

## Other documentation
API documents can be found by searching hosting page and adding /docs such as: 0.0.0.0:8000/docs. There can be found documentation about endpoints. Documentation of code can be found in docstrings.
files:
analytics.py - performs rolling statistics
github.py - has class and methods to communicate with github api and I/O to database
mongo_db.py - class to communicate with MongoDB database
models.py - has database factory abstractclass
main.py - defines endpoints

## Word of caution
I have worked mainly on cloud, where project structure and setup is given by cloud, so this might not be ideal or someone would do it differently, for that I am sorry, but have not had the chance to do
so. To run the application just type: uvicorn main:app --host 0.0.0.0 --port 80 . 
Database can be accessible by everyone and connection string is in main.py. (THIS WOULD NOT OBVIOUSLY BE DONE IN REAL SETTINGS, BUT FOR THIS USE CASE I LET IT THERE)

## OTHER
I have also implemented Streamlit UI that was interactive and communicated with backend, but due to specifications about the task I change it back to backend app. I can prepare and show the app in-person :). 
 
