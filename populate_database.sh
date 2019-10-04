#!/bin/bash

cd data/csvs

for f in *.csv
do
    mysql -uroot -proot -e "USE ApacheIssues LOAD DATA LOCAL INFILE '"$f"' INTO TABLE issues"
done

cd ..
cd ..