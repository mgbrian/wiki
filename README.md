# Wiki

## Installation
This is only expected to work macOS/Linux/Unix+.

**The first time you pull the repository, run:**
***

  ```
  chmod +x install.sh
  ```

  ```
  ./install.sh
  ```

The second step will install all requirements in a `venv` and collect all required
environment variables in an `env.py`. Update this accordingly and run:

  ```
  python3 manage.py migrate
  ```

You just need to supply database connection details, if the database is not created this will create it for you before setting up the tables.

### Running the Server
**For all subsequent runs, ensure the venv is activated:**

```
source .requirements/bin/activate
```

Then run the server:
```
python3 app.py
```
