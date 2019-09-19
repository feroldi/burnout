#!/usr/bin/env python
#cython: language_level=3

import peewee as pw
import argparse

from datetime import datetime, time, timedelta

database = pw.SqliteDatabase(None)


class Session(pw.Model):
    start = pw.DateTimeField()
    end = pw.DateTimeField(default=datetime.now)
    detail = pw.TextField()
    tag = pw.FixedCharField(max_length=16)

    @staticmethod
    def all_tags():
        return Session.select(pw.fn.Distinct(Session.tag))

    class Meta:
        database = database


class Tracking(pw.Model):
    start = pw.DateTimeField(default=datetime.now)
    is_active = pw.BooleanField()

    @staticmethod
    def actives():
        return (
            Tracking.select().where(Tracking.is_active).order_by(Tracking.start.desc())
        )

    class Meta:
        database = database


def is_tracking():
    return Tracking.actives().count() > 0


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
        return Session.create(start=track.start, detail=detail, tag=tag)


def productivity_score(date_from, date_to, tag=None):
    total_sum = timedelta()
    for entry in Session.select(Session.start, Session.end).where(
        Session.end >= date_from, Session.start <= date_to, (Session.tag == tag if tag else True)
    ):
        start = (
            entry.start
            if entry.start >= date_from
            else entry.start + (date_from - entry.start)
        )
        end = entry.end if entry.end <= date_to else entry.end - (entry.end - date_to)
        total_sum += end - start
    return total_sum


def status(args):
    if bool(args.date_from) != bool(args.date_to):
        raise RuntimeError("invalid set of arguments")

    if args.date_from:
        date_from, date_to = (
            datetime.fromisoformat(args.date_from),
            datetime.fromisoformat(args.date_to),
        )
    elif args.today:
        today = datetime.now().date()
        date_from = datetime.combine(today, time(0, 0))
        date_to = datetime.combine(today, time(23, 59))

    if args.per_tags:
        for session in Session.all_tags():
            score = productivity_score(date_from, date_to, tag=session.tag)
            print(f"{session.tag}\t{score}")

    total_score = productivity_score(date_from, date_to)
    print(f"TOTAL\t{total_score}")

    answer = "yes" if is_tracking() else "no"
    print(f"Currently tracking: {answer}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-path", metavar="PATH", required=True)
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
    parser_status.add_argument("--per-tags", action="store_true")
    parser_status.set_defaults(func=status)
    args = parser.parse_args()

    database.init(args.database_path)
    database.connect()
    database.create_tables([Session, Tracking])

    args.func(args)
