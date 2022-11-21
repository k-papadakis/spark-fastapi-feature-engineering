# Feature Engineering with FastAPI

This project is a simple app to engineer features by using [transformations](https://featuretools.alteryx.com/en/stable/api_reference.html#aggregation-primitives) and [aggregations](https://featuretools.alteryx.com/en/stable/api_reference.html#aggregation-primitives) as described in the featuretools library.

The data is comprised of loans that customers have taken. The transformations are done per loan and the aggregations are done per customer.

The main logic of app is written in [app/main.py](app/main.py).

It is possible to get the API server up and running by executing

```shell
docker compose up
```

You can access the server on [http://localhost:8000](http://localhost:8000). See also the API's documentation at [http://localhost:8000/docs](http://localhost:8000/docs) on a web browser.

For ease of use with VS Code, a [.devcontainer](.devcontainer) has been created which also installs dependencies for testing implemented in [app/test_main.py](app/test_main.py).

As an alternative to docker you can create a conda environment specified in [conda-requirements.yml](conda-requirements.yml) by running

```shell
conda env create -f environment.yml
```
