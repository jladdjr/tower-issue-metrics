#!/usr/bin/env python

import sqlite3
from datetime import date, timedelta
import random

import plotly.plotly as py
import plotly.graph_objs as go

from stat_collector import Stat_Collector

# Github
GIT_USER = ''
GIT_PASSWORD = ''

# Database
DATABASE_PATH = 'issue_count.db'
CREATE_TABLE = False
ADD_TODAYS_ISSUE_COUNT = False

# Monte Carlo
NUM_SAMPLE_WEEKS = 2        # Simulations will be based on this many weeks of past performance
NUM_SIMULATIONS = 100000    # Number of Monte Carlo simulations
SAMPLE_CEILING = 365        # A given simulation will be cut off after reaching this value

# Plotly
PLOTLY_FILENAME = 'monte_carlo'

# Connect to database
conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

# Create table
if CREATE_TABLE:
    print("Create table")
    c.execute('''CREATE TABLE issues
                 (date date DEFAULT CURRENT_TIMESTAMP, ticket_count integer)''')
    conn.commit()

# Record today's issue count
if ADD_TODAYS_ISSUE_COUNT:
    print("Record today's issue count")
    # Get today's issue count
    collector = Stat_Collector(GIT_USER, GIT_PASSWORD)
    issue_count = collector.get_count_significant_issues()

    # Insert value into table
    c.execute('''INSERT INTO issues (ticket_count) VALUES (?)''', (issue_count,))
    conn.commit()

# Collect past performance
print("\nLoad past performance")
today = date.today()
day = timedelta(days=1)
previous_count = None
weekday_progress = []
weekend_progress = []
current_date = today
current_issue_count = None
for i in range(NUM_SAMPLE_WEEKS * 7 + 1):
    # Get ticket count for day
    dates = (current_date.strftime('%Y-%m-%d'), (current_date + day).strftime('%Y-%m-%d'))
    c.execute('''SELECT ticket_count FROM issues
                 WHERE date >= date(?) and date < date(?)
                 ORDER BY date ASC''', dates)
    count = c.fetchone()
    if not count:
        print "(Missing information for date)"
        count = previous_count
    else:
        count = count[0]

    # Store change
    if count and previous_count:
        change = previous_count - count
        if current_date.isoweekday() in range(1, 6):
            weekday_progress.append(change)
            print("Weekday: {0:%b %d}: {1}".format(current_date, change))
        else:
            weekend_progress.append(change)
            print("Weekend: {0:%b %d} - {1}".format(current_date, change))

    # Set today's issue count
    if count and not current_issue_count:
        current_issue_count = count

    previous_count = count
    current_date -= day

print("Weekday progress: {0}".format(weekday_progress))
print("Weekend progress: {0}".format(weekend_progress))

conn.close()

# Run monte carlo simulation
print("Run Monte Carlo simulation")
distribution = list()
for i in range(SAMPLE_CEILING):
    distribution.append(0)

for i in range(NUM_SIMULATIONS):
    issues_left = current_issue_count
    time_spent = 0
    current_day = date.today()
    while issues_left > 0 and time_spent < SAMPLE_CEILING:
        if current_day.isoweekday() in range(1, 6):
            issues_left += weekday_progress[random.randint(0, len(weekday_progress) - 1)]
        else:
            issues_left += weekend_progress[random.randint(0, len(weekend_progress) - 1)]
        time_spent += 1
        current_day += day

    # Only count result if simulation finished
    if time_spent != SAMPLE_CEILING:
        distribution[time_spent - 1] += 1

print "Distribution:"
current_day = date.today()
for i in range(SAMPLE_CEILING):
    print("{0:%b %d} - {1}".format(current_day, 100.0 * distribution[i] / NUM_SIMULATIONS))
    current_day += day

print "\nCumulative:"
current_day = date.today()
total = 0
x = []
y = []
for i in range(SAMPLE_CEILING):
    total += 100.0 * distribution[i] / NUM_SIMULATIONS
    x.append("{0:%Y-%m-%d}".format(current_day))
    y.append(total)
    print("{0:%b %d} - {1}".format(current_day, total))
    current_day += day

    if total > 99.9:
        break

trace = go.Scatter(x=x, y=y)
layout = dict(title = 'Tower 3.1: All Med/High Issues Closed',
              xaxis = dict(title = 'Date'),
              yaxis = dict(title = 'Cumulative Frequency (%)'),
              )
figure = dict(data=[trace], layout=layout)
plot_url = py.plot(figure, filename=PLOTLY_FILENAME, layout=layout)
print "Plot URL: {0}".format(plot_url)
