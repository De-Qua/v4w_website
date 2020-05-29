
i = 0
endn = 10
percentage = i / endn
string_to_be_print = "-"
for i in range(endn):
    string_to_be_print += "="
    print(string_to_be_print, end="\r", flush=True)
