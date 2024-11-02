# Initial Certificate Generation

Use this if certificates have not been generated before on the current server.

If there are existing certificates somewhere, you can just copy them into the `certs` folder and skip the steps below.

1. Fill in the EMAIL and DOMAIN NAME in `docker-compose.yml` and save.

   _TODO: Figure out why these aren't being picked up from the env file._

2. Run `docker-compose up certbot` to start the Certbot service and obtain certificates.
3. Once Certbot successfully obtains the certificates, stop the Certbot container. The renewal service in the main `docker-compose` file will renew the certificates going forward.
