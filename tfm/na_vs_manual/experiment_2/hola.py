import re

regexes = {
    "sh[[ow]] ip int[[erface]] br[[ief]]": "show ip interface brief",
}

regexes = {regex.replace("[", "(").replace("]", ")?"): value for regex, value in regexes.items()}

input_string = "sh ip int brief 0/2/0"

for regex, value in regexes.items():
    regexp = re.compile(regex)
    base_command = regexp.search(input_string).group(0)
    args = input_string.replace(base_command, "").strip().split(" ")
    if result:
        print(args)
        break