# =====================================
# Build stage
# =====================================
FROM python:3.13-alpine AS build

# Build-time dependencies (removed after build):
# - build-base: C/C++ compiler toolchain (required to build numpy, pandas, matplotlib extensions)
# - python3-dev: Python headers needed for compiling C extensions
# - git: required because one dependency is installed directly from a git repository
RUN apk add --no-cache \
        build-base \
        python3-dev \
        git

WORKDIR /build

# Copy packaging metadata first (better cache reuse)
COPY pyproject.toml setup.py README.md ./
# Copy only the application source
COPY src/ src/

# Install the application and all dependencies into an isolated prefix
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install .

# =====================================
# Runtime stage
# =====================================
FROM python:3.13-alpine

# Runtime-only shared libraries:
# - libstdc++: required by numpy / pandas / matplotlib C++ extensions
RUN apk add --no-cache \
        libstdc++ \
    && adduser -S -h /home/sigrid sigrid

COPY --from=build /install /usr/local

USER sigrid
WORKDIR /home/sigrid

ENTRYPOINT ["report-generator"]
