# Initial Certificate Generation

Use this if certificates have not been generated before on the current server.

## Option 1 - Copying Existing Certificates from Elsewhere
If there are existing certificates somewhere, they can be copied into the `certs` folder here and will automatically get synced to the Nginx and Certbot containers. The folder structure should look like this, where `DOMAIN_NAME` is the same value set in the `dockerenv` file (see top-level instructions):
   * `certs/live/<DOMAIN_NAME>/fullchain.pem`
   * `certs/live/<DOMAIN_NAME>/privkey.pem`

## Option 2 - Generating Fresh Certificates
1. Fill in the actual EMAIL and DOMAIN NAME in the `docker-compose.yml` file here and save.

   _TODO: Figure out why these aren't being picked up from the env file._

2. Run `docker-compose up certbot` to start the Certbot service and obtain certificates.
3. Once Certbot successfully obtains the certificates, stop the Certbot container. The renewal service in the main `docker-compose` file will renew the certificates going forward.
