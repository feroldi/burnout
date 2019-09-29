# burnout

Burnout is a tracking tool that keeps records of one's productivity over periods of time.

**Note**: this tool probably goes crazy when there are DST changes in your time zone.

## Example

Start tracking one's productivity:

```shell
$ poetry run burnout/main.py track
```

Finish tracking one's productivity, and give this session a description and a tag:

```shell
$ poetry run burnout/main.py finish --detail "Wrote my essay" --tag ESSAY
```

Show how much time one's spent being productive today:


```shell
$ poetry run burnout/main.py status --today
```

Show how much time one's spent being productive from 08 AM to 4:30 PM on September 16th, 2019:

```shell
$ poetry run burnout/main.py status --from '2019-09-16 08:00' --to '2019-09-16 16:30'
```

## License

This project is licensed under the MIT License.
See LICENSE.
