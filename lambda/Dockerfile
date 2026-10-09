FROM public.ecr.aws/lambda/python:3.12
RUN dnf install -y mesa-libGL glib2 && dnf clean all
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
# Disable Numba JIT during initial Lambda smoke tests; avoids pymatting cache locator startup error.
# Benchmark segmentation performance before production.
ENV NUMBA_DISABLE_JIT=1
COPY app.py ${LAMBDA_TASK_ROOT}/app.py
CMD ["app.handler"]
