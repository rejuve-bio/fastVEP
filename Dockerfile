FROM rust:1-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*

COPY Cargo.toml Cargo.lock ./
COPY crates/ ./crates/
COPY web/ ./web/

RUN cargo build --release -p fastvep-web -p fastvep-cli

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y ca-certificates curl samtools wget && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/fastvep-web /usr/local/bin/fastvep-web
COPY --from=builder /app/target/release/fastvep     /usr/local/bin/fastvep
COPY scripts/ /scripts/

EXPOSE 8080

ENTRYPOINT ["fastvep-web"]
