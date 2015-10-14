# Landa

### Add labels to PRs based on touched files or author.

Install:

```bash
pip3 install https://github.com/appfolio/landa/archive/master.zip
```

Start:

```bash
landa appfolio/landa
```

This will add labels to PRs if any file path in the PR matches pattern.

Looks for configuration in `~/.config/landa/landa.conf`. The configuration
exists of two sections. `[author_team]` will apply a label to each PR created
by one of the supplied usernames. `[label_pattern]` will apply a label to each
PR that changes a file that matches given pattern.

```conf
[author_team]
enhancement: balloob,some_other_user
team_awesome: more_user,yes_user

[label_pattern]
js_review: package.json
db_review: db/*
```

### Props

This is based on [Farcy](https://github.com/appfolio/farcy) by Bryce Boe and me.
