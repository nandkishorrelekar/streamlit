# House Price Prediction – Version 2

An interactive web app that uses the existing California Housing Random Forest
model to estimate a district's median house value. The included `model.joblib`
was exported from the previously trained model.

The model expects these eight values, in this order:

1. `MedInc` - median income
2. `HouseAge` - median house age
3. `AveRooms` - average rooms
4. `AveBedrms` - average bedrooms
5. `Population` - district population
6. `AveOccup` - average occupancy
7. `Latitude`
8. `Longitude`

The model output is in units of $100,000. For example, `2.5` is shown as
approximately `$250,000`. This regression model does not provide a confidence
score.

## Run locally

From this directory, create a virtual environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in a browser. The form is
pre-filled with a sample district; edit the values and select **Predict median
house value**.

To load a different compatible sklearn model, set `MODEL_PATH` to its Joblib
file before starting Streamlit. The replacement model must accept the same
eight feature columns.

## Build and publish Docker images with GitHub Actions

The workflow at `.github/workflows/docker-publish.yml` runs on every push and
can also be started manually. On a GitHub-hosted Ubuntu runner, it:

1. Checks out the repository and sets up Python 3.12.
2. Installs the application dependencies and pytest.
3. Runs the Streamlit/model tests.
4. Checks that Docker Hub credentials are configured.
5. Builds the Docker image and starts a temporary container to check the
   Streamlit health endpoint and run a sample model prediction.
6. Logs in to Docker Hub using GitHub Actions secrets and pushes the image.

The workflow publishes `DOCKERHUB_USERNAME/house-price-ml:latest` for pushes
to the repository's default branch. Other branch pushes also publish branch
and commit-SHA tags. It does not deploy to a production server. Failed test,
build, or container steps appear in red in GitHub Actions; the container
smoke-test step prints its logs on failure.

### Put the project in a GitHub repository

1. On GitHub, select **New repository**, name it `ML_Streamlit_App`, choose
   **Private** (or another visibility if preferred), and create it without
   initializing another README or `.gitignore`.
2. From this project directory, initialize a separate local repository and
   commit the project files:

```bash
git init -b main
git add app.py model.joblib requirements.txt Dockerfile README.md tests .github
git commit -m "Add Streamlit app Docker CI"
```

3. If GitHub CLI is installed and authenticated, create the private remote and
   push the branch:

```bash
gh repo create ML_Streamlit_App --private --source=. --remote=origin --push
```

Alternatively, create the empty repository through GitHub's website, then add
its URL and push:

```bash
git remote add origin https://github.com/<YOUR-USERNAME>/ML_Streamlit_App.git
git push -u origin main
```

### Configure Docker Hub publishing

1. In Docker Hub, create a repository named `house-price-ml` under your
   account. Choose public or private visibility.
2. In Docker Hub account settings, create an access token named
   `github-actions-token`. Grant only the permissions needed to pull and push
   images (Read and Write); Delete permission is not needed by this workflow.
3. In the GitHub project repository, open **Settings → Secrets and variables
   → Actions** and add these **Repository secrets**:

   | Secret name | Value |
   | --- | --- |
   | `DOCKERHUB_USERNAME` | Your Docker Hub username |
   | `DOCKERHUB_TOKEN` | The Docker Hub access token |

   Do not paste the token into source code or commit it to the repository.
4. Commit and push the workflow and project files. A push triggers the
   workflow; no deployment service or paid runner is required.

The image is published as
`DOCKERHUB_USERNAME/house-price-ml:latest` on the default branch. The workflow
also pushes branch and commit-SHA tags. If secrets are missing, the workflow
fails with an explicit message before attempting to build or publish.

### View workflow results

1. Open the repository on GitHub.
2. Select the **Actions** tab.
3. Select **Build and publish Docker image** to see recent runs.
4. Open a run and expand each step for logs. A green check means tests, image
   build, container smoke test, and Docker Hub push all passed; a red cross
   identifies the failing step and its error output.

You can also open a commit and select its **Checks** section to view the
workflow status for that push.

After a successful run, open Docker Hub → **Repositories** →
`house-price-ml` and confirm the `latest` tag was updated.

### Pull and run the published image

After the workflow publishes the image, replace `<DOCKERHUB_USERNAME>` with
your Docker Hub username. For a private Docker Hub repository, run `docker login`
first and authenticate using your Docker Hub access token:

```powershell
docker pull <DOCKERHUB_USERNAME>/house-price-ml:latest
docker run --rm -p 127.0.0.1:8501:8501 <DOCKERHUB_USERNAME>/house-price-ml:latest
```

Open [http://localhost:8501](http://localhost:8501) and verify the heading
**House Price Prediction – Version 2**.

### Run tests locally

Install pytest in addition to the application dependencies, then run:

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
```

## Direct Docker deployment

This project uses a **direct replacement** deployment: the updated image is
built first, then the existing container is stopped and removed, and a new
container is started with the same name and port. The app keeps the same URL,
`http://localhost:8501`, but users may experience brief downtime between
stopping the old container and the new one becoming healthy.

Install and start Docker Desktop (or another Docker Engine), then run these
commands from this directory in PowerShell. Keep the existing container and
image names (`california-housing-streamlit`) consistent:

```text
1. Keep a rollback tag for the currently deployed image.
2. Build the new image.
3. Stop and remove the current container.
4. Start the new container using the same name and port.
5. Check the health endpoint and container status.
```

```powershell
# 1. Preserve the current image for rollback.
docker tag california-housing-streamlit:latest california-housing-streamlit:previous

# 2. Build the updated image. Change the version for each deployment.
docker build --build-arg APP_VERSION=2.0.0 -t california-housing-streamlit:latest .

# 3. Replace the old container.
docker stop california-housing-streamlit
docker rm california-housing-streamlit

# 4. Start the replacement with the same name, port, and local URL.
docker run -d --name california-housing-streamlit -p 127.0.0.1:8501:8501 california-housing-streamlit:latest

# 5. Verify the app and deployment version.
Invoke-WebRequest http://127.0.0.1:8501/_stcore/health
docker inspect --format 'State={{.State.Status}} Health={{.State.Health.Status}}' california-housing-streamlit
docker logs --tail 30 california-housing-streamlit
```

Open [http://localhost:8501](http://localhost:8501). The UI displays the
application version so you can confirm the new image is serving requests.

### Roll back if the new container fails

The `previous` image tag keeps the last image available. Stop and remove a
failed replacement, then start the prior image with the same port mapping:

```powershell
docker stop california-housing-streamlit
docker rm california-housing-streamlit
docker run -d --name california-housing-streamlit -p 127.0.0.1:8501:8501 california-housing-streamlit:previous
docker inspect --format 'State={{.State.Status}} Health={{.State.Health.Status}}' california-housing-streamlit
```

### Preserve model files and application data

`model.joblib` is copied into the Docker image by the Dockerfile. To deploy a
new model, place the trusted replacement at `model.joblib` in this project
before building the updated image. The new image then carries that model when
the old container is removed.

Files written only inside a container's writable layer are not preserved when
that container is removed. Store mutable application data in a Docker named
volume or a host bind mount, and attach the same volume or mount to each
replacement container. If using a model mounted from the host, mount it read
only at `/app/model.joblib` (or set `MODEL_PATH` to its container path). Joblib
uses Python pickle serialization, so only load trusted model files.

If `docker build` fails, do not stop the existing container. If the
replacement fails after the old container was removed, inspect it with
`docker logs california-housing-streamlit` and use the rollback steps above.
