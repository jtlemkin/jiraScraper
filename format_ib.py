import sys

lines = ""

with open(sys.argv[1], "r") as read_file:
	lines = read_file.readlines()

lines.replace("-", ", ")

with open(sys.argv[1], "w") as write_file:
	write_file.write(map(lambda x: x.replace("-", ", "), lines))
