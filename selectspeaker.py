import json

with open('speakers.json') as j:
    data = json.load(j)
speakerlist = ([item["name"] for item in data])


print("List of speakers:")
index = -1
minimumindex = 0
for i in speakerlist:
    index = index + 1
    print("{}:".format(index), speakerlist[index])


selectedspeaker = int(input("Which speaker would you like to select:"))
if selectedspeaker > index or selectedspeaker < minimumindex:
    print("Not a proper speaker. Choose again.")

else:
    selectablestyles = (data[selectedspeaker]["styles"])
    styleindex = -1
    print("List of styles:")
    for y in selectablestyles:
        styleindex = styleindex + 1
        selectableid = selectablestyles[styleindex]["id"]
        selectablename = selectablestyles[styleindex]["name"]
        print("Name:", selectablename, "id:", selectableid)
