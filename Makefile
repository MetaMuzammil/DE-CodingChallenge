AWS_REGION ?= ap-southeast-2
ENVIRONMENT ?= dev
TEMPLATE := template.yaml
STACK_NAME := de-assignment-poc
WORKLOAD := poc-de-challenge

test:
	cfn-lint $(TEMPLATE)

deploy: test
	$(eval AWS_ACCOUNT := $(shell aws sts get-caller-identity --query Account --output text ) )
	$(eval CFN_BUCKET := artifactory-$(AWS_REGION)-$(AWS_ACCOUNT))
	echo Deploying to environment $(ENVIRONMENT)
	aws cloudformation package \
		--template-file $(TEMPLATE) \
		--s3-bucket $(CFN_BUCKET) \
		--s3-prefix $(STACK_NAME) \
		--output-template-file rendered.yml
	aws cloudformation deploy \
		--template-file rendered.yml \
		--stack-name $(STACK_NAME) \
		--s3-bucket $(CFN_BUCKET) \
		--capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
		--no-fail-on-empty-changeset \
		--tags \
			createdFor=$(WORKLOAD)