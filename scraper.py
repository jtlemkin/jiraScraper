import requests
from dateutil.parser import parse
from datetime import timedelta
import os
import json
import sys
import pygit2
from datetime import datetime
import csv


class IssueNotExistingError(Exception):
    """Raised when the issue does not exist in Jira"""
    pass


def get_jira_json(project, url, i):
    json_file_path = "data/json/" + project + "/" + str(i) + "_issue.json"

    try:
        f = open(json_file_path, "r")
    except FileNotFoundError:
        issue_url = url + str(i)
        resp = requests.get(issue_url)

        if resp.status_code != 200:
            raise IssueNotExistingError

        # print(json.dumps(resp.json(), indent=4))

        jira_json = resp.json()

        with open(json_file_path, "w+") as f:
            json.dump(jira_json, f)
    else:
        jira_json = json.load(f)
        f.close()

    return jira_json


def get_issue_links(jira_json):
    json_issuelinks = jira_json["fields"]["issuelinks"]

    breaks = "NONE"
    is_broken_by = "NONE"

    # assumes only one link breaks link and is broken by link per issue
    for link in json_issuelinks:
        if "outwardIssue" in link and link["type"]["outward"] == "breaks":
            breaks = link["outwardIssue"]["key"]

        if "inwardIssue" in link and link["type"]["inward"] == "is broken by":
            is_broken_by = link["inwardIssue"]["key"]

    return breaks, is_broken_by


def get_type(jira_json):
    return jira_json["fields"]["issuetype"]["name"]


def write_issue_to_file(file, project, url, i):
    try:
        jira_json = get_jira_json(project, url, i)
    except IssueNotExistingError:
        raise

    bug_id = project + "-" + str(i)
    print(bug_id)

    issue_type = get_type(jira_json)
    priority = get_priority(jira_json)
    time_to_fix = get_time_to_fix(jira_json)
    number_of_comments = get_number_of_comments(jira_json)
    number_of_commenters = get_number_of_commenters(jira_json)
    breaks, is_broken_by = get_issue_links(jira_json)

    file.write("{0},{7},{1},{2:0.3f},{3},{4},{5},{6}\n".format(bug_id, priority, time_to_fix, number_of_comments,
                                                               number_of_commenters, breaks, is_broken_by, issue_type))


def get_priority(resp_json):
    return resp_json["fields"]["priority"]["name"]


def get_time_to_fix(resp_json):
    status = resp_json["fields"]["status"]["name"]
    if (status == "Closed" or status == "Resolved") and resp_json["fields"]["resolutiondate"]:
        resolution_date = parse(resp_json["fields"]["resolutiondate"])
        creation_date = parse(resp_json["fields"]["created"])

        time_to_fix = resolution_date - creation_date
        time_to_fix_in_days = time_to_fix / timedelta(days=1)

        return time_to_fix_in_days
    else:
        # -1 indicates that the issue has not been fixed
        return -1


def get_number_of_comments(resp_json):
    comments = resp_json["fields"]["comment"]["comments"]
    return len(comments)


def get_number_of_commenters(resp_json):
    authors = set()

    comments = resp_json["fields"]["comment"]["comments"]
    for comment in comments:
        authors.add(comment["author"]["name"])

    return len(authors)


def create_dirs(project):
    os.makedirs("data/json/" + project, exist_ok=True)
    os.makedirs("data/csvs/", exist_ok=True)
    os.makedirs("data/starts", exist_ok=True)


def scrape(project, task):
    print("PROCESSING " + project)

    base_url = "https://issues.apache.org/jira/rest/api/latest/issue/"

    create_dirs(project)

    # fname = "data/csvs/" + project + ".csv"
    fname = "data/csvs/" + project + "_commits.csv"

    repo = pygit2.Repository("../apache/" + project.lower())

    ranges = {"ACCUMULO": range(2460, 4675),
              "AMBARI": range(6271, 22780),
              "HADOOP": range(6243, 13891),
              "JCR": range(892, 4119),
              "LUCENE": range(701, 11184),
              "OOZIE": range(609, 3316)
              }

    with open(fname, "a+") as f:
        # this isn't a good method but shouldn't be too much of an issue because the file shouldn't get too large
        def get_start():
            try:
                with open("data/starts/" + project + "_start.txt", "r") as t:
                    try:
                        start = int(t.readline())
                    except ValueError:
                        return 1

                return start
            except FileNotFoundError:
                return 1

        start = get_start()

        if start == 1:
            # f.write("bug_id,issue_type,severity,days_to_close,num_comments,num_commenters,breaks,is_broken_by\n")
            f.write("sha,bug_id,num_files,file_types,avg_line_age,num_owners\n")
            start = ranges[project].start

        issue_no = 0

        def write_all_issues_to_file():
            nonlocal issue_no
            issue_no = start
            consecutive_missed = 0

            threshold_for_missed = 20

            while issue_no < ranges[project].stop:
                try:
                    # task(f, project, project_url, issue_no)
                    task(f, project, issue_no, repo)
                except IssueNotExistingError:
                    consecutive_missed += 1

                    if consecutive_missed < threshold_for_missed:
                        pass
                    else:
                        print("Terminating at issue " + str(issue_no))
                        return
                else:
                    consecutive_missed = 0
                finally:
                    with open("data/starts/" + project + "_start.txt", "w+") as t:
                        t.write(str(issue_no))

                issue_no += 1

        write_all_issues_to_file()

    print("Done scraping", project, "at", issue_no, "\n")


def get_issue_commits(repo, project, issue_no):
    last = repo[repo.head.target]

    project_id = project + "-" + str(issue_no) + " "

    commits = []

    found_match = False
    num_commits_since_match = 0

    for commit in repo.walk(last.id, pygit2.GIT_SORT_TIME):
        if project_id in commit.message:
            commits.append(commit)

        # This makes the assumption that commits pertaining to the same issue are not too far away
        if found_match:
            num_commits_since_match += 1

        if num_commits_since_match > 100:
            break

    return commits


def write_issue_commits_to_file(f, project, issue_no, repo):
    commits = get_issue_commits(repo, project, issue_no)

    bug_id = project + "-" + str(issue_no)

    print(project, "ISSUE NUMBER", issue_no, "\n")

    for commit in commits:

        diff = repo.diff(commit.parents[0], commit, context_lines=0)

        num_files_changed = diff.stats.files_changed
        kinds_of_files = set()
        sum_age_of_lines = 0
        num_lines = 0
        owners = set()

        for patch in diff:
            old_file = patch.delta.old_file.path
            kinds_of_files.add(old_file.split('.')[-1])

            print(datetime.now())

            for hunk in patch.hunks:
                if hunk.old_lines:

                    num_lines += hunk.old_lines

                    blame = repo.blame(old_file, newest_commit=commit.parents[0].hex, min_line=hunk.old_start,
                                       max_line=hunk.old_start + hunk.old_lines - 1, flags=pygit2.GIT_BLAME_NORMAL)

                    for bh in blame:
                        blamed_sha = bh.final_commit_id.hex

                        blamed_commit = repo.revparse_single(blamed_sha)

                        age_of_line = commit.commit_time - blamed_commit.commit_time
                        sum_age_of_lines += age_of_line
                        owners.add(blamed_commit.committer.name)

        if num_lines == 0:
            continue

        avg_age_of_lines = sum_age_of_lines / num_lines

        file_types = ' '.join(kinds_of_files)

        f.write("{},{},{},{},{},{}\n".format(commit.hex, bug_id, num_files_changed, file_types, avg_age_of_lines,
                                             len(owners)))


class CommitData:
    def __init__(self, num_files_changed, files_types, avg_age_of_lines, owners, files):
        self.num_files_changed = num_files_changed
        self.files_types = files_types
        self.avg_age_of_lines = avg_age_of_lines
        self.owners = owners
        self.files = files


def get_commit_data(shas, repo):
    commit_data = {}

    for sha in shas:
        try:
            commit = repo.revparse_single(sha)
        except KeyError:
            print("Skipping sha", sha, "\n");
            continue

        diff = repo.diff(commit.parents[0], commit, context_lines=0)

        num_files_changed = diff.stats.files_changed
        kinds_of_files = set()
        sum_age_of_lines = 0
        num_lines = 0
        owners = set()
        files = set()

        for patch in diff:
            old_file = patch.delta.old_file.path
            kinds_of_files.add(old_file.split('.')[-1])
            files.add(old_file)

            for hunk in patch.hunks:
                if hunk.old_lines:

                    num_lines += hunk.old_lines

                    blame = repo.blame(old_file, newest_commit=commit.parents[0].hex, min_line=hunk.old_start,
                                       max_line=hunk.old_start + hunk.old_lines - 1,
                                       flags=pygit2.GIT_BLAME_NORMAL)

                    for bh in blame:
                        blamed_sha = bh.final_commit_id.hex

                        blamed_commit = repo.revparse_single(blamed_sha)

                        age_of_line = commit.commit_time - blamed_commit.commit_time
                        sum_age_of_lines += age_of_line
                        owners.add(blamed_commit.committer.name)

        if num_lines == 0:
            continue

        avg_age_of_lines = sum_age_of_lines / num_lines

        file_types = ' '.join(kinds_of_files)

        commit_data[sha] = CommitData(num_files_changed, file_types, avg_age_of_lines, owners, files)

    return commit_data


def get_bug_files(shas, commit_data):
    files = set()

    for sha in shas:
        try:
            files = files.union(commit_data[sha].files)
        except KeyError:
            continue

    return files


def get_szz_assumptions(project):
    print("PROCESSING " + project + "\n")

    create_dirs(project)

    fname = "data/csvs/" + project + "_assumptions.csv"

    repo = pygit2.Repository("../../apache/" + project.lower())

    with open(fname, "a+") as f:
        with open('../../InduceBenchmark/' + project + '.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')

            issues = set()

            next(csv_reader)

            for row in csv_reader:
                fixes = row[1].split(',')
                bugs = row[2].split(',')

                commit_data = get_commit_data(fixes + bugs, repo)

                bug_files = get_bug_files(bugs, commit_data)

                for sha in fixes:
                    try:
                        commit = commit_data[sha]
                    except KeyError:
                        continue

                    print(datetime.now(), "Writing", sha, "to csv\n")

                    if commit.files.intersection(bug_files):
                        f.write(
                            "{},{},{},{},{},{},{}\n".format(sha, row[0], commit.num_files_changed, commit.files_types,
                                                            commit.avg_age_of_lines, len(commit.owners), 1))
                    else:
                        f.write(
                            "{},{},{},{},{},{},{}\n".format(sha, row[0], commit.num_files_changed, commit.files_types,
                                                            commit.avg_age_of_lines, len(commit.owners), 0))

            print("Finished processing", project, "\n")

            return issues


# scrape(sys.argv[1], write_issue_to_file)


if sys.argv[2] == 'd':
    scrape(sys.argv[1], write_issue_commits_to_file)
else:
    get_szz_assumptions(sys.argv[1])
