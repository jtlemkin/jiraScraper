#!/usr/bin/env bash

projects=("ACCUMULO" "AMBARI" "HADOOP" "JCR" "LUCENE" "OOZIE")

for project in "${projects[@]}"
do
    echo "Processing ${project}"
    nohup python3 scraper.py $project &
done