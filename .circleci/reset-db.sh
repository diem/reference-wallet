#!/bin/bash

DB_SECRET=`aws --region eu-central-1 secretsmanager get-secret-value --secret-id "staging-rds"`
RDS_PASS=`echo "${DB_SECRET}" | jq -r '.SecretString | fromjson | .aurora'`
RDS_USER="master"
DB_CLUSTER_IDENTIFIER="eu-central-1-staging-aurora"
RDS_ENDPOINT=`aws --region eu-central-1 rds describe-db-cluster-endpoints --db-cluster-identifier "${DB_CLUSTER_IDENTIFIER}" | jq --raw-output --arg MODE "WRITER" '.DBClusterEndpoints[] | select(.EndpointType == "WRITER") |.Endpoint'`

deployments=`kubectl -n staging get deployments | awk '{print $1}' | grep lrw`
echo "deployments to stop: "
echo "${deployments[@]}"
for deployment in ${deployments[@]}; do
    echo "scaling deployment $deployment to 0 ..."
    kubectl -n staging scale deploy "$deployment" --replicas=0
    echo "done!"
done

echo ""
echo "deleting all tables from staging_lrw db..."
echo "creating temporary pod..."
kubectl -n staging run db-cleaner --restart=Never --image=alpine:3.8  --env=H="${RDS_ENDPOINT}" --env=U="${RDS_USER}" --env=P="${RDS_PASS}" -- tail -f /dev/null

echo "waiting to the temporary pod to be in Ready state..."
kubectl -n staging wait --for=condition=Ready pod/db-cleaner

echo "adding mysql-client apk..."
kubectl -n staging exec pod/db-cleaner -it -- ash -c "apk add mysql-client"

echo "getting tables to drop..."
tables=`kubectl -n staging exec pod/db-cleaner -it -- ash -c "mysql -h\\\$H -u\\\$U -p\\\$P staging_lrw -e 'show tables' | awk '{ print $1}' | grep -v '^Tables'"`
echo "tables to drop: "
echo "${tables[@]}"
for table in ${tables[@]}; do
    echo "dropping ${table}..."
    kubectl -n staging exec pod/db-cleaner -it -- ash -c "mysql -h\$H -u\$U -p\$P staging_lrw -e 'drop table $table cascade'"
do

echo "removing the temporary pod..."
kubectl -n staging delete pod/db-cleaner

echo "re-scaling the deployments to 1: "
echo "${deployments[@]}"
for deployment in ${deployments[@]}; do
    echo "scaling deployment $deployment to 1 ..."
    kubectl -n staging scale deploy "$deployment" --replicas=1
    echo "done!"
done

echo "DONE! DONE! DONE!"
