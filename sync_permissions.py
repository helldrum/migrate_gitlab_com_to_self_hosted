#!/usr/bin/env pipenv-shebang
import gitlab
import os
import sys
import yaml


def gitlab_instance(gitlab_url, private_token):
    return gitlab.Gitlab(
        gitlab_url,
        private_token=private_token,
    )


def get_groups_permission(gitlab_instance, permissions):
    print("get group permissions")
    for group in gitlab_instance.groups.list(all=True, membership=True):
        print(".", end="")
        sys.stdout.flush()
        for member in group.members.list():
            permissions[member.name] = {
                "email": "you need to set it manually !",
                "groups": [],
            }
            permissions[member.name]["groups"].append({group.name: member.access_level})
    return permissions


def get_project_permission(gitlab_instance, permissions):
    print("get project permissions")
    for project in gitlab_instance.projects.list(all=True, membership=True):
        print(".", end="")
        sys.stdout.flush()
        try:
            for member in project.members.list():
                permissions[member.name] = {
                    "email": "you need to set it manually !",
                    "projects": [],
                }
                permissions[member.name]["projects"].append(
                    {project.name: member.access_level}
                )
        except Exception as e:
            print(f"exclude permission for user {e}")
    return permissions


def invite_user_on_groups(gitlab_instance, permissions):
    for user in permissions:
        for group in gitlab_instance.groups.list(all=True, membership=True):
            for usr_group in permissions[user].get("groups",[]):
                if group.name in usr_group:
                    print (f"group name : {group.name}")
                    print(
                        {"email": permissions[user]["email"],"access_level": usr_group[group.name]}
                    )
                    try:
                        invitation = group.invitations.create(
                            {
                                "email": permissions[user]["email"],
                                "access_level": usr_group[group.name],
                            }
                        )
                    except (gitlab.exceptions.GitlabCreateError,gitlab.exceptions.GitlabInvitationError) as e:
                        print("error during group invitation for user {user} {e}.")


def invite_user_on_project(gitlab_instance, permissions):
    for user in permissions:
        for project in gitlab_instance.projects.list(all=True, membership=True):
            for usr_project in permissions[user].get("projects",[]):
                if project.name in usr_project:
                    print (f"project name : {project.name}")
                    print(
                        {"email": permissions[user]["email"],"access_level": usr_project[project.name]}
                    )
                    try:
                        invitation = project.invitations.create(
                            {
                                "email": permissions[user]["email"],
                                "access_level": usr_project[project.name],
                            }
                        )
                    except (gitlab.exceptions.GitlabCreateError,gitlab.exceptions.GitlabInvitationError) as e:
                        print("error during group invitation for user {user} {e}.")


def load_data_if_file_exist(yaml_file):
    if os.path.exists(yaml_file):
        with open(yaml_file, "r") as file:
            return yaml.safe_load(file)
    return {}


def dump_dict_to_yaml_file(yaml_file, permissions):
    with open(yaml_file, "w") as file:
        yaml.dump(permissions, file)


def yes_response_or_exit(prompt):
    while True:
        response = input(prompt + " (yes/no): ").lower()
        if response in ["yes", "y"]:
            return True
        sys.exit(-1)


gitlab_com_token = os.getenv("GITLAB_COM_TOKEN")
gitlab_on_prem_token = os.getenv("GITLAB_ON_PREM_TOKEN")

gl_com_inst = gitlab_instance(os.getenv("GITLAB_COM_URL"), gitlab_com_token)
gl_onprem_inst = gitlab_instance(
    os.getenv("GITLAB_SELF_HOST_URL"), gitlab_on_prem_token
)

permissions = {}

script_path = os.path.dirname(os.path.abspath(__file__))
yaml_file = os.path.join(script_path, "permissions.yaml")
permissions = load_data_if_file_exist(yaml_file)
if permissions:
    yes_response_or_exit(
        """permission file found, would you like to apply thoses permissions ? 
(you should review the script before, and complete emails adresse to make it works)"""
    )
    invite_user_on_groups(gl_onprem_inst, permissions)
    invite_user_on_project(gl_onprem_inst, permissions)
else:
    print("permission file not found, get groups and projects users permissions.")
    permissions = {}
    permissions = get_groups_permission(gl_com_inst, permissions)
    permissions = get_project_permission(gl_com_inst, permissions)
    dump_dict_to_yaml_file(yaml_file, permissions)
