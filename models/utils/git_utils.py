import os
import re
import datetime
import subprocess

from dataclasses import dataclass
from utils.nvd_utils import NVD
from pydriller import Repository


@dataclass
class Commit:
    commit_id: str = None
    subject: str = None
    changed_files: list = None
    add_lines: list = None
    rm_lines: list = None
    a_file_nums: int = 0
    i_line_nums: int = 0
    d_line_nums: int = 0
    a_line_nums: int = 0
    method_name: list = None
    a_method_nums: int = 0


class CommitUtils:
    time_delta = 90
    REPOS_PATH = "./repos"

    # gain commits id list by nvd publish date
    def get_commits(self, nvd_page: NVD, repos_path: str):
        pub_date = nvd_page.pub_date.split(" ")[0]
        since = datetime.datetime.strptime(
            pub_date, "%Y-%m-%d") - datetime.timedelta(days=self.time_delta)
        to = datetime.datetime.strptime(
            pub_date, "%Y-%m-%d") + datetime.timedelta(days=self.time_delta)

        commits=[]
        for commit in Repository(path_to_repo=repos_path, since=since,to=to).traverse_commits():
            commits.append(commit.hash)

        return list(set(commits))

    # gain patch information by commit id
    def __get_patch(self, repos, commit_id):
        cmd = f"git format-patch -1 --stdout {commit_id}"

        p = self.__excute_git_cmd(self.REPOS_PATH, repos, cmd)

        return p

    # excute git command
    def __excute_git_cmd(self, repos_path: str, cmd: str):
        pwd = os.getcwd()
        os.chdir(repos_path)
        output = subprocess.check_output(
            cmd, shell=True).decode("utf-8", errors="ignore")
        os.chdir(pwd)
        return output

    # extract vulnerability type & impact & function
    def get_commit_info(self, repos, commit_id) -> Commit:
        commit_info = self.mining_commit_information(repos, commit_id)[0]
        return commit_info

    # mining commit information
    def mining_commit_information(self, repos: str, commit_id) -> list[Commit]:
        commit_info_list = []
        for commit in Repository(path_to_repo=repos, only_commits=[commit_id]).traverse_commits():
            subject = commit.msg
            a_line_nums = commit.lines
            i_line_nums = 0
            d_line_nums = 0
            method_name = []
            changed_files = []
            a_file_nums = len(commit.modified_files)
            for files in commit.modified_files:
                i_line_nums += files.added_lines
                d_line_nums += files.deleted_lines
                for method in files.changed_methods:
                    method_name.append(method.name)
                changed_files.append(files.filename)
            a_method_nums = len(method_name)
            commit_info_list.append(
                Commit(commit_id=commit.hash,
                       subject=subject,
                       changed_files=changed_files,
                       a_line_nums=a_line_nums,
                       i_line_nums=i_line_nums,
                       d_line_nums=d_line_nums,
                       method_name=method_name,
                       a_file_nums=a_file_nums,
                       a_method_nums=a_method_nums))
        return commit_info_list

    # utilize CodeBert to compute patch probability
    def __compute_patch_prob(self, rm_lines: list, add_lines: list):
        pass
