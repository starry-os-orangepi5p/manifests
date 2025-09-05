Starry-Mix Manifests (repo)
=================================

This repository defines a multi-repo workspace for the Google `repo` tool.

Usage
-----
- Install `repo` (Linux):
  - `mkdir -p "$HOME/bin" && curl -fsSL https://storage.googleapis.com/git-repo-downloads/repo -o "$HOME/bin/repo" && chmod +x "$HOME/bin/repo" && export PATH="$HOME/bin:$PATH"`

- Clone with public GitHub remotes (recommended):
  - `repo init -u <this-manifest-repo-url> -b main -m default.xml`
  - `repo sync -j8`

- Clone from an existing local workspace (offline/dev):
  - `repo init -u file:///absolute/path/to/this/manifests -b main -m local.xml`
  - `repo sync -j8`

Manifests
---------
- `default.xml`: Uses GitHub remote `https://github.com/Starry-Mix-THU` and pins non-main branches where needed.
- `local.xml`: Uses `file://` remote pointing to an existing workspace path; includes `box/` and other local-only projects.
- `locked.xml`: Pins every project to the exact local HEAD commit.

Groups
------
- `core`: main OS and orchestration repos.
- `plats`: platform-specific support.
- `crates`, `drivers`, `fs`, `net`, `tools`, `backup` as labeled.

Common Commands
---------------
- Sync all: `repo sync -j8`
- Partial sync by group: `repo sync -g core,plats`
- List projects: `repo list`

Regenerate locked.xml
---------------------
- From `manifests/`: `python3 scripts/gen_locked.py -i default.xml -o locked.xml`
- Include local-only repos (e.g., `box/`): `python3 scripts/gen_locked.py -i local.xml -o locked.xml`
