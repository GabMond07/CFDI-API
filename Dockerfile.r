FROM r-base:4.3.2
RUN R -e "install.packages(c('jsonlite', 'dplyr'), repos='https://cran.r-project.org')"
WORKDIR /app
CMD ["R"]