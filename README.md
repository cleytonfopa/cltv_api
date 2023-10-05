# CLTV API

# Welcome to CLTV API!

This API enables real-time generation of *Customer Lifetime Value
(CLTV)* for a specific user. By using the user’s activity data within
the betting platform during the initial 7-day period, a machine learning
model forecasts the expected Gross Gaming Revenue (GGR) accumulation for
the subsequent 6 months.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
- [Endpoints](#endpoints)
  - [Endpoint 1](#endpoint-1)
- [Authors](#authors)

## Getting Started <a name="getting-started"></a>

### Prerequisites <a name="prerequisites"></a>

This API is written in Python. In order to set up all dependencies, it
is essential you to use the Python virtualenv management tool
[`pipenv`](https://pipenv.pypa.io/en/latest/).

### Installation <a name="installation"></a>

Once you clone this repository, go the API directory. There will be a
file called `Pipfile.lock` specifying all the dependencies used. Open a
terminal and run the following command:

    pipenv sync

This command will install all the packages and their respective versions
necessary to run the API.

### Usage <a name="usage"></a>

Once the environment is set up, we can run the API as follows:

    pipenv run python api.py

## Endpoints <a name="endpoints"></a>

### Endpoint 1 <a name="endpoint-1"></a>

- **URL**: `/predict_cltv`

- **Method**: POST

- **Description**: This endpoint will calculate the prediction for the
  CLTV for each player.

- **Input**: `JSON` file containing the **merge between two datasets:
  *casino* and *players***. See the template file `test.json` in the
  `examples/` folder.

- **Response**:

  - JSON with the point estimate for CLTV, as well as the lower and
    upper bound prediction the for each player.

  For example, for two players:
  `[{"Username":"erika12144","y_pred":17.4625242857,"y_lower":5.7690522222,"y_upper":31.7690522222},{"Username":"euphobravo","y_pred":30.3746,"y_lower":19.5762666667,"y_upper":49.5762666667}]`

## Examples <a name="examples"></a>

There is a file called `test.json` in the `examples/` folder in this
repository that contains an example of the input format this API accept.

Suppose you are running the API locally on default port `1234`. You can
make a request to the API as follows:

    curl -XPOST -H "Content-Type: application/json" -d @examples/test.json http://127.0.0.1:5000/predict_cltv

## Author <a name="authors"></a>

- [Cleyton Farias](mailto:cleytonfarias@outlook.com "e-mail");
