FROM public.ecr.aws/lambda/python:3.12
RUN dnf install -y mesa-libGL glib2 && dnf clean all
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt
COPY app.py ${LAMBDA_TASK_ROOT}/app.py
CMD ["app.handler"]
