import json


def speaker():
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
        stylelist = (data[selectedspeaker]["styles"])
        styleindex = -1
        print("List of styles:")
        for y in stylelist:
            styleindex = styleindex + 1
            selectableid = stylelist[styleindex]["id"]
            selectablename = stylelist[styleindex]["name"]
            print("{}:".format(styleindex), "Name:", selectablename,
                  "id:", selectableid)

        selectedstyle = int(input("Which style would you like to choose:"))
        if selectedstyle > styleindex or selectedstyle < minimumindex:
            print("Not a proper style. Choose again.")

        else:
            speakername = data[selectedspeaker]["name"]
            speakeruuid = data[selectedstyle]["speaker_uuid"]
            speakerstyle = \
                data[selectedspeaker]["styles"][selectedstyle]["name"]
            speakerstyleid = \
                data[selectedspeaker]["styles"][selectedstyle]["id"]
            print("You have choosen",
                  speakername, speakeruuid,
                  "with the style", speakerstyle, "id:", speakerstyleid)
    return speakername, speakeruuid, speakerstyle, speakerstyleid
