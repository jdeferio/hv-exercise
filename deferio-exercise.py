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

    
