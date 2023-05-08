#!/usr/bin/env pipenv-shebang
import os
import gitlab
import pprint


def gitlab_instance(gitlab_url, private_token):
    return gitlab.Gitlab(
        gitlab_url,
        private_token=private_token,
    )


def build_group_structure(groups, parent_id=None):
    groups_structure = {}
    for group in groups:
        if group.parent_id == parent_id:
            groups_structure[group.name] = {
                "path": group.path,
                "subgroups": build_group_structure(groups, group.id),
            }
    return groups_structure


def create_group_or_pass(gitlab_instance, group_name, group_path, parent_id=None):
    try:
        group_data = {"name": group_name, "path": group_path}
        if parent_id is not None:
            group_data["parent_id"] = parent_id
        gitlab_instance.groups.create(group_data)
        print(f"Create group : {group_name}")
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"Group {group_name} already exist, skip...")


def get_group_id_from_group_name(gitlab_instance, group_name):
    try:
        groups = gitlab_instance.groups.list(search=group_name, get_all=True)
    except gitlab.exceptions.GitlabGetError:
        print(f"error: group {group_name} not found")
        return None

    for group in groups:
        if group.name == group_name:
            return group.id
    return None


def create_groups_and_subgroups_recursive(
    gitlab_instance, groups_struct, parent_id=None
):
    for group_name, group_info in groups_struct.items():
        create_group_or_pass(gitlab_instance, group_name, group_info["path"], parent_id)
        group_id = get_group_id_from_group_name(gitlab_instance, group_name)
        if group_id is not None:
            create_groups_and_subgroups_recursive(
                gitlab_instance, group_info["subgroups"], group_id
            )


def create_project_from_subgroups_recursive(
    gl_com_inst, gl_onprem_inst, groups_struct, parent_id=None
):
    for group_name, group_info in groups_struct.items():
        print(f"create projects for group {group_name}")
        try:
            gl_com_group_id = get_group_id_from_group_name(gl_com_inst, group_name)
            gl_com_group = gl_com_inst.groups.get(gl_com_group_id)
            gl_com_projects = gl_com_group.projects.list(get_all=True)
            gl_onprem_group_id = get_group_id_from_group_name(
                gl_onprem_inst, group_name
            )
        except Exception as e:
            print(f"exception during create projects on groups {group_name}, skipping")
            break

        for project in gl_com_projects:
            try:
                print(f"create project {project.name}")
                gl_onprem_inst.projects.create(
                    {
                        "name": project.name,
                        "namespace_id": gl_onprem_group_id,
                        "description": project.description,
                    }
                )
            except gitlab.exceptions.GitlabCreateError:
                print(
                    f"project {project.name} already exists, skip project creation ..."
                )

        if group_info.get("subgroups"):
            create_project_from_subgroups_recursive(
                gl_com_inst, gl_onprem_inst, group_info["subgroups"], gl_onprem_group_id
            )


gitlab_com_token = os.getenv("GITLAB_COM_TOKEN")
gitlab_on_prem_token = os.getenv("GITLAB_ON_PREM_TOKEN")

gl_com_inst = gitlab_instance(os.getenv("GITLAB_COM_URL"), gitlab_com_token)
gl_onprem_inst = gitlab_instance(
    os.getenv("GITLAB_SELF_HOST_URL"), gitlab_on_prem_token
)

groups_struct = {}

gl_com_groups = gl_com_inst.groups.list(get_all=True)
groups_struct = build_group_structure(gl_com_groups)

create_groups_and_subgroups_recursive(gl_onprem_inst, groups_struct)
create_project_from_subgroups_recursive(
    gl_com_inst, gl_onprem_inst, groups_struct, parent_id=None
)
