import os
import glob
import yaml
import sys


def list_tags(data):
    excluded_tags = ("k8s", "always")
    roles = {}
    for role in data.get("roles", []):
        tags = role.get('tags', None)
        name = role.get("role")
        if not tags:
            raise Exception(f"role '{name}' should define at least one tag.")
        roles[name] = [x for x in tags if x not in excluded_tags]

    tasks = {}
    for task in [x for x in data.get("tasks") if "include_tasks" in x]:
        tags = task["include_tasks"]["apply"]["tags"]
        name = os.path.basename(task["include_tasks"]["file"])
        tasks[name] = {
            'file': task["include_tasks"]["file"],
            'tags': [x for x in tags if x not in excluded_tags],
        }
    return roles, tasks


def validate_roles(roles, all_tags, ignore_data):
    # assert that at least one role tag is included
    errors = []
    for rol in roles:
        if not any(x in all_tags for x in roles.get(rol)):
            errors.append(f"role {rol} has no tag included into tags_*.txt files")

    # assert that all roles are tested
    for rol in glob.glob("molecule/default/roles/*"):
        base_rol = os.path.basename(rol)
        if "ignore_roles" in ignore_data and base_rol in ignore_data['ignore_roles']:
            print(f"\033[0;33minfo: ignoring role: {base_rol}\033[0m")
            continue

        if os.path.isdir(rol) and base_rol not in roles:
            errors.append(f"role {base_rol} is not included into converge.")
    return errors


def validate_tasks(tasks, all_tags, ignore_data):
    # assert that at least one task tag is included
    errors = []
    for t in tasks:
        if not any(x in all_tags for x in tasks[t].get('tags')):
            errors.append(f"task {t} has no tag included into tags_*.txt files")

    # assert that all tasks are tested
    def _is_task_included(task_file, tasks):
        for t in tasks:
            if task_file.endswith(tasks.get(t).get('file')):
                return True
        return False

    for task_file in glob.glob("molecule/default/tasks/*"):
        base_task = os.path.basename(task_file)
        if "ignore_tasks" in ignore_data and base_task in ignore_data['ignore_tasks']:
            print(f"\033[0;33minfo: ignoring task: {base_task}\033[0m")
            continue
        if os.path.isfile(task_file) and not _is_task_included(task_file, tasks):
            errors.append(f"task {task_file} is not included into converge.")
    return errors


def parse_ignore():
    out = []
    ignore_file = ".taglint"
    if os.path.isfile(ignore_file):
        with open(ignore_file) as f:
            out = yaml.safe_load(f)
    return out


def main():
    converge = "molecule/default/converge.yml"
    if not os.path.isfile(converge):
        sys.stderr.write(f"missing mandatory {converge} for default molecule scenario\n.")
        sys.exit(1)

    ignore_data = parse_ignore()

    # Parse converge file and list tags
    try:
        with open(converge) as file:
            for data in yaml.safe_load(file):
                if data.get("name", None) == "Converge" and "tasks" in data and isinstance(data.get("tasks"), list):
                    roles, tasks = list_tags(data)
                    # list all tags
                    all_tags = []
                    for t in glob.glob('molecule/default/tags_*.txt'):
                        with open(t) as fh:
                            all_tags += [x for x in fh.read().split('\n') if x]
                    errors = validate_roles(roles, all_tags, ignore_data)
                    errors += validate_tasks(tasks, all_tags, ignore_data)
                    if errors:
                        msg = '\n  - '.join(errors)
                        print(f"\033[0;31merrors\033[0m:\n  - {msg}")
                        sys.exit(1)
                    sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"raise: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
