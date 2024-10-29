# Wiki

## Deployment

### Sans Docker

The installer script below has only been written to target macOS, Debian or Alpine. The app itself should work on any Unix OS but you'll have to figure out the installation process.

**The first time you pull the repository:**

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
    
    The installation step will install all requirements in a `venv` folder named `.requirements` and collect all required
    environment variables in a file named `env.py`. 

4. Populate the environment variables accordingly and run the command below to set up the database (this will automatically create it if it doesn't already exist before setting up the tables): 

    ```
    source .requirements/bin/activate && python3 manage.py migrate
    ```

#### Running the Server

1. For all subsequent runs, ensure the venv is activated:

    ```
    source .requirements/bin/activate
    ```

2. Then run the server:

    ```
    python3 app.py
    ```

### With Docker

1. Update `dockerenv` accordingly. Skip setting `DOMAIN_NAME`, and step 2 below if this is not a production deployment.
2. Obtain SSL certificates if this hasn't been done before. Update `<DOMAIN_NAME>` below accordingly and run:

```
  docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d <DOMAIN_NAME>
```

3. `docker compose up`

    - The site should be accessible at `http://localhost:<PORT>` locally. This offers direct access to the app server.
    - If all the steps above were followed, it should be accessible at `https://localhost` locally or publicly at `https://<DOMAIN_NAME>`. This uses Nginx as an added layer in front of the app server.

        (`<PORT>` and `<DOMAIN_NAME>` as set in `dockerenv`)
