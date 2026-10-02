-- 02_s3_integration.sql
-- Connects Snowflake to the S3 bucket through an IAM role (no access keys).
-- Step 1 and 3 run here, step 2 happens in the AWS console.

USE ROLE ACCOUNTADMIN;

-- step 1: create the integration (fill in your account id and bucket)
CREATE STORAGE INTEGRATION IF NOT EXISTS S3_LANDING
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-landing-reader'
  STORAGE_ALLOWED_LOCATIONS = ('s3://polder-insurance-landing-yourname/landing/');

-- copy STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID from this output
-- into aws/trust-policy.json, then update the role's trust policy in AWS (step 2)
DESC INTEGRATION S3_LANDING;

GRANT USAGE ON INTEGRATION S3_LANDING TO ROLE TRANSFORMER;

-- step 3: everything below runs as the pipeline role
USE ROLE TRANSFORMER;
USE WAREHOUSE WH_PIPELINE;
USE SCHEMA INSURANCE.BRONZE;

-- the policy system exports semicolon-separated files with a header row
CREATE FILE FORMAT IF NOT EXISTS FF_CSV_SEMICOLON
  TYPE = CSV
  FIELD_DELIMITER = ';'
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  EMPTY_FIELD_AS_NULL = TRUE;

-- the postcode reference is a normal comma-separated file
CREATE FILE FORMAT IF NOT EXISTS FF_CSV_COMMA
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- one JSON object per line
CREATE FILE FORMAT IF NOT EXISTS FF_JSON
  TYPE = JSON;

CREATE STAGE IF NOT EXISTS LANDING
  URL = 's3://polder-insurance-landing-yourname/landing/'
  STORAGE_INTEGRATION = S3_LANDING;

-- should list the files you uploaded
LIST @LANDING;
