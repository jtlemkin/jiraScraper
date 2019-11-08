#!/usr/bin/env bash

projects=("ACCUMULO" "AMBARI" "HADOOP" "JCR" "LUCENE" "OOZIE")

for project in "${projects[@]}"
do
    nohup python3 scraper.py $project s &
done