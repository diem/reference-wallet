ARG NIROPS_IMAGE_TAG=develop
FROM 695406093586.dkr.ecr.eu-central-1.amazonaws.com/nirops:${NIROPS_IMAGE_TAG}

WORKDIR /src/

# weird bug with non-builtin typing (https://github.com/ethereum/eth-abi/issues/131)
RUN pip uninstall -y typing \
    && pip install -Iv 'diem' \
    && pip install -Iv 'jwcrypto'

COPY deployment.py /src

ENTRYPOINT ["python", "deployment.py"]

