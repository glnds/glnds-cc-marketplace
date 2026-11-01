# Cost efficiency patterns

## Terraform / CloudFormation / SAM

```bash
# Previous-generation EC2/RDS
rg -nP 'instance_type\s*=\s*"(m5|c5|r5|m4|c4|r4|t2|t3)\.[a-z0-9]+"' -g '*.tf'
rg -nP 'instance_class\s*=\s*"db\.(m5|r5|m4|r4)\.[a-z0-9]+"' -g '*.tf'

# S3 buckets without lifecycle
rg -L 'lifecycle_rule|aws_s3_bucket_lifecycle_configuration' -g '*.tf' \
  $(rg -l 'resource\s+"aws_s3_bucket"' -g '*.tf')

# ECR without lifecycle
rg -L 'aws_ecr_lifecycle_policy' -g '*.tf' $(rg -l 'aws_ecr_repository' -g '*.tf')

# CloudWatch log groups without retention (defaults to never expire)
PAT_LOG='resource\s+"aws_cloudwatch_log_group"\s+"[^"]+"\s*\{'
PAT_LOG+='(?:(?!retention_in_days)[\s\S]){0,400}\}'
rg -nP "$PAT_LOG" -g '*.tf'

# Oversized Lambda memory
PAT_LAM='resource\s+"aws_lambda_function"[\s\S]{0,600}'
PAT_LAM+='memory_size\s*=\s*(2048|3008|4096|5120|10240)'
rg -nP "$PAT_LAM" -g '*.tf'

# gp2 instead of gp3
rg -n 'type\s*=\s*"gp2"' -g '*.tf'

# NAT gateways per AZ
rg -c 'aws_nat_gateway' -g '*.tf'

# DynamoDB provisioned (vs PAY_PER_REQUEST) for spiky workloads
rg -n 'billing_mode\s*=\s*"PROVISIONED"' -g '*.tf'

# SAM / CloudFormation equivalents
rg -nP 'MemorySize:\s*(2048|3008|4096|5120|10240)' -g '*.yaml' -g '*.yml'
rg -nP 'RetentionInDays' -g 'template*.yaml'    # absence = never expire
```

## Runtime and containers

```bash
# Dockerfile: single-stage, COPY . ., apt without cleanup
rg -c '^FROM ' Dockerfile*
rg -n '^COPY\s+\.\s+' Dockerfile*
rg -L 'AS\s+build|AS\s+builder' Dockerfile*
rg -n 'apt-get\s+install[^&]*$' Dockerfile*

# N+1 queries heuristic
rg -nP 'for\s+\w+\s+in\s+\w+[\s\S]{0,200}\.(find|query|select|get|filter)\(' \
  -g '*.{py,js,ts,java,go}'

# SELECT * in prod queries
rg -nP '\bSELECT\s+\*\b' -g '*.{sql,py,js,ts,java,go,rb}'

# High-cardinality metric labels
rg -nP 'statsd\.(increment|gauge|histogram)\([^)]*user[_-]?id|request[_-]?id|session[_-]?id'
rg -nP 'labelNames:\s*\[[^\]]*(userId|email|uuid|requestId)' -g '*.{js,ts}'

# Debug logging in production paths
rg -n 'log(ger)?\.debug|console\.debug|fmt\.Println' -g '!**/test/**'
```

## Preferred tools

`infracost breakdown --path . --format json` for priced diffs. `checkov -d . --framework terraform`
includes many cost and ops checks. `trivy config` for IaC misconfiguration (absorbs the tfsec
engine). `tflint --recursive` with the AWS ruleset. `dockle` and `dive` for image bloat.

## Red flags

- CloudWatch log groups without `retention_in_days`.
- S3 buckets without a lifecycle rule (and without an abort-multipart-upload rule).
- ECR without lifecycle.
- Lambda over 1024 MB without a stated reason.
- gp2 EBS.
- Previous-generation instance families where Graviton fits.
- Single-stage Docker builds with `node_modules`, `.git`, or build toolchains in the final image.
- High-cardinality Prometheus or Datadog labels.
- Multi-AZ NAT Gateways in low-traffic VPCs.
- `SELECT *` plus no pagination plus no index.
