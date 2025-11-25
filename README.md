# etl-in-aws
This project implements a fully automated, event-driven data pipeline using multiple AWS services.
The pipeline collects data from two independent sources—local files and a MySQL database—performs transformations, stores the refined data in Amazon Redshift, and delivers analytics through Microsoft Power BI.

The solution is built for scalability, low operational overhead, and real-time data delivery.

Architecture Summary
Data Sources

>> Local Drive Files
CSV/JSON/text files processed through AWS Lambda and delivered to S3.

>> MySQL Server
Tables extracted and ingested into S3 before transformation using AWS Glue.

Pipeline Flow
1. Local Files → Lambda → S3 → Lambda → Redshift

>>Files are added to a local directory.

>>A Lambda function transforms, cleans, and validates the dataset.

>>The processed output is pushed to an S3 bucket.

>>S3 triggers an event notification.

>>Another Lambda function loads the S3 file into Amazon Redshift using COPY commands or the Redshift Data API.

2. MySQL → S3 → Glue → Lambda → Redshift

>>MySQL data is extracted and uploaded to S3 (scheduled job or AWS DMS alternative).

>>AWS Glue performs schema mapping, data cleaning, and transformation.

>>Glue output is written back to an S3 landing/processed zone.

>>An S3 trigger invokes a Lambda function.

>>The Lambda function loads the processed dataset into Redshift.

Data Analytics Layer
Redshift → Power BI

Once the data lands in Redshift:

>>Power BI is connected through the built-in Amazon Redshift connector.

>>Dashboards and reports are built for real-time insight into operational and analytical metrics.

Key Features

Event-driven architecture using S3 notifications

Automated ingestion from heterogeneous data sources

>>Serverless transformations using AWS Lambda

>>Scalable ETL using AWS Glue

>>Structured storage and querying in Redshift

>>Interactive BI dashboards using Power BI

>>Easy extensibility for new data sources

>>Cloud-native, highly available, and secure
