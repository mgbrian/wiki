# Wiki

## Deployment

### Sans Docker

The installer script below has only been written to target macOS, Debian or Alpine. The app itself should work on any Unix-based OS but you'll have to figure out the installation process (or just use Docker!).

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

4. Populate the environment variables accordingly:

   ```
   source .requirements/bin/activate && python3 manage.py migrate
   ```

5. Make the app runner script executable.

   ```
   chmod +x start.sh
   ```

#### Running the Server

**Either** Run the app's dev server directly:

   ```
   source .requirements/bin/activate && python3 app.py
   ```

**OR** Run the start script. This runs the app using Hypercorn:

   ```
   ./start.sh
   ```

### With Docker

1. Duplicate `dockerenv_sample` into `dockerenv` and update all variables accordingly. If this is not a production deployment, don't set `DOMAIN_NAME`, and skip step 2 below.
2. Obtain SSL certificates if this hasn't been done before for the current server. Follow the steps in [certbot/README.md](certbot/README.md).
3. `docker compose up --build` or `sudo docker compose up --build` if you get a permission error (this may happen due to the certificates folder created by Certbot in step 2 being restricted).

   (`<PORT>` and `<DOMAIN_NAME>` as set in `dockerenv`)

   - The site should be accessible at `http://localhost:<PORT>` locally. This offers direct access to the app server (Hypercorn).
   - If all the steps above were followed, it should be accessible at `https://localhost` locally or publicly at `https://<DOMAIN_NAME>`. This uses Nginx as an added layer in front of the app server.

   Visually the two options look something like this:
   ```
      [BROWSER] --> [Hypercorn on port <PORT>] --> [APP]
      [BROWSER] --> [Nginx on port 80/443] --> [Hypercorn on port <PORT>] --> [APP]
   ```
