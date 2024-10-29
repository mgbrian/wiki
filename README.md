# Wiki

## Deployment

### Sans Docker

This is only expected to work well on macOS/Debian (and derivatives)/Alpine.

**The first time you pull the repository, run:**

---

1. On macOS, ensure [Homebrew](https://brew.sh/) and [Ollama](https://ollama.com/download) are installed.

2. Make the install script executable:

```
chmod +x install.sh
```

3. Run the install script.

```
./install.sh
```

The installation step will install all requirements in a `venv` and collect all required
environment variables in an `env.py`. 

4. Populate the environment variables accordingly and run the command below to set up the database (this will automatically create it if it doesn't already exist before setting up the tables): 

```
python3 manage.py migrate
```

#### Running the Server

**For all subsequent runs, ensure the venv is activated:**

```
source .requirements/bin/activate
```

Then run the server:

```
python3 app.py
```

### With Docker

1. Update `dockerenv` accordingly.
2. Obtain SSL certificates if this hasn't been done before. Update <DOMAIN_NAME> below accordingly and run:

```
  docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d <DOMAIN_NAME in dockerenv>
```

3. `docker compose up`

4. This should be accessible at `http://localhost` locally, or publicly at the set domain.
