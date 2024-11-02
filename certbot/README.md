# Initial Certificate Generation

Use this if certificates have not been generated before on the current server.

If there are existing certificates somewhere, you can just copy them into the `certs` folder and skip the steps below.

1. Update `DOMAIN_NAME` and `CERTBOT_EMAIL` in `dockerenv` in the top-level folder.
2. Run `docker-compose up certbot` to start the Certbot service and obtain certificates.
3. Once Certbot successfully obtains the certificates, stop the Certbot container. The renewal service in the main `docker-compose` file will renew the certificates going forward.
