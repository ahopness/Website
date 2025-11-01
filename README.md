<div align="center">
    <img src="https://blob.gifcities.org/gifcities/HNMHMX7577NIEONBTNFB3257TGA3ZVOI.gif">
    <h3>My World Wide Web page, static site, work catalog. </h3>
    <h4>Powered by a static site generator written in Python and hosted by Github Pages.</h4>
</div>

## Directory Structure

```
project/
├── data/           # CSS, images, and other assets
├── pages/          # HTML pages with TEMPLATE tags
├── templates/      # HTML templates with CONTENT placeholders
├── builder.py      # Static site generator
├── server.py       # Development server w/ hot reloading
└── build/          # Generated output (created by builder.py)
```

## Requirements

- Python 3.6 or higher
  - `pip install watchdog` to run server.py.

## To Do

- [x] Add UV package manager.
- [x] Change template engine to Jinja.
- [ ] Update `index.html`.

