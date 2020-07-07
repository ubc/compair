# extract-answers.awk - reads csv files of ComPAIR answers and generates txt files, one containing each answer's text
#
# Revisions:
#	2019-03-08 - new
#
# Sample usage: awk -f extract-answers.awk answers.csv

BEGIN {
	# note: make replacements to csv before running this script.
	#	1. \n to " "
	#	2. \r to \r\n
	# run first with debug on to check output before saving to txt files
	debug = 0;	# debug level: 0=none
	assign = 2;	# assignment number
	# columns
	if (assign == 1)
	{	first = 5;
		last = 4;
		stnum = 6;
		ans = 8;
	}
	else 	if (assign == 2)
	{	first = 2;
		last = 1;
		stnum = 3;
		ans = 5;
	}
	else
	{	exit 1;
	}
	
	# defaults
	BINMODE = 3; # don't replace line endings
	RS = "\r\n";	# in-record linebreaks are only \n newlines so safe to separate records by [CR][LF]
	FS = ",";		# comma-separated values
	FPAT = "([^,]+)|(\"[^\"]+\")"; # from https://www.gnu.org/software/gawk/manual/html_node/Splitting-By-Content.html.  Requires Gawk v4+.
}

# test
{	# strip quotes from answer
	if (substr($ans, 1, 1) == "\"")
	{	len = length($ans);
		$ans = substr($ans, 2, len - 2);    # Get text within the two quotes
	}
	
	# generate filename
	fn = $first "_" $last "_" $stnum;
	gsub(/\W/,"_",fn); # replace all non- word-constituent characters
	fn = fn ".txt";
	
	if (debug)
	{	print fn ":";
		print $ans;
	}
	else
	{	print "Saving to " fn;
		print $ans > fn;
	}
}
