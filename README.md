# mixcloud-trigger

Run local actions when new items are added to MixCloud.

Example uses include:

*  Autoplay newly published things in a new browser window
*  Send a notification email
*  Feed item to an IM bot
*  Tweet a link

Why?  Because...

1.  I kept missing new uploads by my favourite DJ
2.  The [MixCloud API](https://www.mixcloud.com/developers/) makes it easy

You'll probably want to run this from a cron, so it has built-in locking to ensure no more than one instance runs at once.


## Requirements

*  Python 3 &amp; (probably included) pyvenv.  On OSX with [homebrew](http://brew.sh/), `brew install python3`


## Features

* Record successful processing so that item won't be touched again
* Retry failed actions on the next run
* Limit to N most recent items


## Setup

Needs a virtualenv and a few requirements.

```bash
$ cd mixcloud-trigger
$ pyvenv _venv3/
$ . _venv3/bin/activate
$ pip install --upgrade pip
$ pip install -r code/requirements.txt
```


## Configuration

Supports [.ini](https://en.wikipedia.org/wiki/INI_file) files plus include dirs so config is easy to manage & machine-generate.  

Example config tree:

```bash
$ tree conf
conf
├── main.conf
└── sources
    └── outsidetrance.conf
    
$ cat cat conf/main.conf
[sources]
sources_dir = conf/sources/

[metadata]
metadata_path = data/

$ cat conf/sources/outsidetrance.conf
[outsidetrance]
item_action = /bin/echo -n {name}
max_items = 3
```

Global config follows the format:

| Section | Key | Default | Description |
|---|---|---|---|
| `sources` | `sources_dir` | - | Directory to look in for per-source configs.  If it starts with a `/` it's treated as an absolute path; without and it's relative to the dir the main config file was in. |
| `metadata` | `metadata_path` | - | Directory in which locks &amp; per-source metadata will be stored in SQLite format. |


Per-source config must be:

* Within the `sources_dir` directory.  It is not valid to store per-source config in the main config file.
* Filename ending with `.conf`
* In a section headed with the source name

Inside, the following fields are valid:

| Key | Default | Description |
|---|---|---|
| `max_items`  | `5` | Maximum number of items to process in a single run against this feed.  Mostly to prevent all-of-the-items-ever getting processed on the first run.  Set to `0` if you really want this. |
| `want_types` | `upload,favorite` | Comma-separated list of item types you want to process; others will be ignored.  No spaces! |
| `item_action` | - | Shell command to be called on every matching item, with item values substituted.  See below for format. |
| `all_action`  | - | Shell command to be called once for this feed with all matching items.  Not called if zero items matched. __Not yet supported__|


### item_action Format

Python's String.format() is used to interpolate variables into your command for the specific feed item.  Variables are:

| Variable | Meaning  |
|---|---|
| `name` | Item name, e.g. "DJ AlexMock's Awesome Mix" |
| `url` | Direct MixCloud URL to the item |
| `type` | The type of feed item, e.g. `upload`, `favorite` |
| `created_time` | Time the item was created on MixCloud |

Variables are escaped with `shlex.quote()`.  Your command isn't; be careful with it.

Anything `/bin/sh` can handle, `item_action` can handle.  Your action is written to a temporary file and passed to the local `/bin/sh` for execution.  This means...

* `;` can be used to separate multiple commands.  e.g. `cd /path/to/somewhere; do_something_with {url}`
* Pipes work just fine
* Environment vars work - e.g. `cd $HOME; do_something_with {url}`
* `sudo` if you want to, but secure it properly

Python's `subprocess` module has problems handling very large amounts of output from a command.  This includes basically anything that prints a progress bar.  If you're calling some utility and it has a `--quiet` option, try to use it.


### all_action format

TBA.


## Running

```bash
$ tree conf
conf
├── main.conf
└── sources
    └── outsidetrance.conf

$ . _venv3/bin/activate

(_venv3) $ ./code/mixtrig.py -h    # display help

(_venv3) $ ./code/mixtrig.py -c examples/conf/main.conf
```


## Implementation Notes

* To ensure no item gets processed twice, once handled media item keys are written to a small SQLite DB is maintained under `data/`.  I tried a simpler approach (ignoring anything from before the script's last run) but it seems there's sometimes a delay between media uploads and the item becoming available, and this meant unseen items could fall before the script's previous run.
* Coloured/indented output with [clint](https://github.com/kennethreitz/clint)
* Some test coverage via basic Python unittest module


## Meta

### Limitations

* MixCloud's API returns 20 items per page and we don't yet support pagination.  Thus if there are more than 20 new items since the last scrape (and you set `max_items` > 20), the oldest ones will be overlooked.


## Coding

### Tests

```
$ python -m unittest discover code/
```

### Todo

* Better input-checking on config
* Make `all_action` work
* Mutleythreading for shell actions


### Pull Requests

Yes please!


## License

GPLv3.
