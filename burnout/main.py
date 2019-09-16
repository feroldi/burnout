#!/usr/bin/env python

import peewee
import argparse
import pytz
import os

from datetime import datetime, time, timedelta

database = peewee.SqliteDatabase("burnout.sqlite3")

local_tz = pytz.timezone(os.environ["TZ"])


class Entry(peewee.Model):
    start = peewee.DateTimeField()
    end = peewee.DateTimeField(default=lambda: datetime.now(pytz.utc))
    detail = peewee.TextField()
    tag = peewee.FixedCharField(max_length=16)

    class Meta:
        database = database


class Tracking(peewee.Model):
    start = peewee.DateTimeField(default=lambda: datetime.now(pytz.utc))
    is_active = peewee.BooleanField()

    @staticmethod
    def actives():
        return (
            Tracking.select().where(Tracking.is_active).order_by(Tracking.start.desc())
        )

    class Meta:
        database = database


def start_tracking():
    for track in Tracking.actives():
        track.is_active = False
        track.save()
    return Tracking.create(is_active=True)


def finish_tracking(detail, tag):
    actives = Tracking.actives()
    if actives.count() == 1:
        track = actives.get()
        track.is_active = False
        track.save()
        return Entry.create(start=track.start, detail=detail, tag=tag)


def productivity_score(date_from, date_to):
    total_sum = timedelta()
    for entry in Entry.select(Entry.start, Entry.end).where(
        Entry.end >= date_from, Entry.start <= date_to
    ):
        entry_start = datetime.fromisoformat(entry.start).astimezone(pytz.utc)
        entry_end = datetime.fromisoformat(entry.end).astimezone(pytz.utc)
        start = (
            entry_start
            if entry_start >= date_from
            else entry_start + (date_from - entry_start)
        )
        end = entry_end if entry_end <= date_to else entry_end - (entry_end - date_to)
        total_sum += end - start
    return total_sum


def status(args):
    if bool(args.date_from) != bool(args.date_to):
        raise RuntimeError("invalid set of arguments")

    if args.date_from:
        date_from, date_to = (
            local_tz.localize(datetime.fromisoformat(args.date_from)),
            local_tz.localize(datetime.fromisoformat(args.date_to)),
        )
        date_from, date_to = (
            date_from.astimezone(pytz.utc),
            date_to.astimezone(pytz.utc),
        )
    elif args.today:
        today = datetime.now(pytz.utc).date()
        midnight = local_tz.localize(datetime.combine(today, time(0, 0)), is_dst=None)
        almost_next_day = local_tz.localize(
            datetime.combine(today, time(23, 59)), is_dst=None
        )
        date_from = midnight.astimezone(pytz.utc)
        date_to = almost_next_day.astimezone(pytz.utc)

    print(productivity_score(date_from, date_to))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_track = subparsers.add_parser("track")
    parser_track.set_defaults(func=lambda _: start_tracking())

    parser_finish = subparsers.add_parser("finish")
    parser_finish.add_argument("--detail", metavar="TEXT", required=True)
    parser_finish.add_argument("--tag", type=str, required=True)
    parser_finish.set_defaults(
        func=lambda args: finish_tracking(detail=args.detail, tag=args.tag)
    )

    parser_status = subparsers.add_parser("status")
    parser_status.add_argument("--from", dest="date_from", metavar="DATETIME")
    parser_status.add_argument("--to", dest="date_to", metavar="DATETIME")
    parser_status.add_argument("--today", action="store_true")
    parser_status.set_defaults(func=status)
    args = parser.parse_args()

    database.connect()
    database.create_tables([Entry, Tracking])

    args.func(args)
