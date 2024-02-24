#!/usr/bin/python
# see https://pypi.org/project/holidays/
# see https://pypi.org/project/icalendar/
# get calendars for Germany from https://www.schulferien.org/deutschland/ical/

from icalendar import Calendar, Event
from datetime import date, timedelta

import holidays
import datetime
import glob

logging = 1


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


de_holidays = holidays.Germany(
    prov="NI"
)  # or holidays.US(), or holidays.CountryHoliday('US')

for filename in glob.glob("/etc/openhab/html/FerienKalender/*.ics"):
    if logging > 0:
        print(f"parsing file {filename}")
    file = open(filename, "rb")
    cal = Calendar.from_ical(file.read())

    if logging > 1:
        print(cal)

    for component in cal.walk():
        if component.name == "VEVENT":
            summary = component.get("summary")
            description = component.get("description")
            location = component.get("location")
            startdt = component.get("dtstart").dt
            enddt = component.get("dtend").dt
            exdate = component.get("exdate")
            if component.get("rrule"):
                reoccur = component.get("rrule").to_ical().decode("utf-8")
                for item in parse_recurrences(reoccur, startdt, exdate):
                    if logging > 0:
                        print(
                            "\t{0} {1}: {2} - {3}".format(
                                item, summary, description, location
                            )
                        )
            else:
                if logging > 0:
                    print(
                        "\t{0}-{1} {2}: {3} - {4}".format(
                            startdt.strftime("%D %H:%M UTC"),
                            enddt.strftime("%D %H:%M UTC"),
                            summary,
                            description,
                            location,
                        )
                    )
                for single_date in daterange(startdt, enddt):
                    if logging > 0:
                        print(single_date.strftime("%Y-%m-%d"))
                    de_holidays.append({single_date: description})

now = datetime.datetime.now()
print(date(now.year, now.month, now.day) in de_holidays)
