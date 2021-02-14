[![Tests](https://github.com/d5h-foss/yatl/workflows/Tests/badge.svg)](https://github.com/d5h-foss/yatl/actions?workflow=Tests)
[![Codecov](https://codecov.io/gh/d5h-foss/yatl/branch/master/graph/badge.svg)](https://codecov.io/gh/d5h-foss/yatl)
[![PyPI](https://img.shields.io/pypi/v/pyyatl.svg)](https://pypi.org/project/pyyatl/)

# Summary

YATL is a templating language in which both the input and output are YAML.
This solves the common problem of wanting to have a template that produces YAML files,
but are usually solved by using an templating framework (Go templates, Jinja2, etc.), thus making the input not YAML.
This means you can no longer lint your input, or load it in an IDE without confusing it. It also means that your
template is probably tied to the specific language in which your toolchain is written.

YATL aims to be both a standard YAML-in, YAML-out templating language, and a library to load files. This codebase
is a Python implementation, but the plan is to make a core library with bindings for many languages.

This is a work in progress. See the status section below for details.

# Installation

```console
$ pip install PyYATL
```

# Usage

```pycon
>>> import yatl
>>> yatl.load("""
... hosts:
...     - .for (host in west_hosts):
...         .(host)
...     - .for (host in east_hosts):
...         .(host)
... """, {"west_hosts": ["west-1", "west-2"], "east_hosts": ["east-1", "east-2"]})
{'hosts': ['west-1', 'west-2', 'east-1', 'east-2']}
```

# The YATL Language

This section gives an overview of the YATL syntax. For more details, see the complete documentation (coming soon).

All YATL directives start with a `.`.

## Interpolation

When `.(p)` is seen in a value, it is replaced with the parameter value of `p`.

Example:

```yaml
environment: .(env)
deployment_name: .(service_name)-.(env)
```

If `env = production` and `service_name = foo`, then the output would be:

```yaml
environment: production
deployment_name: foo-production
```

## Conditionals

Example:

```yaml
deployment_type: canary
.if (is_production):
    alert-email: page_me@example.com
```

If `is_production = true`, then the output is:

```yaml
deployment_type: canary
alert-email: page_me@example.com
```

You can also have `.elif` and `.else`:

```yaml
.if (is_production):
    slack-channel: "#production"
.elif (is_staging):
    slack-channel: "#staging"
.else:
    slack-channel: "#development"
```

You can also use `.if` in lists. This is a special case where the value within the `.if` will extend the outer list:

```yaml
hosts:
    - west-1
    - west-2
    - .if (multi_data_center):
        - east-1
        - east-2
```

Assuming `multi_data_center = true`, this would output:

```yaml
hosts:
    - west-1
    - west-2
    - east-1
    - east-2
```

If you actually want a list within a list when using `.if`, you need to add an extra list wrapping the `.if`.

## For Loops

For loops allow you to loop over values:

```yaml
hosts:
    .for (host in hosts):
        .(host)
```

If `hosts = ["west-1", "west-2"]`, then the output would be:

```yaml
hosts:
    - west-1
    - west-2
```

For loops always return lists, so the syntax is a bit loose. The following are both equivalent:

```yaml
hosts:
    .for (host in hosts):
        .(host)
```

```yaml
hosts:
    - .for (host in hosts):
        .(host)
```


Like `.if`, they extend the outer list, so you can combine for loops into a single list:

```yaml
hosts:
    - .for (host in west_hosts):
        .(host)
    - .for (host in east_hosts):
        .(host)
```

Assuming the obvious assignments, this outputs:

```yaml
hosts:
    - west-1
    - west-2
    - east-1
    - east-2
```

## Loading Files

YATL allows including files, to make it easier to organize large YAML objects.

The basic idea is that if you load a YATL file like this:

```yaml
top:
    .load_defaults_from: some-file.yaml
    foo: bar
```

And `some-file.yaml` looks like this:

```yaml
baz: quux
```

Then you'll get this:

```yaml
top:
    foo: bar
    baz: quux
```

Loaded files can also load other files.

Files loaded with `.load_defaults_from` are always considered defaults. Hence, if a file has fields in common
with loaded defaults, then the file doing the loading always wins out. Otherwise objects are merged. For example,
say we have this in a file called `config.yaml`:

```yaml
outer:
    .load_defaults_from: some-file.yaml
    inner:
        foo: bar
```

If `some-file.yaml` looks like this:

```yaml
inner:
    foo: baz
```

Then the result will be this (fields in both `config.yaml` and `some-file.yaml` are taken from `config.yaml`, because
loads are always defaults):

```yaml
outer:
    inner:
        foo: bar
```

If `some-file.yaml` looks like this instead:

```yaml
inner:
    baz: quux
```

Then the result would be this (fields in objects are merged):

```yaml
outer:
    inner:
        foo: bar
        baz: quux
```

If `inner` was not an object (e.g., it's a list) in either file, then no merging will happen, and whatever is in
`config.yaml` will be the result.

Lastly, if a file loads two or more files which both have defaults for the same field, then whichever is loaded at
the highest nesting level will win. For example, if we have:

```yaml
outer:
    .load_defaults_from: file1.yaml
    inner:
        load_defaults_from: file2.yaml
```

If both `file1.yaml` and `file2.yaml` have defaults for the same field (which would have to be inside `inner`), then the
defaults from `file2.yaml` will take precendence.

# Status

The language spec is likely to change at least slightly.

- [x] Proof of concept
- [ ] Support safe expressions
- [ ] Polish (load lists of files, allow escaping, etc.)
- [ ] Complete documentation
- [ ] Include line number with error messages
- [ ] Support Python versions other than CPython 3.6 and Python 3.7+ (because of dict ordering)

This software should be considered beta.
