#!/bin/bash

for f in csvs/*.csv
do
    mysql -e "LOAD DATA INFILE '"$f"' INTO TABLE issues 
      FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' IGNORE 1 LINES" 
      #generic username and password
      -u root --password= root ApacheIssues
echo "Done: '"$f"' at $(date)"
done