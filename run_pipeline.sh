i=${1}
end=${2}

while [ $i -le $end ]; do
   cmd="python3 run_luigi.py SimplifyDocumentSchema --proposal-id=${i} "
   echo $cmd
   eval $cmd
   i=$(($i+1))
done

