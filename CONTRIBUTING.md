# Contributing to Gemini Gateway

First off, thank you for considering contributing to Gemini Gateway! It's people like you that make Gemini Gateway such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, [make one](https://github.com/thuanha-groove/gemini-gateway/issues/new)! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

### Fork & create a branch

If this is something you think you can fix, then [fork Gemini Gateway](https://github.com/thuanha-groove/gemini-gateway/fork) and create a branch with a descriptive name.

A good branch name would be (where issue #33 is the ticket you're working on):

```sh
git checkout -b 33-add-new-feature
```

### Get the test suite running

Be sure to have a working test suite so that you can ensure your changes don't break existing functionality.

### Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first 😸

### Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with Gemini Gateway's master branch:

```sh
git remote add upstream git@github.com:thuanha-groove/gemini-gateway.git
git checkout master
git pull upstream master
```

Then update your feature branch from your local copy of master, and push it!

```sh
git checkout 33-add-new-feature
git rebase master
git push --force-with-lease origin 33-add-new-feature
```

Finally, go to GitHub and [make a Pull Request](https://github.com/thuanha-groove/gemini-gateway/compare)

### Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

To learn more about rebasing and merging, check out this guide on [syncing a fork](https://help.github.com/articles/syncing-a-fork).

We're happy to help you get your PR's merged in, so feel free to ask for help!
