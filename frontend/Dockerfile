FROM nginx:1.27-alpine

# Copy the lightweight Vue static assets from the frontend module
COPY frontend/static /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
