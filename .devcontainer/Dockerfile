FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG QUARTO_VERSION=1.10.18

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl \
    && curl --fail --location --output /tmp/quarto.deb \
      "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.deb" \
    && dpkg --install /tmp/quarto.deb \
    && rm /tmp/quarto.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
