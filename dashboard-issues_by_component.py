#!/usr/bin/env python

from stat_collector import Stat_Collector
from stat_grapher import Stat_Grapher

# Git credentials
git_user = ''
git_password = ''

# Plotly credentials
plotly_user = ''
plotly_api_key = ''

stream_ids = []  # Removed 7 keys
table_title = 'Tower 3.1: Issues by Component (High/Med)'
table_filename = 'tower_issues_by_component'

# Collect stats, stream data to graph
print "[Collecting stats]"
stats = Stat_Collector(git_user, git_password).get_issues_by_component(dummy_data=False)
print ""

print "[Graphing stats]"
Stat_Grapher(plotly_user, plotly_api_key, stream_ids).graph_issues_by_component(stats, build_table=False, table_title=table_title, table_filename=table_filename)
