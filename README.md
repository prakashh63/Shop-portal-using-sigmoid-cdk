# Shop portal (consumer of sigmoid_cdk)

A small online-shop backend built only from `app.py`. The infrastructure comes from the
`sigmoid_cdk` package; the code in `src/` and `site/` is the application.

```
Browser --HTTPS--> CloudFront
                    |-- /            -> website bucket    (site/index.html)
                    |-- /assets/*    -> assets bucket     (site/assets/*)
                    '-- /api/*       -> API Gateway
                                         |-- /api/users   -> users Lambda
                                         |-- /api/orders  -> orders Lambda  -- writes --> invoices bucket
                                         '-- /api/reports -> reports Lambda -- reads  --> invoices bucket

SNS topic "shop-orders" -> worker Lambda          (sends confirmation emails)
EventBridge rate(1 day) -> reports Lambda         (nightly report)
```

## Run locally (no AWS account needed)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python local_test.py        # runs all four handlers with fake events
python local_server.py      # the whole app in your browser: http://localhost:8000
cdk synth --quiet           # builds the template and runs the cdk-nag security checks
python show_plan.py         # prints what was built, read from cdk.out/
```

## What each Lambda is allowed to do

| Lambda | Trigger | S3 access | Why |
| --- | --- | --- | --- |
| users | `/api/users` | none | no files needed |
| orders | `/api/orders` | invoices: read and write | stores invoices |
| reports | `/api/reports` + daily schedule | invoices: read only | counts invoices |
| worker | SNS topic `orders` | none | sends emails |

`show_plan.py` prints the exact S3 actions per role, so you can check that `users` and `worker`
have none and `reports` has no write action.
