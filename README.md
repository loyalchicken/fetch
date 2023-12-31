# Receipt Points Processor

This service processes submitted receipts and calculates points according to predefined rules.

### Installation and Running the Service

1. **Build the Docker Image:**

    ```sh
    docker build -t receipt-processor .
    ```

2. **Run the Container:**

    ```sh
    docker run -p 80:80 receipt-processor
    ```

Now the service is accessible at `http://localhost:80`.

## Usage

The service exposes two endpoints:

- **Process Receipt**: `POST /receipts/process`
  
  Submit receipt data as JSON. It returns a unique receipt ID. Make a request to `http://localhost:80/receipts/process`.

- **Get Points**: `GET /receipts/{receipt_id}/points`
  
  Retrieve the calculated points for the given receipt ID by making a request to `http://localhost:80/receipts/{receipt_id}/points`.