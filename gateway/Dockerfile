FROM nginx:1.17-alpine as dynamic_conf

#-------------------------------------------------------------------
FROM dynamic_conf as default_conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY tmp/frontend/. /html/

#-------------------------------------------------------------------
FROM default_conf as static_conf
COPY nginx.static.conf /etc/nginx/nginx.conf