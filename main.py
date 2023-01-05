import getspeakers
import selectspeaker
import getjsonquery
import getfile

url = "http://localhost:50021"
wannaexit = "False"

if __name__ == "__main__":
    while wannaexit == "False":
        print("Here's what you can do:")
        print("0: Update speakers info + files")
        print("1: Choose a speaker (You must do 0 first.)")
        print("2: Generate necessary json (You must do 1 first.)")
        print("3: Get generated audio file (You must do 1 and 2 firt.)")
        print("4: Exit")

        selection = int(input("What would you like to do:"))

        if selection == 0:
            getspeakers.updatespeakers(url)

        elif selection == 1:
            speakername, speakeruuid, speakerstyle,\
                    speakerstyleid = selectspeaker.speaker()
        elif selection == 2:
            text = str(input("Japanese text:"))
            getjsonquery.jsonqueryget(url, speakerstyleid, text)

        elif selection == 3:
            getfile.simplesynthesis(url, speakerstyleid)

        elif selection == 4:
            wannaexit = "True"

        else:
            print("Not a proper option. Try again.")
