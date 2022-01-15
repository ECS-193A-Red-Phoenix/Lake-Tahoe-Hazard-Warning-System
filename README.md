# Lake Tahoe Hazard Warning System

A web and mobile app that uses a 3D hydrodynamic model to create a hazardous map of Lake Tahoe, and push real-time warning notifications to users.

Get started by cloning this repository:

`git clone https://github.com/ECS-193A-Red-Phoenix/LakeTahoe-HazardWarningSystem.git`

# General Workflow

Only push changes to directly to main branch if it's a trivial change, or if it makes sense to push it without needing review.
Otherwise, the general workflow is summarized by this image

Every time you start working make sure your local repo is up to date by calling

`git pull`

This will merge any changes on github into your current branch.

1. Make a new branch for the feature you're working on

    `git checkout -b <my_branch_name>`

2. Work on implementing the feature and adding as many commits as you want

    `git commit -m "Added ..."`

3. When the feature is done, push your branch to github

   `git push origin <my_branch_name>`

4. Create a pull request by following the link shown from the previous step
   - To speed up development, anyone of us can review and accept pull requests

5. Checkout to main branch

   `git checkout main`