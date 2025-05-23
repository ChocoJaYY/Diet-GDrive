<p align="center">
  <img src="https://i.imgur.com/UOU0MXR.png" width="800 alt="Diet-GDrive logo" />
</p>

# Diet-GDrive

> **Keep your Google Drive healthy with Diet-GDrive—automatically trim the digital fat and keep only what matters!**

**Diet-GDrive** is a smart, scriptable tool to keep your Google Drive lean and clutter-free. Delete old files, keep only your most important items, and automate cloud organization in just a few clicks.
No more wasted storage. No more manual sorting. Just a healthier, lighter Drive.

---

## Features

* **Delete all but the latest N files** in one or more Google Drive folders.
* **Recursively clean** all subfolders (optional).
* **Filter files** by extension or regex pattern.
* **Only delete files older than X minutes**.
* **Sort files** by modified time, created time, name, or size.
* **Dry run/test mode** to preview what will be deleted.
* **Verbose and logging options**.
* **Safe confirmation prompts** (unless overridden).
* **Flexible command-line usage** for automation.

---

## Installation

1. **Clone this repository** (or download the script file):

   ```bash
   git clone https://github.com/ChocoJaYY/Diet-GDrive.git
   cd Diet-GDrive
   ```

2. **Install required dependencies**:

   ```bash
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

3. **Set up Google Drive API credentials:**

   * Go to [Google Cloud Console](https://console.developers.google.com/).
   * Create a new project (if needed).
   * Enable the Google Drive API.
   * Create OAuth **Desktop** credentials and download `client_secrets.json`.
   * Rename your credentials file to `cleaner_client_secrets.json` and place it in the script directory.

---

## Usage

Run the script with Python:

```bash
python DietGDrive.py [options] <folder_id> [folder_id2 ...] <files_to_keep>
```

### Required Arguments

* `<folder_id>`: One or more Google Drive folder IDs to clean.
* `<files_to_keep>`: Number of most recent files to keep in each folder.

### Options

| Option              | Description                                                            |
| ------------------- | ---------------------------------------------------------------------- |
| `-t`, `--test-mode` | Dry run/test mode (do not delete files, just print what would happen). |
| `--sort`            | Sort files by `modifiedTime`, `createdTime`, `name`, or `size`.        |
| `--reverse`         | Reverse the sorting order (keep oldest files instead of newest, etc).  |
| `--ext`             | Only consider files with these extensions (e.g. `.pdf,.jpg`).          |
| `--exclude`         | Regex pattern for file names to exclude from deletion.                 |
| `-v`, `--verbose`   | Verbose output.                                                        |
| `--logfile`         | Write logs to a file (UTF-8).                                          |
| `-y`, `--yes`       | Do not prompt for confirmation, just delete.                           |
| `-r`, `--recursive` | Clean folders recursively (include all subfolders).                    |
| `--older-than`      | Only delete files older than this many minutes.                        |

---

## Example Commands

#### Clean multiple folders at once, keeping only 2 files in each (with confirmation prompt):

```bash
python DietGDrive.py YOUR_FOLDER_ID 2BcDeFgHijKLmNOpq 2
```

#### Keep only the 20 largest files (by size) in a folder, and delete the rest:

```bash
python DietGDrive.py --sort size --reverse YOUR_FOLDER_ID 20
```

#### Only keep the **latest file** in each folder, recursively, and do not prompt for confirmation:

```bash
python DietGDrive.py -r -y YOUR_FOLDER_ID 1
```

#### Keep the 5 most recently **created** (not modified) files in a folder:

```bash
python DietGDrive.py --sort createdTime YOUR_FOLDER_ID 5
```

#### Only consider image files (`.jpg`, `.png`) for deletion, keep latest 15:

```bash
python DietGDrive.py --ext .jpg,.png YOUR_FOLDER_ID 15
```

#### Exclude files with names containing “final” or “report”, delete all others except the latest 3:

```bash
python DietGDrive.py --exclude "(final|report)" YOUR_FOLDER_ID 3
```

#### Do a **dry run** to see what would be deleted in a folder and log output to `cleanup.log`:

```bash
python DietGDrive.py --test-mode --logfile cleanup.log YOUR_FOLDER_ID 7
```

#### Verbose mode, recursively keep 0 files (delete *everything*) except those matching extension filter:

```bash
python DietGDrive.py -r -v --ext .docx,.xlsx YOUR_FOLDER_ID 0
```

#### Clean, keeping latest 2 files older than 24 hours (1440 minutes):

```bash
python DietGDrive.py --older-than 1440 YOUR_FOLDER_ID 2
```

---

### Advanced Regex Examples

#### Delete **all files matching** `*_example.*` (keep none):

```bash
python DietGDrive.py --exclude "^(?!.*_example\.).*" YOUR_FOLDER_ID 0
```

*(Deletes all files ending with `_example.*`)*

#### Delete **all files except** those matching `*_example.*` (protect matching files):

```bash
python DietGDrive.py --exclude "_example\." YOUR_FOLDER_ID 0
```

*(Keeps files ending with `_example.*`, deletes all others)*

#### Clean recursively, **only delete backup files** (names contain “backup”), keep none:

```bash
python DietGDrive.py -r --exclude "^(?!.*backup).*" YOUR_FOLDER_ID 0
```

#### Clean, **delete all except** “important” files:

```bash
python DietGDrive.py --exclude "important" YOUR_FOLDER_ID 0
```

*(Keeps files with "important" in the name, deletes all others)*

---

## First Run & Authentication

On first run, a browser window will open for you to log in and grant access.
A `token.json` file will be created for future use—keep this file safe.

---

## Logging

Use `--logfile mylog.txt` to log all actions, errors, and summaries to a file.

---

## Safety & Notes

* **Test with `--test-mode`** before actual deletion!
* The script does **not** touch files in the Google Drive "trash".
* You must have permission to delete files in the folders you specify.
* Recursive operations on large folders may be subject to Google API quotas.

---

## Troubleshooting

* If you see authentication errors, delete `token.json` and re-run to re-authenticate.
* If you get `quota` or `rate limit` errors, wait a while or reduce the number of operations.
* Check file/folder IDs and permissions if nothing happens.

---

## Contributing

PRs and suggestions are welcome!
Want a new feature or better regex samples? [Open an issue!](https://github.com/ChocoJaYY/Diet-GDrive/issues)

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Made with ❤️ to keep your cloud in shape!**
