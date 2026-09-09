#!/bin/bash

# This script is used to split the huge sample
# file into tiny 20MB pieces to speed up preparsing
#
# Author  ==> <paulo-a-gil@alticelabs.com>
# Version ==> 2.0
#
# "Não há soluções triviais para problemas complexos"

# Check for indir
if [ -z "$1" ]; then
	echo -e "ERROR: Please supply input directory!"
	echo -e "Usage: $0 <indir> <outdir>"
	exit 1
fi

# Check for outdir
if [ -z "$2" ]; then
	echo -e "ERROR: Please supply output directory!"
	echo -e "Usage: $0 <indir> <outdir>"
	exit 1
fi

# Human readable variables
indir=$1
outdir=$2

# Checks if indir is well formed
lastChar=${indir: -1}
if [[ lastChar != "/" ]]; then
	indir="$indir/"
fi

# Checks if outdir is well formed
lastChar=${outdir: -1}
if [[ lastChar != "/" ]]; then
	outdir="$outdir/"
fi

# cd into input directory
cd $indir

while IFS= read -r -d $'\0' fileName; do
	folder=$(basename $fileName .xml)
	file=$(basename $fileName)
	echo "Splitting file $file"
	mkdir=$(mkdir $outdir$folder)
	split=$(split -d -b 20MB -a 5 $file $file.)
	mv=$(mv $file.* $outdir$folder/)
done < <(find "$indir" -maxdepth 2 -type f -iname "*.xml" -print0 2> /dev/null)
