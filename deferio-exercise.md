# Health Verity Warehousing Exercise

### __Q1. You have a table in your data warehouse with 1,000, 000,000 records and 10 years of data. Each record has a "date" column. You need to indicate for upstream day of the week for each row, and flag US Holidays.__  
<br>

__A1.__ For a data warehouse of this size, one would want to normalize the data as best as possible. Normalization, in this context, would mean not repeating data that is not unique and simplifying data layout. 
- __Days of the week__, as in Monday through Sunday, could be assigned a code corresponding to the plain-english version (1: Monday, 2:Tuesday, etc.). A days_of_the_week table could be created with two columns: code (1,2,3, etc), and day_value (monday, tuesday, wednesday, etc). A single digit code was chosen for this table because it represents a miniscule amount of data that can be added to a large table without significantly increasing its size. In this case, we could add a field to the primary fact table indicating the corresponding day of the week code to the date value. The day_value could then be accessed with a lookup. Records in the primary table would have to be backfilled to populate the day of the week code, but this could be achieved relatively easily with an script.

- We could take a similar approach (to above) with __US Holidays__. There are publicly available datasets that contain US holiday data (including name, date, etc.), such as the following from [Microsoft](https://learn.microsoft.com/en-us/azure/open-datasets/dataset-public-holidays?tabs=azureml-opendatasets). This dataset spans the years 1970 - 2099, with data sourced from [Wikipedia](https://en.wikipedia.org/wiki/Category:Lists_of_public_holidays_by_country) and [PyPI Holidays](https://pypi.org/project/holidays/), and could be duplicated on local architecture. An additional field could be added to this holidays table to codify the unique holidays. Once dates in the fact table and the holidays table are standardized, one could run an update statement on the fact table to create a holiday flag or simply rely on search queries to determine associated holiday code.


|id|date|day_code|
|-|-|-|
|12345|2022-09-23 |5|
|67890|2022-09-24 |6| 

|day_code|day_value|
|-|-|
|5|friday|
|6|actsaturday|
<br>

### __Q2. Below are the most common query patterns that are being executed on this table by upstream. What partition strategy /any other solutions would you recommend?__

```SQL
--Query Pattern 1:
select count(distinct some_id) some_cnt, count(record_id) as record_cnt, attribute1, attribute2, date
from table
where date between {range of dates, usually across couple years} 
group by attribute1, attribute2, date;
```

<br>

__A2.__ If the attributes{1,2} are typically the same, one could use a vertical shard strategy to split the data by patterns of use. If specific fields are queried regularly, then it might make sense to devise a strategy to shard the fields that are not used that often away from those that are used more commonly.

<br>

### __Q3. You have a table with 4 columns (person_id, activity_start_date, activity_end_date, activity_code). Each person/activity have a start date and end date. Write a code (SQL or Python) to collapse "input" table on person level and create start/end across different activities (produce "output"). Dedup overlapping time periods. "Output time periods should be unique across activities, and do not overlap.__

<br>

### Input:
|person_id|activity_start_date|activity_end_date|activity_code|
|-|-|-|-|
|1|2/3/2021|2/30/2021|X1|
|1|2/15/2021|3/3/2021|X2|
|1|2/20/2021|2/21/2021|X3|
|1|3/15/2021|3/17/2021|X3|
|1|3/18/2021|3/20/2021|X4|

<br>

### Output:
|person_id|start_date|end_date|
|-|-|-|
|1|2/3/2021|3/3/2021|
|1|3/15/2021|3/20/2021|


<br>

__A3.__ 
```Python
import copy
import sqlite3
import datetime as dt
from pathlib import Path

db_path = Path('hv-exercise.sqlite3')
conn = sqlite3.connect(db_path, check_same_thread=False)


query = "select person_id, activity_start_date, activity_end_date from activities order by person_id, date(activity_start_date) asc;"
# query_limit = "select person_id, activity_start_date, activity_end_date from activities order by person_id, date(activity_start_date) asc limit 10000;"

cur = conn.cursor()
cur.execute(query)

results = cur.fetchall()

seen = {
    "person_id": "",
    "start_date": "",
    "end_date": ""
}
answer = []

def collapse_dates(records: tuple):
    """Collapse dates to dedup overlapping time periods
    Input: tuple of person_id, start_date, end_date

    return a dictionary with person_id, start_date, and end_date
    """
    pid, s, e = records
    try:
        start = dt.datetime.strptime(s, '%m/%d/%Y')
    except ValueError:
        start = dt.datetime.min
    try:
        end = dt.datetime.strptime(e, '%m/%d/%Y')
    except ValueError:
        end = dt.datetime.min
    
    if seen['person_id'] != pid:
        seen['person_id'] = pid
        seen['start_date'] = start
        seen['end_date'] = end
        return
    
    if seen['start_date'] == dt.datetime.min and start > dt.datetime.min:
        seen['start_date'] = start
    if seen['end_date'] == dt.datetime.min and end > dt.datetime.min:
        seen['end_date'] = end

    if (seen['start_date'] <= start <= seen['end_date']) and (end <= seen['end_date']):
        return  
    
    if (seen['start_date'] <= start <= seen['end_date']) and (end > seen['end_date']):
        seen['end_date'] = end
        return

    if start > seen['end_date']:
        start_fmt = dt.datetime.strftime(seen['start_date'], '%m/%d/%Y')
        end_fmt = dt.datetime.strftime(seen['end_date'], '%m/%d/%Y')
        
        seen['start_date'] = start_fmt
        seen['end_date'] = end_fmt
        answer.append(copy.deepcopy(seen))

        seen['start_date'] = start
        seen['end_date'] = end
        return


for record in results:
    collapse_dates(record)

seen['start_date'] = dt.datetime.strftime(seen['start_date'], '%m/%d/%Y')
seen['end_date'] = dt.datetime.strftime(seen['end_date'], '%m/%d/%Y')
answer.append(copy.deepcopy(seen))


print(answer)
```
The following code yields 3 response values. It was assumed that the 3/15 - 3/17 time period does not overlap with other time periods, contrary to the assignment example.

|person_id|start_date|end_date|
|-|-|-|
|1|2/3/202|3/3/2021|
|1|3/15/2021|3/17/2021|
|1|3/18/2021|3/20/2021|

This code is easy to apply. The result can be output to a file, or used to populate another table within the database. By tracking record indices, we can also minimize the data stored in memory and pull chunks with a `limit X` clause in our sql query (see: `query_limit` above). After each chunk is analyzed, we store the indices in a temporary table, and ensure that we dont pull those indices again with an accompanying `where` clause.

<br>

### __Q4. You have patient_diagnosis table and slowly-changing-dimension table for practitioners. Write a query to return all subsequent records for the patient after he was referred by active family practititoners to cargiologist__

<br>

```SQL
WITH referral AS (
	SELECT
		dx.*
	FROM
		patient_diagnosis dx
	LEFT JOIN dim_practitioner dm ON dx.practitioner_id = dm.practitioner_id
	LEFT JOIN dim_practitioner dm2 ON dx.referred_practitioner_id = dm2.practitioner_id
WHERE
	dm.practitioner_specialty = 'family practitioner'
	AND dm2.practitioner_id = 'cardiologist'
	AND (date(dm.effective_date_start) <= date(dx.date) <= date(dm.effective_date_end)))
	SELECT
		* FROM patient_diagnosis pd
	WHERE
		date(pd.date) > date(referral.date);
```

