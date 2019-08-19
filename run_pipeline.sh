i=${1}
end=${2}

while [ $i -le $end ]; do
   cmd="python run_luigi.py SimplifyDocumentSchema --proposal-id=${i} "
   eval $cmd
   i=$(($i+1))
done

