FROM ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff AS uv
FROM python:3.12.15-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS cli
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /opt/enrama
COPY pyproject.toml uv.lock build-constraints.txt README.md LICENSE ./
COPY src ./src
RUN uv build --wheel --out-dir /tmp/wheels --build-constraint build-constraints.txt --require-build-hashes --no-cache \
    && uv sync --locked --no-dev --no-install-project --no-build --no-cache \
    && uv pip install --python .venv/bin/python --no-deps --no-cache /tmp/wheels/*.whl \
    && uv pip check --python .venv/bin/python \
    && rm -rf /tmp/wheels /usr/local/bin/uv
ENV PATH="/opt/enrama/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
ARG REVISION=unknown
LABEL org.opencontainers.image.source="https://github.com/Dev-Peter21/enrama" \
      org.opencontainers.image.revision=$REVISION
USER 10001:10001
WORKDIR /site
ENTRYPOINT ["enrama"]
CMD ["--help"]

FROM nginx:1.30.6-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951 AS static
ARG REVISION=unknown
LABEL org.opencontainers.image.source="https://github.com/Dev-Peter21/enrama" \
      org.opencontainers.image.revision=$REVISION
COPY docker/nginx.conf.template /etc/enrama/nginx.conf.template
COPY --chmod=555 docker/serve.sh /usr/local/bin/enrama-serve
RUN rm -rf /usr/share/nginx/html && mkdir -p /srv && chown 101:101 /srv
USER 101:101
ENV PORT=8080
EXPOSE 8080
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/local/bin/enrama-serve"]
