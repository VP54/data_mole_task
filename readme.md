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
1. Check if the repository_name is already in database
    i. in that case you should only retrieve new records otherwise, download whole data from the API
    (Why to download whole data for new repository? -> I have assumed that the users would also like to be able to see the history and in real case for example agriculture sensors, vendors or ML team would want data for other usage (BI, ML, Data Analysis etc.))
2. The app also checks rate limits as the app could potentially make more requests than permitted, resulting in connection errors from Streamline. 
    That is why this app checks requests left, stops if needed, and waits until it can start to request data again. (When not requesting data, data refreshing is done from database to ensure that the app is running. This approach could be useful for instance if we had multiple users with their own apps contribution to the database. There cannot be duplicates as the app filters them out).

3. UI is created simply with interactive tables in streamline. Why is that? Streamline is straightforward, lightweight, yet powerful library to crate PoC / simple product webpages.

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

