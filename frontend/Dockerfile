FROM nginx:alpine
# מחיקת קובץ ההגדרות הדיפולטיבי של Nginx
RUN rm /etc/nginx/conf.d/default.conf
# העתקת ההגדרות שלנו
COPY nginx.conf /etc/nginx/conf.d/
# העתקת ה-HTML
COPY index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]