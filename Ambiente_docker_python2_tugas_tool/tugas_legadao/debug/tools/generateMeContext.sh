#!/bin/bash

function generateMeContext() {
	# Initialize fileId variable
	unset fileName

	for i in {0..10000}
	do
		# Format number
		if [ $i -lt 10 ]; then
			n="0000$i"	
		elif [ $i -lt 100 ]; then
			n="000$i"
		elif [ $i -lt 1000 ]; then
			n="00$i"
		elif [ $i -lt 10000 ]; then
			n="0$i"
		fi
		
		# Check if formed file exists
		file="$1.$n"
		if [ -f "$file" ]; then
			echo "Processing $file"
		else
			return 1
		fi
		
		# Get current file opening and closing tags
		start=$(cat -n $file | grep '<xn:MeContext id="*"' | awk '{print $1}')
		end=$(cat -n $file | grep '</xn:MeContext>' | awk '{print $1}')

		# Get number of lines for current file
		numLines=$(awk 'END {print NR}' $file)

		# Convert lists to arrays
		start=($start)
		end=($end)
		list=()

		# If no start or end tags are found append to last known file
		if [ ${#start[@]} -eq 0 ]; then
			if [ ${#end[@]} -eq 0 ]; then
				if [ -z "$fileName" ]; then
					echo "No MeContext found on file $file"
				else
					write=$(cat $file >> $fileName)
				fi
			fi
		fi

		# Shift start/end values to include beggining of file
		if [ ${#start[@]} -gt 0 ]; then
			if [ ${#end[@]} -gt 0 ]; then
				if [ ${end[0]} -lt ${start[0]} ]; then
					item=${end[0]}
					list+=("1:$item")
					end=(${end[@]:1})
				fi
			fi
		fi
		
		# Parse start/end arrays and create list with pairs
		if [ ${#start[@]} -eq 0 ]; then
			for idx in ${!end[@]}
			do
				if [ -z "${start[$idx]}" ]; then
					list+=("1:${end[$idx]}")
				else
					list+=("${start[$idx]}:${end[$idx]}")
				fi
			done
		else
			for idx in ${!start[@]}
			do
				if [ -z "${end[$idx]}" ]; then
					list+=("${start[$idx]}:$numLines")
				else
					list+=("${start[$idx]}:${end[$idx]}")
				fi
			done
		fi

		# Loop through start:end pairs
		for pair in ${list[@]}
		do
			tmp=(${pair//:/ })
			startLine=${tmp[0]}
			endLine=${tmp[1]}

			if [ $startLine -eq 1 ]; then
				pass=1
			else
				fileName=$(head -n $startLine $file | tail -n 1 | sed 's/.*<xn:MeContext id="\(.*\)">.*$/\1/')
				fileName="MeContext=$fileName.xml"
			fi
			
			write=$(tail -n +$startLine $file | head -n $(($endLine-$startLine+1)) >> $fileName)
		done

		# Remove file since we don't need it anymore
		rm $file
	done
}

# Check for output directory
if [ -z "$1" ]; then
	echo -e "ERROR: Please supply output directory!"
	echo -e "Usage: $0 <outdir>"
	exit 1
fi

# Human readable variables
outdir=$1

# cd into output directory
cd $outdir

while IFS= read -r -d $'\0' dir; do
	if [[ $dir != $outdir ]]; then
		cd $dir
		fname=$(basename $dir)
		fname="$fname.xml"
		generateMeContext $fname
		cd $outdir
	fi
done < <(find "$outdir" -maxdepth 2 -type d -print0 2> /dev/null)
