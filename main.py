import getspeakers
import selectspeaker
import getjsonquery
import getfile
import get2speakermorphing

url = "http://localhost:50021"
wannaexit = False

if __name__ == "__main__":
    while wannaexit is False:
        print("Here's what you can do:")
        print("0: Update speakers info + files")
        print("1: Choose a speaker (You must do 0 once)")
        print("2: Generate necessary json (You must do 1 first.)")
        print("3: Get generated audio file (You must do 1 and 2 firt.)")
        print("4: Morphing from 2 speakers audio (You must do 1 and 2 first.)")
        print("5: Exit")

        selection = int(input("What would you like to do:"))

        if selection == 0:
            getspeakers.updatespeakers(url)

        elif selection == 1:
            speakername, speakeruuid, speakerstyle, \
                    speakerstyleid = selectspeaker.speaker()
        elif selection == 2:
            text = str(input("Japanese text:"))
            getjsonquery.jsonqueryget(url, speakerstyleid, text)

        elif selection == 3:
            getfile.simplesynthesis(url, speakerstyleid)

        elif selection == 4:
            speakername2, speakeruuid2, speakerstyle2, \
                speakerstyleid2 = selectspeaker.speaker()

            selectedmorphing = float(input("Set value from 0 to 1 (e.g 0.4):"))
            get2speakermorphing.synthesismorphing(url,
                                                  speakerstyleid,
                                                  speakerstyleid2,
                                                  selectedmorphing)

        elif selection == 5:
            wannaexit = True

        else:
            print("Not a proper option. Try again.")
