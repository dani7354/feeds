# feeds

## Setup for development

1. Clone the repository
2. Create virtual env: `$ python3 -m venv venv/ && source venv/bin/activate`
3. Install dependencies: `$ pip install --upgrade pip && pip install -r requirements.txt`
4. Create a `.env` file in the root directory and add the following:

```
CONFIG_PATH=/local/path/to/project/feeds/config.dev.json
DEBUG=True
```

`config.dev.json` should be manually created and filled with information about the feeds or pages, which you would like
to follow. See `config.example.json` for inspiration.