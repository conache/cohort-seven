# Participate in the program

As a participant in the program, you should be using this repository. The goal of this repo is to be:

- An informational resource for how the EPF program operates.
- A coordination point for people participating in the program.
- A historical record of prior projects.
- A collection of useful resources for future program participants.

Please, be open with anything you wish to improve about these processes. Feel free to be bold and simply open a pull request with the changes and we can discuss them there.

## Development updates

One of the core goals of this program is to improve your technical writing and communication skills. One key way to do this is to get comfortable telling people about what you are working on. One of the expectations for program participants is a regularly cadenced development update. For the duration of the program, all participants should publish a development update at least once every two weeks.

A good development update can take many forms. Every individual will probably need to find their own style. Here are some suggestions:

- You don't need to explain everything, but sometimes it is good to try and explain things to see if you know how.
- A bulleted list of factual statements about what you worked on is a great place to start.
- Links are great. Forum posts. Pull requests. HackMD documents. Any resources you have been studying or creating. 

A great example is Danny Ryan's "finalized" series of development updates. Check out their update about their [work on the Merge devnets](https://blog.ethereum.org/2021/04/02/finalized-no-25/) for inspiration.
You can also check out [development updates from previous cohorts](https://github.com/eth-protocol-fellows/cohort-six/blob/master/development-updates.md). 

### Best practices

You should: 

- Post your first update within the first week of starting into the program, write about your initial research. 
- Post your update somewhere public. Publishing using an external blog, [HackMD](https://hackmd.io/c/tutorials/%2Fs%2Ftutorials) or own website are all great. Link it in the main [`development-updates.md` document](/development-updates.md) in the corresponding table. Open a PR from a branch dedicated to a specific week in your fork of the repo, check the [guide for using git below](#using-git-for-collaboration) for more details.
- Ensure that the content is published publicly before adding it's link in the [`development-updates.md` document](/development-updates.md). Trying out the link in your browser's incognito / private mode is a great way to test this.
- Make sure the markdown table is properly formatted before you push your commits. You can use a local IDE with markdown support, HackMD or [table formatting tool](https://github.com/nvuillam/markdown-table-formatter). The simplest option is to run the bundled formatter from the repo root: `python3 scripts/dev_updates.py format development-updates.md`.
- You don't need to worry much about merge conflicts on the table. An automation keeps `development-updates.md` mergeable: it merges the latest `main` into your PR without deleting anyone's data and re-formats the table. See [Automatic table merging](#automatic-table-merging) below.
- Share your development update to current thread in R&D Discord `#protocol-fellowship` channel.
- Not use an LLM or similar tech for generating your updates. The point is to exercise your technical writing and expressing ideas, generated updates won't be accepted.

### Using git for collaboration

The cohort coordination using a public repository is also meant to give you an experience of real-world collaboration in free open-source software (FOSS) development using [Git](https://git-scm.com/video/what-is-version-control). Git tracks changes to code, making collaboration on projects seamless, especially in FOSS where public repositories are the norm. Consider using the Git command line interface (CLI) over using GitHub's web interface. It's an important skill you can learn during the cohort that will serve you well throughout your career. Check out the resources on [using git in the epf.wiki](https://epf.wiki/#/wiki/dev/cs-resources?id=terminals-shell-scripting-and-version-control).

#### 1. Forking the repository and setting up your local environment 

Install [git](https://git-scm.com/) using a preferred method on your machine and set it up with your github SSH key. You need to [setup ssh](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) and [add the generated key to your github account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account) if you haven't done so yet. With your git setup complete, **fork the repo** to your github account (by clicking the Fork button) and clone the fork locally, for example: 

```
git clone git@github.com:<your-username>/cohort-seven.git
```
Now you have a local copy of the repo that you can use to update your fork. Let's add the main repository as an upstream named `epf7`: 
```
cd cohort-seven
git remote add epf7 https://github.com/eth-protocol-fellows/cohort-seven.git
```
This completes your one time setup of the repository.

#### 2. Keeping your local repository up to date

With the upstream added, you can keep your local repo updated by directly pulling from `epf7` upstream. If you already added your own commits on top of it, rebase it before opening a PR:
```
git fetch epf7
git rebase epf7/master
```

#### 3. Adding your updates

To add your update, update your local `main` branch, create a branch for the corresponding week and commit your edits: 
```
git checkout -b week1
emacs development-updates.md #add your update with your preferred editor
git add .
git commit
git push
```
After pushing to your fork of the repo, you are ready to open the PR. Got to the github page and create a PR from your weekly branch to the main branch of this repository. 

### Using `/projects/<project-name>.md`

Project deliverables should be posted in various open places such as the Research forum, the Ethereum Magicians forums, github gists, HackMd documents and this repository. 

Create a document under the path `/projects/<project-name>.md`. Take inspiration for writing your project from the [project template](/projects/project-template.md). Generally, your project document should include: 

- Basic description of project you are working on, scope, goals and roadmap
- All necessary links to repos where development is happening, documentation, research posts and technical background 
- List of participants working on the project

This document can be created later in the program when your project is mature enough and you are ready to present it. It's generally recommended around a month (week 4-6) into the fellowship.

### Using `/notes/<your-name>.md`

Feel free to create a document under the path `/notes/<your-name>.md`. This document should be used for things like:

- Aggregating links to reading resources you've found useful.
- Writing down notes about potential projects.
- Fleshing out full details of potential projects.
- Development updates.

This document isn't meant to be a "profile". It is meant to be used especially in the [first phases](/program-guide/program-details.md#phase-one) of the program where most of the exploration takes place. 

When submitting a PR, make sure you are using the latest main branch. Otherwise [rebase and keep your changes always on top](#2-keeping-your-local-repository-up-to-date) to be sure you are not deleting content of others.

When merging someone else's PR, use your best judgement and ask if you are unsure. 

If your IDE or system creates some hidden config files (e.g. `.vscode/...`), please make sure you don't upload them to the repo by updating the `.gitignore`. 

### Automatic table merging

`development-updates.md` is a single large table edited by everyone, so PRs frequently show merge conflicts even when two people just filled different cells. This is caused by markdown column-width whitespace, not by real conflicting edits. The repo automates the fix so you rarely need to resolve a conflict by hand.

**What runs automatically**

- A GitHub Action ([`.github/workflows/auto-merge-dev-updates.yml`](/.github/workflows/auto-merge-dev-updates.yml)) runs whenever a PR touching the table is opened or updated. It merges the latest base branch into your PR branch using a *semantic* table merge, re-formats the table, and pushes the result back to your branch. It keeps everyone's existing data (filled cells and rows are never deleted) and adds your update on top. When the run is green, your PR is mergeable.
- To run it on an existing/older PR (one opened before this automation existed, so the workflow never fired on it), a maintainer goes to **Actions → dev-updates mergeable → Run workflow** and enters the PR number. Pushing any new commit to the PR also triggers it.
- For the action to push to your fork branch, keep **"Allow edits by maintainers"** checked when opening the PR (it's on by default). If it's off, the run fails and you can run the formatter yourself (below).
- Only genuine conflicts (two different links in the *same* cell) make the run fail; resolve those manually by looking for `<!-- CONFLICT ... -->` markers.

**Doing it locally**

The same logic lives in [`scripts/dev_updates.py`](/scripts/dev_updates.py) (Python 3, no dependencies):

```
# format the table canonically (idempotent)
python3 scripts/dev_updates.py format development-updates.md

# one-time: make `git merge`/`rebase`/`pull` resolve the table automatically
bash scripts/setup-merge-driver.sh
```

After running the setup script once, keeping your branch in sync (`git rebase epf7/main` or `git pull`) merges the table for you without conflicts.
