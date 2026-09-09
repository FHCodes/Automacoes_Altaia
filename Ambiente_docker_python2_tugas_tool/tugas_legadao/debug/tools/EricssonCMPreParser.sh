#!/bin/bash

# This script is used to automate the whole
# preparsing process
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
	echo -e "ERROR: Please supply outdir directory!"
	echo -e "Usage: $0 <indir> <outdir>"
	exit 1
fi

# Human readable variables
indir=$1
outdir=$2

# Create outdir folder if not exists
mkdir -p $outdir

# Split original file into tiny pieces
bash /opt/alticelabs/namf/tools/splitEricssonCmFile.sh $indir $outdir

# Get MeContext files from those pieces
bash /opt/alticelabs/namf/tools/generateMeContext.sh $outdir

# Call JAR to finish PreParsing process
/usr/bin/java -jar /opt/alticelabs/namf/tools/EricssonCMPreParser.jar --indir $indir --outdir $outdir -v

# Remove MeContext files after calling the PreParser JAR
cd $outdir
rm -r */
