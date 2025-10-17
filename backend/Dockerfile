FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bank_iq_agent_v1.py .

EXPOSE 8080

CMD ["python", "bank_iq_agent_v1.py"]
