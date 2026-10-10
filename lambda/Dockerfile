FROM public.ecr.aws/lambda/python:3.12
RUN dnf install -y mesa-libGL glib2 && dnf clean all
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
# Disable Numba JIT during initial Lambda smoke tests; avoids pymatting cache locator startup error.
# Benchmark segmentation performance before production.
ENV NUMBA_DISABLE_JIT=1 \
    U2NET_HOME=/tmp/.u2net \
    XDG_CACHE_HOME=/tmp/.cache \
    NUMBA_CACHE_DIR=/tmp/numba-cache
ARG GIT_COMMIT=unknown
ENV WAREHOUSE_GENERATOR_COMMIT=${GIT_COMMIT}
COPY app.py ${LAMBDA_TASK_ROOT}/app.py
COPY prompts/ ${LAMBDA_TASK_ROOT}/prompts/
COPY schemas/ ${LAMBDA_TASK_ROOT}/schemas/
CMD ["app.handler"]
