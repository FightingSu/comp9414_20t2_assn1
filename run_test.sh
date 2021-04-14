prefix=""
if [[ "$1" == "test_others" ]]
then
    cd ./others_test_case
    prefix="../"
fi

for i in `ls`
do
    if [[ "$i" =~ "input".*".txt" ]] 
    then
        printf "\n\n     testing file: %s\n" $i
        fuzzyScheduler=`python3 "$prefix"fuzzyScheduler.py $i`
        primitiveFuzzyScheduler=`python3 "$prefix"primitiveFuzzyScheduler.py $i`

        if [[ "$primitiveFuzzyScheduler" == "$fuzzyScheduler" ]] 
        then
            printf "Same output!\n\n"
            printf "%s\n" "$fuzzyScheduler"
        else
            printf "Different output!\n"

            printf "\nfuzzySchduler:\n\n%s" "$primitiveFuzzyScheduler"
            printf "\n\nadvanced_searcher:\n\n%s" "$fuzzyScheduler"
        fi
        printf "\n_________ test ended _________\n\n"
    fi
done