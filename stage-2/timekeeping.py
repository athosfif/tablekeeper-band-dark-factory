"""Wall-clock grids with elapsed-time duration and first-fold IANA resolution."""
from datetime import date, datetime, time, timedelta, timezone
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from validation import fail, require

UTC = timezone.utc
WEEKDAYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')


def zone(name):
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        fail()


def calendar_date(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) is not None)
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail()


def clock_time(value):
    require(re.fullmatch(r'\d{2}:\d{2}', value) is not None)
    try:
        return time.fromisoformat(value)
    except ValueError:
        fail()


def local_time(value):
    require(type(value) is str, 'malformed_request', 400)
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', value) is not None)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        fail()


def resolve(local, tz):
    first = local.replace(tzinfo=tz, fold=0)
    require(first.astimezone(UTC).astimezone(tz).replace(tzinfo=None) == local,
            'invalid_local_time')
    return first


def hours(restaurant, day):
    return next((h for h in restaurant['opening_hours']
                 if h['weekday'] == WEEKDAYS[day.weekday()]), None)


def interval(restaurant, value):
    local = local_time(value)
    tz = zone(restaurant['timezone'])
    start = resolve(local, tz)
    opening = hours(restaurant, local.date())
    require(opening is not None, 'outside_opening_hours')
    opens = datetime.combine(local.date(), clock_time(opening['opens']))
    closes = datetime.combine(local.date(), clock_time(opening['closes']))
    require(opens <= local < closes, 'outside_opening_hours')
    elapsed = int((local - opens).total_seconds() // 60)
    require(elapsed % restaurant['slot_minutes'] == 0, 'not_on_slot_grid')
    try:
        end = (start.astimezone(UTC) + timedelta(minutes=restaurant['reservation_duration_minutes'])).astimezone(tz)
    except OverflowError:
        fail('outside_opening_hours')
    require(end.astimezone(UTC) <= resolve(closes, tz).astimezone(UTC), 'outside_opening_hours')
    return start, end


def starts(restaurant, day):
    opening = hours(restaurant, day)
    if not opening:
        return
    value = datetime.combine(day, clock_time(opening['opens']))
    closes = datetime.combine(day, clock_time(opening['closes']))
    while value < closes:
        local = value.isoformat(timespec='minutes')
        try:
            start, end = interval(restaurant, local)
        except Exception as error:
            from validation import APIError
            if not isinstance(error, APIError) or error.code not in ('invalid_local_time', 'outside_opening_hours'):
                raise
        else:
            yield local, start, end
        # A very large valid slot step simply has no further candidates today.
        remaining = int((closes - value).total_seconds() // 60)
        if restaurant['slot_minutes'] >= remaining:
            break
        value += timedelta(minutes=restaurant['slot_minutes'])


def instant(value):
    return datetime.fromisoformat(value).astimezone(UTC)


def now():
    return datetime.now(UTC)
