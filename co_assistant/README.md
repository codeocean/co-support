# Code Ocean Command-Line Assistant

## Installation

To install the Co-Assistant, run the following command:

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

To use the Co-Assistant Prerequisite Checker, execute the following command with the appropriate AWS region and account ID:

```bash
co-assistant check-prerequisites ...
```

## Example

Here is an example of how to run the checker:

```bash
co-assistant check-prerequisites ...
```

## Note

Currently, this assistant only checks prerequisites for Code Ocean deployment.
