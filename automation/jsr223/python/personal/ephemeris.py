"""This script sets todays type of days using ephemeris actions"""

from core.rules import rule
from core.triggers import when
from core.actions import Ephemeris
import os


@rule(
    "ephemeris day typ detection",
    description="determine todays day type",
    tags=["ephemeris", "weekend", "holiday", "systemstart", "cronjob"],
)
@when("Time cron 5 5 0 ? * * *")
# @when("Time cron 0/60 * * * * ?")
@when("System started")
def determine_day_type(event):
    """
    determine todays type of days

    Args:
        event (_type_): _description_
    """
    OH_CONF = os.getenv("OPENHAB_CONF")
    ephemeris_public_holiday_file = OH_CONF + "/services/holidays_de.xml"
    today_morning = ZonedDateTime.now().truncatedTo(ChronoUnit.DAYS)

    determine_day_type.log.debug(OH_CONF)
    next_holiday = Ephemeris.getNextBankHoliday(ephemeris_public_holiday_file)

    until_holiday = Ephemeris.getDaysUntil(next_holiday, ephemeris_public_holiday_file)
    name_holiday = Ephemeris.getHolidayDescription(next_holiday)
    determine_day_type.log.info(
        "Nächster Feiertag: " + str(name_holiday) + " in Tagen: " + str(until_holiday)
    )

    next_public_holiday_date = today_morning.plusDays(until_holiday)
    determine_day_type.log.info(
        "Nächster Feiertag: " + str(next_public_holiday_date.toString()).split("T")[0]
    )

    events.sendCommand("NextDay_PublicHoliday", str(name_holiday))
    events.sendCommand("NextDay_Till_PublicHoliday", str(until_holiday))

    ephemeris_birthday_file = OH_CONF + "/services/birthdays.xml"
    next_birthday = Ephemeris.getNextBankHoliday(ephemeris_birthday_file)
    until_birthday = Ephemeris.getDaysUntil(next_birthday, ephemeris_birthday_file)
    determine_day_type.log.info(
        "Nächster Geburtstag: "
        + str(next_birthday)
        + " in Tagen: "
        + str(until_birthday)
    )

    next_birthday_date = today_morning.plusDays(until_birthday)
    determine_day_type.log.info(
        "Nächster Geburtstag: " + str(next_birthday_date.toString()).split("T")[0]
    )

    events.sendCommand("NextDay_Birthday", str(next_birthday))
    events.sendCommand("NextDay_Till_Birthday", str(until_birthday))

    ephemeris_school_holiday_file = OH_CONF + "/services/holidays.xml"
    next_school_holiday = Ephemeris.getNextBankHoliday(ephemeris_school_holiday_file)
    until_school_holiday = Ephemeris.getDaysUntil(
        next_school_holiday, ephemeris_school_holiday_file
    )
    next_school_holiday = str(str(next_school_holiday).split(" ")[0])
    determine_day_type.log.info(
        "Nächster Ferientag: "
        + next_school_holiday
        + " in Tagen: "
        + str(until_school_holiday)
    )

    next_school_holiday_date = today_morning.plusDays(until_school_holiday)
    determine_day_type.log.info(
        "Nächster Ferientag: " + str(next_school_holiday_date.toString()).split("T")[0]
    )

    events.sendCommand("NextDay_SchoolHoliday", next_school_holiday)
    events.sendCommand("NextDay_Till_SchoolHoliday", str(until_school_holiday))

    day_of_year = today_morning.getDayOfYear() - 1
    start_of_year_date = today_morning.minusDays(day_of_year)
    determine_day_type.log.info(
        "JahresAnfang: "
        + str(start_of_year_date.toString()).split("T")[0]
        + " was "
        + str(day_of_year)
        + " days ago."
    )

    scan_birthdays = Ephemeris.getNextBankHoliday(
        today_morning, ephemeris_birthday_file
    )
    scan_birthdays_date = today_morning.plusDays(
        Ephemeris.getDaysUntil(scan_birthdays, ephemeris_birthday_file)
    )
    last_birthday_date = today_morning
    while last_birthday_date.until(scan_birthdays_date, ChronoUnit.DAYS) > 0:
        determine_day_type.log.info(
            "Geburtstag: "
            + str(scan_birthdays)
            + " am "
            + str(scan_birthdays_date.toString()).split("T")[0]
        )

        birthday_group_name = scan_birthdays.split(" ")[0]
        birthday_item_name = scan_birthdays.replace(" ", "_")
        birthday_item_till_date_name = birthday_group_name + "_till_Birthday"
        if not itemRegistry.getItems(birthday_group_name):
            add_item(
                birthday_group_name,
                item_type="Group",
                label=birthday_group_name,
                category="calendar",
                groups=["gEphemeris"],
            )

        if not itemRegistry.getItems(birthday_item_name):
            add_item(
                birthday_item_name,
                item_type="DateTime",
                label=birthday_item_name + " [%s]",
                category="calendar",
                groups=[birthday_group_name],
            )
        events.sendCommand(
            birthday_item_name, str(scan_birthdays_date.toString()).split("T")[0]
        )

        if not itemRegistry.getItems(birthday_item_till_date_name):
            add_item(
                birthday_item_till_date_name,
                item_type="Number",
                label=birthday_item_till_date_name + " [%s]",
                category="calendar",
                groups=[birthday_group_name],
            )
        events.sendCommand(
            birthday_item_till_date_name,
            str(today_morning.until(scan_birthdays_date, ChronoUnit.DAYS)),
        )

        last_birthday_date = scan_birthdays_date
        scan_birthdays = Ephemeris.getNextBankHoliday(
            last_birthday_date.plusDays(1), ephemeris_birthday_file
        )
        scan_birthdays_date = today_morning.plusDays(
            Ephemeris.getDaysUntil(scan_birthdays, ephemeris_birthday_file)
        )


#        determine_day_type.log.info(
#            "Nächster Geburtstag: "
#            + str(scan_birthdays)
#            + " am "
#            + str(scan_birthdays_date.toString()).split("T")[0]
#            + " in "
#            + str(last_birthday_date.until(scan_birthdays_date, ChronoUnit.DAYS))
#        )
