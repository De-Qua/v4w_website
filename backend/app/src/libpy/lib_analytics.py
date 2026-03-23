from calendar import monthrange
from calendar import month_name
import numpy as np
#import datetime
from datetime import date
from datetime import datetime
import pdb
from datetime import timedelta

def extract_stats(data, col_names):
    """
    The father methods that calls all of the small ones we need
    """
    #pdb.set_trace()
    dates = data['datetime']
    urls = data['url']
    traffic_data_complete, traffic_data_10_weeks, traffic_data_last_week, averages, trends = analyze_traffic(dates, urls)
    pages_stats_bar, page_stats_pie = extract_pages_stats(urls)
    np_urls = np.asarray([url['value'] for url in pages_stats_bar])
    url_with_max_visualization = int(np.max(np_urls)) #int64 is not JSON serializable!
    # yday and today are old (not very good code), but since it's only one day, not a big deal
    yday_visits, max_visits_yday = extract_yesterday_stats(dates)
    today_visits, max_visits_today = extract_today_stats(dates)
    devices = data['ua_platform']
    devices_stats = extract_device_stats(devices)
    searches_stats, max_search = extract_searches_stats(urls)

    general_info = {'max_pages':url_with_max_visualization,
                    'max_visits_yday':max_visits_yday,
                    'max_visits_today':max_visits_today,
                    'max_search':max_search,
                    'averages':averages,
                    'trends':trends
                    }

    data_dict = {'stats_url':pages_stats_bar,
                'stats_url_pie':page_stats_pie,
                'traffic_whole':traffic_data_complete,
                'traffic_last_10_weeks':traffic_data_10_weeks,
                'traffic_last_week':traffic_data_last_week,
                'yesterday':yday_visits,
                'today':today_visits,
                'devices_stats':devices_stats,
                'searched_stats':searches_stats
                }
    return general_info, data_dict

def extract_yesterday_stats(dates):
    """
    Statistics about yesterday for every hour
    """
    visits_per_hour, max_visits = extract_stats_of_a_day(dates, 1)
    return visits_per_hour, max_visits

def extract_today_stats(dates):
    """
    Statistics about today for every hour
    """
    visits_per_hour, max_visits = extract_stats_of_a_day(dates, 0)
    return visits_per_hour, max_visits

def extract_stats_of_a_day(dates, timedelta_in_days):
    """
    Statistics about today for every hour
    """
    year, month, day, today = getTodaySeparated()
    todays = [visit for visit in dates if (today-visit.date() == timedelta(days=timedelta_in_days))]
    #24 hours
    hours = np.linspace(0, 23, 24)
    max_visits_in_an_hour = 0
    visits_per_hour = []
    for hour in hours:
        #pdb.set_trace()
        visits_hour = [visit for visit in todays if (visit.hour >= hour) and (visit.hour < (hour + 1))]
        num_of_visits = len(visits_hour)
        visits_per_hour.append({'name':int(hour), 'value':num_of_visits})
        if num_of_visits > max_visits_in_an_hour:
            max_visits_in_an_hour = num_of_visits
    return visits_per_hour, max_visits_in_an_hour

def getTodaySeparated():

    today = date.today()
    year = today.year
    month = today.month
    day = today.day
    return year, month, day, today

def extract_week_stats(dates):
    """
    Statistics about this week for every day
    """
    today = datetime.date.today()
    days_of_the_week = []
    week_visits = []
    max_visits = 0
    format = "%Y-%m-%d"
    for i in range(0,7):
        days_of_the_week.append(today - timedelta(days=i))
    for day in days_of_the_week:
        visits = [visit for visit in dates if (visit.date()-day == timedelta(days=0))]
        #print("checking {} against {}".format(day, visit.date()))
        day_date = day.strftime(format)
        week_visits.append({'date':day_date, 'value':len(visits)})
        if len(visits) > max_visits:
            max_visits = len(visits)
    return week_visits, max_visits

def extract_month_stats(dates):
    """
    Statistics about this month for every day
    """
    return 1

def extract_last_3_month_stats(dates):
    """
    Statistics about the last three months (including current one) for every week? day?
    """
    return 1

def analyze_traffic(dates, urls):
    """
    A better version to extract data using dates and urls at the same time.

    It loops over and counts how many visits per day and also separates into what types of visits (home, search, info, others).
    It creates one big list for all traffic data, one for the last 10 weeks and one for the last weeks.
    This can be easily changed.
    Using only one for loop makes it O(n), which is not too bad. However, pandas implementation of something like numpy's where
    would be much faster, I believe.

    It returns 3 lists of dicts where each dict will have 6 keys:
    1) date
    2) total_visits
    3) searches
    4) home
    5) info
    6) others

    plus also some general informations:
    - averages, which contains:
        - average visits in total
        - average visits last 10 week
        - average visits last week
    - trends (in percentages)
        - last week vs total
        - last week vs last teen weeks


    ###
    # TODO: rewrite using pandas methods to make it faster
    ###
    """
    traffic_data = []
    date_format = "%Y-%m-%d"
    last_date = dates[0] # this work only if everything is sorted
    traffic_data.append({'date':dates[0].strftime(date_format), 'total_visits':0, 'searches':0,
                            'home':0, 'info':0, 'others':0})

    traffic_data_last_ten_weeks = []
    started_gathering_last_ten_weeks = False
    traffic_data_last_week = []
    started_gathering_last_week = False
    today_date = datetime.now()
    total_visits_all_time = 0 # just for statistics
    counter_days = 0 # this helps to understand at which actual day we are (index goes on, the day stays the same)
    counter_days_last_ten_weeks = 0
    counter_days_last_week = 0
    total_visits = np.zeros(3)
    averages = np.zeros(3)
    trends = np.zeros(2)
    # trying to use only one for loop, so check has to be made in place, no other searches
    for index, (cur_date, url) in enumerate(zip(dates, urls)):
        if last_date.day == cur_date.day:
            traffic_data[counter_days]['total_visits'] += 1
            total_visits[0] += 1
            if started_gathering_last_ten_weeks == True:
                traffic_data_last_ten_weeks[counter_days_last_ten_weeks]['total_visits'] += 1
                total_visits[1] += 1
            if started_gathering_last_week == True:
                traffic_data_last_week[counter_days_last_week]['total_visits'] += 1
                total_visits[2] += 1
            total_visits_all_time += 1
            traffic_type = understand_traffic_type(url)
            traffic_data[counter_days][traffic_type] += 1
            if started_gathering_last_ten_weeks:
                traffic_data_last_ten_weeks[counter_days_last_ten_weeks][traffic_type] += 1
            if started_gathering_last_week:
                traffic_data_last_week[counter_days_last_week][traffic_type] += 1
        else:
            # check that last day was correct
            okay = check_visits(traffic_data[counter_days])
            assert(okay), f"Problem with: {traffic_data}, okay was {okay}"
            traffic_data.append({'date':cur_date.strftime(date_format), 'total_visits':0, 'searches':0,
                                    'home':0, 'info':0, 'others':0})
            last_date = dates[index]
            # CHECK IF WE ARE IN THE LAST TWO MONTHS
            #pdb.set_trace()
            last_date_datetime =  datetime(last_date.year, last_date.month, last_date.day, last_date.hour, last_date.minute, last_date.second, last_date.microsecond)
            #print(f"new day: {today_date} - last_date: {last_date_datetime}")
            #print(f"diff: {last_date_datetime - today_date}, check: {last_date_datetime - today_date > timedelta(weeks=10)}")
            if today_date - last_date_datetime < timedelta(weeks=10) and not started_gathering_last_ten_weeks:
                # time to start the last two months
                started_gathering_last_ten_weeks = True
                traffic_data_last_ten_weeks.append({'date':cur_date.strftime(date_format), 'total_visits':0, 'searches':0,
                                        'home':0, 'info':0, 'others':0, 'value':10})
                #print('once')
            elif started_gathering_last_ten_weeks == True:
                traffic_data_last_ten_weeks.append({'date':cur_date.strftime(date_format), 'total_visits':0, 'searches':0,
                                        'home':0, 'info':0, 'others':0, 'value':10})
                counter_days_last_ten_weeks += 1
                #print('adding every day')

            # CHECK IF WE ARE IN THE LAST WEEK
            if today_date - last_date_datetime < timedelta(weeks=1) and not started_gathering_last_week:
                # time to start the last two months
                started_gathering_last_week = True
                traffic_data_last_week.append({'date':cur_date.strftime(date_format), 'total_visits':0, 'searches':0,
                                        'home':0, 'info':0, 'others':0, 'value':10})
                #print('once')
            elif started_gathering_last_week == True:
                traffic_data_last_week.append({'date':cur_date.strftime(date_format), 'total_visits':0, 'searches':0,
                                        'home':0, 'info':0, 'others':0, 'value':10})
                counter_days_last_week += 1
                #print('adding every day')

            counter_days += 1

    # averaging
    averages[0] = total_visits[0] / counter_days
    averages[1] = total_visits[1] / counter_days_last_ten_weeks
    averages[2] = total_visits[2] / counter_days_last_week

    trends[0] = averages[2] / averages[0]
    trends[1] = averages[2] / averages[1]

    print("No logs here so I print to output, not very important. If needed, change app/src/libpy/lib_analytics.py in analyze_traffic (maybe line 123?)")
    print(f"Traffic data contains {len(traffic_data)} days for {total_visits_all_time} visits in total, which accounts for {total_visits_all_time/len(traffic_data)} visits per day in average")
    return traffic_data, traffic_data_last_ten_weeks, traffic_data_last_week, averages.tolist(), trends.tolist()

def to_integer(dt_time):
    """helper method to convert timestamp to datetime (seems like timestamp needs to be converted to integer before)"""
    return 10000*dt_time.year + 100*dt_time.month + dt_time.day

def understand_traffic_type(url):
    """Returns one of the 4 traffic types (home, searches, info, others)."""
    if url == 'https://www.dequa.it/':
        return "home"
    elif 'partenza' in url or 'update_results' in url:
        return "searches"
    elif 'info' in url or 'contatti' in url or 'idee' in url or 'comesiusa' in url or 'chisiamo' in url or 'howitsmade' in url or 'partecipare' in url or 'contatti' in url:
        return "info"
    else:
        return "others"

def check_visits(traffic_dict):
    """Just check that the sum of the different visits is the same as the total visits."""
    return traffic_dict['total_visits'] == (traffic_dict['searches'] + traffic_dict['home'] +
            traffic_dict['info'] + traffic_dict['others'])

def extract_traffic_stats(dates):
    """
    Statistics about visits per day/month/week.
    """
    months = np.linspace(1,12,12).astype(int)
    year = date.today().year
    years = 2020 + np.linspace(0, 1, 2).astype(int)
    visit_per_year = []
    visit_per_month = []
    last_six_months = np.linspace(datetime.date.today().month - 5, datetime.date.today().month, 6).astype(int)
    visits_last_six_months = []
    last_two_months = np.linspace(datetime.date.today().month - 1, datetime.date.today().month, 2).astype(int)
    visit_per_week = []
    visit_per_day = []
    max_visits_6m = 0
    max_visits_2m = 0
    for c_month in last_six_months:
        visits = [visit for visit in dates if visit.month == c_month]
        #format = "%Y-%m"
        #month_date = visits[0].strftime(format)
        visits_c = len(visits)
        visits_last_six_months.append({'name':int(c_month), 'value':visits_c})
        if visits_c > max_visits_6m:
            max_visits_6m = visits_c
    for c_month in last_two_months:
        days = monthrange(year, c_month)[1] # numero di giorni in quel mese
        for c_day in range(1,days+1):
            visits = [visit for visit in dates if visit.day == (c_day) and visit.month == c_month]
            day_as_date = datetime.date(year, c_month, c_day)
            format = "%Y-%m-%d"
            day_date = day_as_date.strftime(format)
            visits_c = len(visits)
            visit_per_day.append({'date':day_date, 'value':visits_c})
            if visits_c > max_visits_2m:
                max_visits_2m = visits_c

    return visits_last_six_months, max_visits_6m, visit_per_day, max_visits_2m

def extract_device_stats(devices):
    """
    Extract stats about devices
    """
    devices_no_none = [device for device in devices if device]
    devices_list = np.unique(np.asarray(devices_no_none))
    devices_stats = {}
    for device in devices_list:
        device_visit = [dev for dev in devices if dev == device]
        devices_stats[device] = len(device_visit)
    #pdb.set_trace()
    return devices_stats


def extract_searches_stats(urls):
    """
    Check what people seached
    """
    searches = [url for url in urls if 'update_results' in url]
    searches_stats = []
    max_search = 0
    address_search = [url for url in searches if 'arrivo=&' in url]
    searches_stats.append({'name':'ricerca singola', 'value':len(address_search)})
    if len(address_search) > max_search:
        max_search = len(address_search)
    path_search = [url for url in searches if not 'arrivo=&' in url]
    searches_stats.append({'name':'ricerca percorso', 'value':len(path_search)})
    if len(path_search) > max_search:
        max_search = len(path_search)
    walking = [url for url in path_search if 'walk=on' in url]
    searches_stats.append({'name':'a piedi', 'value':len(walking)})
    if len(walking) > max_search:
        max_search = len(walking)
    bridges = [url for url in path_search if 'lazy=on' in url]
    searches_stats.append({'name':'con i ponti', 'value':len(bridges)})
    if len(bridges) > max_search:
        max_search = len(bridges)
    tide = [url for url in path_search if 'tide=on' in url]
    searches_stats.append({'name':'con la marea', 'value':len(tide)})
    if len(tide) > max_search:
        max_search = len(tide)
    boat = [url for url in path_search if 'boat=on' in url]
    searches_stats.append({'name':'in barca', 'value':len(boat)})
    if len(boat) > max_search:
        max_search = len(boat)

    return searches_stats, max_search

def extract_pages_stats(urls):

    home_url = 'https://www.dequa.it/'
    search_string = 'update_results'
    info_page = '/info'
    idee_page = '/idee'
    contact_page = '/contatti'
    howitsmade_page = '/howitsmade'
    partecipa_page = '/partecipare'
    aboutus_page = '/chisiamo'
    howto_pagew = '/comesiusa'
    feedback_page = '/r2d2'
    manifest_page = '/manifest.json'
    robots_page = '/robots.txt'
    sworker_page = '/serviceWorker.js'
    url_stats = []
    url_stats_pie = {}
    home_urls = [url for url in urls if url == home_url]
    url_stats.append({'name':'home', 'value':len(home_urls)})
    searches = [url for url in urls if search_string in url]
    url_stats.append({'name':'ricerche', 'value':len(searches)})
    info_urls = [url for url in urls if info_page in url]
    url_stats.append({'name':'info', 'value':len(info_urls)})
    idee_urls = [url for url in urls if idee_page in url]
    url_stats.append({'name':'idee', 'value':len(idee_urls)})
    contacts_urls = [url for url in urls if contact_page in url]
    url_stats.append({'name':'contatti', 'value':len(contacts_urls)})
    howitsmade_urls = [url for url in urls if howitsmade_page in url]
    url_stats.append({'name':'howitsmade', 'value':len(howitsmade_urls)})
    partecipa_urls = [url for url in urls if partecipa_page in url]
    url_stats.append({'name':'partecipa', 'value':len(partecipa_urls)})
    aboutus_urls = [url for url in urls if aboutus_page in url]
    url_stats.append({'name':'chisiamo', 'value':len(aboutus_urls)})
    howto_urls = [url for url in urls if howto_pagew in url]
    url_stats.append({'name':'comesiusa', 'value':len(howto_urls)})
    feeedback_urls = [url for url in urls if feedback_page in url]
    url_stats.append({'name':'feedback', 'value':len(feeedback_urls)})
    manifest_urls = [url for url in urls if manifest_page in url]
    url_stats.append({'name':'manifest', 'value':len(manifest_urls)})
    robots_urls = [url for url in urls if robots_page in url]
    url_stats.append({'name':'robots', 'value':len(robots_urls)})
    sworker_urls = [url for url in urls if sworker_page in url]
    url_stats.append({'name':'worker', 'value':len(sworker_urls)})
    url_stats_pie = {item['name']:item['value'] for item in url_stats}

    return url_stats, url_stats_pie
