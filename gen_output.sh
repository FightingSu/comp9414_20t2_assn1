#!/bin/bash

txt_files=`ls`
for i in $txt_files
do
    if [[ "$i" =~ "input".*"txt" ]]
    then
        printf "$i...\n"
        python3 fuzzyScheduler.py $i > ${i/input/output}
    fi
done