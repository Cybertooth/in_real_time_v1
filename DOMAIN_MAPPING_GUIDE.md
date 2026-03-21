# Custom Domain Mapping for Cloud Run

To avoid the URL changing with every deployment and to use your own domain (`riju.dev`), follow these steps.

## Option 1: Cloud Run Domain Mapping (Easiest)

Google Cloud Run allows you to map a custom domain directly to your service.

1.  **Go to Cloud Run in GCP Console**: Navigate to the [Cloud Run page](https://console.cloud.google.com/run).
2.  **Manage Custom Domains**: Click on **Manage Custom Domains** at the top.
3.  **Add Mapping**:
    *   Click **Add Mapping**.
    *   Select the service `python-director`.
    *   Select the region `us-central1`.
    *   Enter your domain (e.g., `api.riju.dev` or `director.riju.dev`).
4.  **Verify Domain Ownership**:
    *   Google will ask you to verify ownership of `riju.dev`.
    *   Follow the instructions to add a **TXT record** to your Squarespace DNS settings.
5.  **Update DNS Records**:
    *   Once verified, Google will provide **CNAME** or **A/AAAA** records.
    *   Log in to **Squarespace** -> **Settings** -> **Domains** -> **riju.dev** -> **Edit DNS**.
    *   Add the records provided by Google.
6.  **Wait for Propagation**: It may take up to 24 hours (usually much faster) for SSL to provision and DNS to propagate.

## Option 2: Firebase Hosting (Recommended for Flutter Apps)

If you are already using Firebase, you can use Firebase Hosting to proxy requests to Cloud Run.

1.  **Initialize Firebase Hosting**: Run `firebase init hosting` in your project root.
2.  **Configure Rewrites**: In `firebase.json`, add a rewrite rule:
    ```json
    "hosting": {
      "rewrites": [
        {
          "source": "/api/**",
          "run": {
            "serviceId": "python-director",
            "region": "us-central1"
          }
        }
      ]
    }
    ```
3.  **Connect Domain**: In the Firebase Console -> Hosting, click **Add Custom Domain** and follow the instructions to add `riju.dev`.
4.  **Deploy**: Run `firebase deploy --only hosting`.

> [!TIP]
> Using Firebase Hosting is often smoother as it handles SSL automatically and integrates well with the rest of your Firebase project.
