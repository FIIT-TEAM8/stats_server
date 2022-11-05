FROM python:3.9-alpine

WORKDIR /myApp

ENV PRODUCTION=production

COPY . ./

RUN pip install -r requirements.txt

EXPOSE 5002

CMD ["python", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5002"]