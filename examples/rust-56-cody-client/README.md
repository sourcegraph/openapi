# Rust Cody Client

This is n example Rust implementation of a Cody Chat CLI that interacts with the Sourcegraph API to provide context-aware responses based on repository content.

## Prerequisites

- Rust
- Cargo

## Dependencies

This project uses the following dependencies:
- tokio (1.0+)
- reqwest (0.11+)
- serde_json (1.0+)
- structopt (0.3+)
- futures (0.3+)

## Environment Variables

Before running the application, make sure to set the following environment variables:

- `SRC_ACCESS_TOKEN`: Your Sourcegraph access token
- `SRC_ENDPOINT`: The Sourcegraph API endpoint URL

## Building the Project

To build the project, run:
````
cargo build
````

For a release build with optimizations:
````
cargo build --release
````

## Running the Application

You can run the application using:
````
cargo run -- --context-repo github.com/sourcegraph/openapi --message "Example prompt here"
````

Or, if you've built the release version:
````
./target/release/rust-56-cody-client --context-repo github.com/sourcegraph/openapi --message "Example prompt here"
````

Replace `github.com/sourcegraph/openapi`, etc., with the names of the repositories you want to include in the context, and "Example prompt here" with your actual query.

Please note that the `--context-repo` option is optional. You can use it multiple times to include multiple repositories, or omit it entirely if you don't need repository context:

````
./target/release/rust-56-cody-client --message "Your query without context"
````

If you do use `--context-repo`, you can specify multiple repositories like this:
````
./target/release/rust-56-cody-client --context-repo <repo1> --context-repo <repo2> --message "Your query here"
````

## Features

- Fetches repository context based on provided repository names
- Sends chat completion requests to the Sourcegraph API
- Handles Server-Sent Events (SSE) for streaming responses
- Formats and displays the AI-generated response

## Note

This client is designed to work with the Sourcegraph API. Make sure you have the necessary permissions and a valid access token to use this application.

This code/example was tested against Sourcegraph Enterprise.
