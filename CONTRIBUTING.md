# Contributing to `linkedin-spider`

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

You can contribute in many ways:

# Types of Contributions

## Report Bugs

Report bugs at https://github.com/vertexcover-io/linkedin-spider/issues

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

## Fix Bugs

Look through the GitHub issues for bugs.
Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

## Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

## Write Documentation

linkedin-spider could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

## Submit Feedback

The best way to send feedback is to file an issue at https://github.com/vertexcover-io/linkedin-spider/issues.

If you are proposing a new feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

# Get Started!

Ready to contribute? Here's how to set up `linkedin-spider` for local development.
Please note this documentation assumes you already have `uv` and `Git` installed and ready to go.

1. Fork the `linkedin-spider` repo on GitHub.

2. Clone your fork locally:

```bash
cd <directory_in_which_repo_should_be_created>
git clone git@github.com:vertexcover-io/linkedin-spider.git
```

3. Now we need to install the environment. Navigate into the directory

```bash
cd linkedin-spider
```

Then, install and activate the environment with:

```bash
uv sync
```

4. Set up environment variables for authentication. Create a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env with your LinkedIn credentials
```

**Example .env file:**
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
HEADLESS=true
```

5. Install pre-commit to run linters/formatters at commit time:

```bash
uv run pre-commit install
```

6. Create a branch for local development:

```bash
git checkout -b name-of-your-bugfix-or-feature
```

Now you can make your changes locally.

7. Don't forget to add test cases for your added functionality to the `tests` directory.

8. When you're done making changes, check that your changes pass the formatting tests.

```bash
make check
```

Now, validate that all unit tests are passing:

```bash
make test
```

9. (Optional) For additional validation, you can run the MCP server locally to test your changes:

```bash
# Test the CLI
make run-cli

# Test the MCP server
make run-mcp
```

10. Commit your changes and push your branch to GitHub:

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

11. Submit a pull request through the GitHub website.

## Available Make Commands

For your convenience, here are the available make commands:

```bash
make help          # Show all available commands
make install       # Install dev dependencies and pre-commit hooks
make check         # Run code quality tools (linting, type checking)
make test          # Run tests with pytest
make build         # Build wheel file
make clean         # Clean build artifacts and cache
make run-cli       # Run LinkedIn spider CLI
make run-mcp       # Run LinkedIn spider MCP server
```

# Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated.
   Put your new functionality into a function with a docstring, and add the feature to the list in `README.md`.
