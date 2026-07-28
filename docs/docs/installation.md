---
layout: default
title: Installation
nav_order: 2
---

# Installation
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Step 1 - Required Dependencies

In order to install and run deemon, you'll need Python 3.8 or higher.

Please refer to [python.org](https://www.python.org/downloads/) for more information.

### Step 2 - Installing from source

Clone the repository and run the portable installer. It creates a `.venv` in the checkout and installs deemon in editable mode.

```bash
git clone https://github.com/deathrashed/deemon.git
cd deemon
./install.sh
```

Use the local command directly:

```bash
./.venv/bin/deemon --init
./.venv/bin/deemon --help
```

For a global command, install the checkout with `pipx install --editable .`.

## Configuration & First Use

Congrats! If you've made it this far, you have successfully installed deemon. 
There are a few things you should configure before using deemon. Head on over 
to the [configuration](configuration.md) page to learn more.
