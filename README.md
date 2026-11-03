# Burp Suite HTTP History Exporter

A small Python script that converts an HTTP history XML export from Burp Suite into a
spreadsheet-friendly **CSV** file or a self-contained **HTML** report you can open in a browser.

Requests and responses are base64-decoded, so the captured HTTP traffic is readable in the output.

## Requirements

- Python 3 (developed and tested with Python 3.14)
- No third-party packages. The script uses only the standard library.

## Exporting from Burp Suite

Export your HTTP history as XML from Burp Suite (select the items in the HTTP history
view, then use the save/export items option and choose XML). Keep the resulting `.xml`
file; it is the input to this script.

## Usage

```bash
# Run interactively: the script asks for the input file, format and output path
python3 burp_history_export.py

# Pass everything on the command line
python3 burp_history_export.py path/to/export.xml -f html -o path/to/report.html

# CSV is the default format
python3 burp_history_export.py path/to/export.xml -o history.csv
```

### Options

| Argument | Description |
| --- | --- |
| `input` | Path to the Burp HTTP history XML export. Optional on the command line; asked for if omitted. |
| `-f`, `--format` | `csv` or `html`. Asked for if omitted (defaults to `csv`). |
| `-o`, `--output` | Output file path, or a directory (the file is then named after the input). Defaults to `output/<input name>.<format>`. |
| `-h`, `--help` | Show help and exit. |

### Interactive mode

Any option you leave out is asked for at the prompt:

- **Input file:** re-prompts until the file exists.
- **Output format:** `csv` or `html`; anything else is rejected.
- **Output path:** press Enter to accept the default shown in brackets.

When the script is run without a terminal (for example from a cron job or another script),
it does not prompt. The input file is then required, and the output defaults to CSV at
`output/<input name>.csv`.

### Output

Output files are written to `output/` by default. The script creates the directory if it does
not exist.

**CSV** contains one row per request/response pair, with these columns:

`index, time, method, url, host, host_ip, port, protocol, path, extension, status,
response_length, mimetype, comment, request, response`

The file is UTF-8 with a byte-order mark, so Excel displays non-ASCII text correctly.

**HTML** is a single file with no external dependencies. It shows a table of the items
(number, time, method, URL, status, length, MIME type, comment). Each row has a **show**
link that reveals the decoded request and response. Content is HTML-escaped.

## Notes

- Bodies are decoded as UTF-8, with undecodable bytes replaced by `�`. Binary responses
  (images, archives, and so on) will not be readable in either output format.
- The script reads the whole export into memory. Very large exports need a correspondingly
  large amount of RAM.

## Project layout

```
burp_history_export.py   # the converter
data/                    # your Burp XML exports (git-ignored)
output/                  # default location for generated files (git-ignored)
```
