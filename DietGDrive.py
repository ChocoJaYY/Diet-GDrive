import argparse
import os
import re
from functools import partial
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone, timedelta

SCOPES = ['https://www.googleapis.com/auth/drive']

def google_logon():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('cleaner_client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def get_all_folders(service, parent_id):
    folders = []
    try:
        metadata = service.files().get(fileId=parent_id, fields="id, name").execute()
        folders.append({'id': parent_id, 'name': metadata.get('name', 'Unknown')})
    except Exception as e:
        print(f"Could not retrieve folder name for {parent_id}: {e}")
        folders.append({'id': parent_id, 'name': str(parent_id)})

    query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    page_token = None
    while True:
        try:
            response = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()
            for folder in response.get('files', []):
                folders.extend(get_all_folders(service, folder['id']))
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        except HttpError as error:
            print(f'An error occurred during folder fetch: {error}')
            break
    return folders

def google_delete(service, file_to_delete):
    service.files().delete(fileId=file_to_delete['id']).execute()

def google_query(service, folder_id, fields=None):
    fields = fields or "nextPageToken, files(id, name, modifiedTime, createdTime, mimeType, size)"
    query = f"trashed=false and '{folder_id}' in parents"
    result = []
    page_token = None
    while True:
        try:
            response = service.files().list(
                q=query,
                orderBy="modifiedTime",
                fields=fields,
                pageSize=1000,
                pageToken=page_token
            ).execute()
            result.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        except HttpError as error:
            print(f'An error occurred: {error}')
            break
    return result

def log_action(logfile, text):
    if logfile:
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(text + '\n')

def filter_files(files, ext_filter=None, exclude_pattern=None, verbose=False):
    initial_count = len(files)
    filtered = files
    if ext_filter:
        ext_list = [e.strip().lower() for e in ext_filter.split(",")]
        filtered = [f for f in filtered if os.path.splitext(f['name'])[1].lower() in ext_list]
    if exclude_pattern:
        regex = re.compile(exclude_pattern)
        filtered = [f for f in filtered if not regex.search(f['name'])]
    if verbose:
        print(f"Filtered {initial_count - len(filtered)} files due to extension/exclude filters.")
    return filtered

def filter_by_age(files, minutes_old=0):
    if not minutes_old or minutes_old <= 0:
        return files
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
    filtered = []
    for f in files:
        mtime = f.get('modifiedTime', '')
        if mtime:
            try:
                filedate = datetime.fromisoformat(mtime.replace("Z", "+00:00"))
            except Exception:
                continue
            if filedate < cutoff:
                filtered.append(f)
    return filtered

def sort_files(files, sort_by="modifiedTime", reverse=False):
    def get_val(f):
        if sort_by in ("modifiedTime", "createdTime"):
            try:
                return datetime.fromisoformat(f.get(sort_by, "").replace("Z", "+00:00"))
            except Exception:
                return datetime.min
        elif sort_by == "size":
            try:
                return int(f.get("size", 0))
            except Exception:
                return 0
        return f.get("name", "")
    return sorted(files, key=get_val, reverse=reverse)

def clean_drive(folder_id, folder_name, files_to_keep, test_mode=False, query=None, clean=None,
                sort_by="modifiedTime", reverse=False, ext_filter=None, exclude_pattern=None,
                verbose=False, logfile=None, confirm=False, older_than=0):
    summary = {'found': 0, 'kept': 0, 'deleted': 0, 'skipped': 0, 'errors': 0}
    files = query(folder_id)
    files = filter_files(files, ext_filter=ext_filter, exclude_pattern=exclude_pattern, verbose=verbose)
    files = sort_files(files, sort_by=sort_by, reverse=reverse)
    files = filter_by_age(files, minutes_old=older_than)
    summary['found'] = len(files)

    if files_to_keep < 0:
        print("Files to keep cannot be < 0")
        return summary

    if files_to_keep > 0:
        files_to_remove = files[:-files_to_keep]
        files_kept = files[-files_to_keep:]
    else:
        files_to_remove = files
        files_kept = []

    summary['kept'] = len(files_kept)

    if files_to_remove:
        print(f"\n[{folder_name} ({folder_id})] Files that will be deleted:")
        for f in files_to_remove:
            size_str = f"{int(f['size'])/1024:.1f} KB" if f.get('size') else "N/A"
            print(f"  {f['name']} (ID: {f['id']}, Modified: {f.get('modifiedTime', '')}, Created: {f.get('createdTime', '')}, Size: {size_str})")
            log_action(logfile, f"[{folder_name} ({folder_id})] Will delete: {f['name']} (ID: {f['id']}, Size: {size_str})")
    else:
        print(f"[{folder_name} ({folder_id})] No files to remove.")

    if test_mode:
        print("--- DRY RUN --- Skipping file deletion.")
        return summary

    if files_to_remove and not confirm:
        proceed = input("Proceed with deletion? (y/n): ").strip().lower()
        if proceed != 'y':
            print("Aborting deletion.")
            return summary

    for f in files_to_remove:
        try:
            if verbose:
                print(f"Deleting {f['name']} (ID: {f['id']})")
            clean(f)
            summary['deleted'] += 1
            size_str = f"{int(f['size'])/1024:.1f} KB" if f.get('size') else "N/A"
            log_action(logfile, f"[{folder_name} ({folder_id})] Deleted: {f['name']} (ID: {f['id']}, Size: {size_str})")
        except Exception as e:
            summary['errors'] += 1
            print(f"Error deleting {f['name']}: {e}")
            log_action(logfile, f"[{folder_name} ({folder_id})] ERROR deleting {f['name']} (ID: {f['id']}): {e}")

    print(f"Kept {len(files_kept)} files. Deleted {summary['deleted']} files. Skipped {summary['errors']} errors.")
    log_action(logfile, f"[{folder_name} ({folder_id})] SUMMARY: Kept {len(files_kept)}, Deleted {summary['deleted']}, Errors {summary['errors']}")
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Clean one or more Google Drive folders by deleting all but the latest N files."
    )
    parser.add_argument("-t", "--test-mode", "--dry-run", action="store_true",
                        help="Dry run / test mode (do not delete files)", default=False)
    parser.add_argument("--sort", default="modifiedTime", choices=["modifiedTime", "createdTime", "name", "size"],
                        help="Sort files by this field before keeping/deleting.")
    parser.add_argument("--reverse", action="store_true", help="Reverse the sorting order")
    parser.add_argument("--ext", default=None, help="Only consider files with these extensions (comma-separated, e.g. .pdf,.jpg)")
    parser.add_argument("--exclude", default=None, help="Regex pattern for file names to exclude from deletion")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument("--logfile", default=None, help="File to write logs to (UTF-8, supports Unicode)")
    parser.add_argument("-y", "--yes", action="store_true", help="Do not prompt for confirmation, just delete")
    parser.add_argument("-r", "--recursive", action="store_true", help="Clean folders recursively (include all subfolders)")
    parser.add_argument("--older-than", type=int, default=0,
                        help="Only delete files older than this many minutes (default: 0, disabled)")
    parser.add_argument("folder_ids", nargs="+", help="One or more Google Drive folder IDs to clean")
    parser.add_argument("files_to_keep", help="Number of most recent files to keep", type=int)
    args = parser.parse_args()

    api = google_logon()
    total_summary = {'found': 0, 'kept': 0, 'deleted': 0, 'skipped': 0, 'errors': 0}

    for folder_id in args.folder_ids:
        if args.recursive:
            # Get all subfolders recursively, as list of dicts with id, name
            folder_list = get_all_folders(api, folder_id)
        else:
            # Only process the given folder, not its subfolders
            try:
                metadata = api.files().get(fileId=folder_id, fields="id, name").execute()
                folder_list = [{'id': folder_id, 'name': metadata.get('name', 'Unknown')}]
            except Exception as e:
                print(f"Could not retrieve folder name for {folder_id}: {e}")
                folder_list = [{'id': folder_id, 'name': str(folder_id)}]

        for folder in folder_list:
            fid = folder['id']
            fname = folder['name']
            print(f"\nCleaning folder: {fname} (ID: {fid})")
            summary = clean_drive(
                fid, fname, args.files_to_keep,
                test_mode=args.test_mode,
                query=partial(google_query, api),
                clean=partial(google_delete, api),
                sort_by=args.sort,
                reverse=args.reverse,
                ext_filter=args.ext,
                exclude_pattern=args.exclude,
                verbose=args.verbose,
                logfile=args.logfile,
                confirm=args.yes,
                older_than=args.older_than
            )
            for k in total_summary:
                total_summary[k] += summary.get(k, 0)

    print("\n=== SUMMARY ===")
    print(f"Total files found: {total_summary['found']}")
    print(f"Total kept: {total_summary['kept']}")
    print(f"Total deleted: {total_summary['deleted']}")
    print(f"Total skipped/errors: {total_summary['errors']}")
