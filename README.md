# Code Ocean Support Command-Line

## Installation

To install the co-support, run the following command:

```bash
pip install .
```

## Setting up with virtualenv

1. Create a virtual environment:
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

## Usage

To use the co-support Prerequisite Checker, execute the following command with the appropriate AWS region and account ID:

```bash
co-support check-prerequisites ...
```

## Example

Here is an example of how to run the checker:

```bash
co-support check-prerequisites ...
```

## Note

Currently, this tool only checks prerequisites for Code Ocean deployment.
